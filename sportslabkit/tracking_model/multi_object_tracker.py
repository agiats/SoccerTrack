from __future__ import annotations

import time
import uuid
from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd
from filterpy.kalman import KalmanFilter
from motpy.model import Model, ModelPreset

from sportslabkit import BBoxDataFrame, Camera
from sportslabkit.logger import logger, tqdm
from sportslabkit.types.types import Box, Vector, _pathlike
from sportslabkit.types.detections import Detections
from sportslabkit.types.detection import Detection
from sportslabkit.types.tracklet import Tracklet

DEFAULT_MODEL_SPEC = ModelPreset.constant_velocity_and_static_box_size_2d.value


class MultiObjectTracker:
    """The main component that manages the tracking of multiple objects.

    Args:
        dt: Time step in seconds.
        model_spec: Specifies the dimension and order for position and size of the object.
        matching_fn: Determines the strategy on which the trackers and detections are assigned.
        tracker_kwarg: Are passed to each single object tracker.
        active_tracks_kwargs: Limits surfacing of fresh/fading out tracks.

    Examples:
        >>> mot = MultiObjectTracker(dt=1/25, model_spec="constant_velocity_and_static_box_size_2d")
        >>> res = mot.track("path/to/video.mp4")
        >>> res.to_bbdf()
    """

    def __init__(
        self,
        detection_model=None,
        image_model=None,
        tracker: Tracklet = None,
        tracker_kwargs: dict[str, Any] = {},
        matching_fn: Any | None = None,
    ) -> None:
        self.detection_model = detection_model
        self.image_model = image_model
        self.matching_fn: Any = matching_fn

        self.tracker_class = tracker
        self.tracker_kwargs = tracker_kwargs

        self.trackers: list[Tracklet] = []
        self.stale_trackers: list[Tracklet] = []

        self.detections_matched_ids = []
        self.current_step = 0

    def track(
        self,
        source: _pathlike | Camera,
        num_frames: int | None = None,
        batch_size: int = 1,
    ):
        """Tracks objects in a video.

        Args:
            source: Path to a video file or a Camera object.

        Returns:
            The result of the tracking as a xxx.
        """

        if not isinstance(source, Camera):
            cam = Camera(source)
        else:
            cam = source

        dets = []
        for frame in (pbar := tqdm(cam[:num_frames])):
            # detect objects using the detection model
            detections = self.detection_model(frame).to_list()

            # extract features from the detections
            if len(detections) > 0 and self.image_model is not None:
                embeds = self.image_model.embed_detections(detections, frame)
                for i, det in enumerate(detections):
                    det.feature = embeds[i]

            dets.append(detections)

            # update the state of the multi-object-tracker tracker
            # with the list of bounding boxes
            active_trackers = self.step(detections=detections)

            # get tracks to be displayed
            all_trackers = self.all_trackers()
            pbar.set_postfix({"Number of active/all tracks": f"{len(active_trackers)}/{len(all_trackers)}"})

    def step(self, detections: list[Detection]) -> list[Tracklet]:
        """the method matches the new detections with existing trackers,
        creates new trackers if necessary and performs the cleanup.

        Returns the active tracks after active filtering applied
        """
        # filter out empty detections
        # detections = [det for det in detections if det.box is not None]

        # match trackers with detections
        logger.debug("step with %d detections" % len(detections))
        for detection in detections:
            logger.debug(f"\t{[int(item) for item in detection.box]}, {detection.score:.2f}")

        matches = self.matching_fn(self.trackers, detections)
        logger.debug("matched %d pairs" % len(matches))

        self.detections_matched_ids = [None] * len(detections)

        # assigned trackers: correct
        for match in matches:
            track_idx, det_idx = match[0], match[1]
            self.trackers[track_idx].update(detection=detections[det_idx], global_step=self.current_step)
            self.detections_matched_ids[det_idx] = self.trackers[track_idx].id

        # not assigned detections: create new trackers POF
        assigned_det_idxs = set(matches[:, 1]) if len(matches) > 0 else []
        for det_idx in set(range(len(detections))).difference(assigned_det_idxs):
            det = detections[det_idx]
            tracker = self.instatiate_tracker_with_detection(det)
            self.detections_matched_ids[det_idx] = tracker.id
            self.trackers.append(tracker)

        # unassigned trackers
        assigned_track_idxs = set(matches[:, 0]) if len(matches) > 0 else []
        for track_idx in set(range(len(self.trackers))).difference(assigned_track_idxs):
            self.trackers[track_idx].update(None, global_step=self.current_step)

        # cleanup dead trackers
        self.cleanup_trackers()

        # update current step
        self.current_step += 1

        return self.active_trackers()

    def instatiate_tracker_with_detection(self, detection: Detection) -> Tracklet:
        """instantiates a new tracker from a detection"""
        tracker = self.tracker_class(
            **self.tracker_kwargs,
        )
        tracker.update(detection=detection, no_predict=False)
        return tracker

    def active_trackers(self) -> list[Tracklet]:
        """returns all active tracks after optional filtering by tracker steps
        count and staleness."""
        return [tracker for tracker in self.trackers if tracker.is_active()]

    def all_trackers(self) -> list[Tracklet]:
        """returns all trackers."""
        return self.trackers + self.stale_trackers

    def to_bbdf(self):
        """Create a bounding box dataframe."""
        df = pd.concat([t.to_bbdf() for t in self.active_trackers()], axis=1).sort_index()
        df = df.reindex(index=range(self.current_step))

        return pd.concat([t.to_bbdf() for t in self.all_trackers()], axis=1).sort_index()

    def cleanup_trackers(self) -> None:
        """Moves stale trackers into the stale_trackers list."""
        count_before = len(self.trackers)
        self.stale_trackers.extend([t for t in self.trackers if t.is_stale() and not t.is_invalid()])
        self.trackers = [t for t in self.trackers if not (t.is_stale() or t.is_invalid())]
        count_after = len(self.trackers)
        logger.debug("deleted %s/%s trackers" % (count_before - count_after, count_before))

    def tune(self):
        pass

import optuna
import numpy as np
from sportslabkit import Tracklet
from sportslabkit.metrics import iou_score, convert_to_x1y1x2y2


def tune_motion_model(
    motion_model_class,
    detections,
    ground_truth_positions,
    n_trials=100,
    hparam_search_space=None,
    metric=iou_score,
    verbose=False,
    return_study=False,
):
    def objective(trial: optuna.Trial):
        params = {}
        for param_name, search_space in hparam_search_space.items():
            if search_space["type"] == "categorical":
                params[param_name] = trial.suggest_categorical(
                    param_name, search_space["values"]
                )
            elif search_space["type"] == "float":
                params[param_name] = trial.suggest_float(
                    param_name, search_space["low"], search_space["high"]
                )
            elif search_space["type"] == "logfloat":
                params[param_name] = trial.suggest_float(
                    param_name, search_space["low"], search_space["high"], log=True
                )
            elif search_space["type"] == "int":
                params[param_name] = trial.suggest_int(
                    param_name, search_space["low"], search_space["high"]
                )

        motion_model = motion_model_class(**params)
        tracklet = Tracklet()
        ious = []

        for det, gt in zip(detections, ground_truth_positions):
            tracklet.update(det)
            prediction = motion_model(tracklet)

            iou = iou_score(convert_to_x1y1x2y2(prediction), convert_to_x1y1x2y2(gt))
            ious.append(iou)

        avg_iou = np.mean(ious)
        return 1 - avg_iou  # Minimize 1 - IoU

    if verbose:
        optuna.logging.set_verbosity(optuna.logging.INFO)
    else:
        optuna.logging.set_verbosity(optuna.logging.WARNING)

    if hparam_search_space is None:
        hparam_search_space = motion_model_class.hparam_search_space

    study = optuna.create_study()
    study.optimize(objective, n_trials=n_trials)

    best_params = study.best_params
    best_iou = 1 - study.best_value
    if return_study:
        return best_params, best_iou, study
    return best_params, best_iou