from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Tuple, Union

import numpy as np
import optuna
import pandas as pd

from sportslabkit import Tracklet
from sportslabkit.detection_model.dummy import DummyDetectionModel
from sportslabkit.logger import logger, tqdm
from sportslabkit.metrics import hota_score


class MultiObjectTracker(ABC):
    def __init__(self, window_size=1, step_size=None, max_staleness=5, min_length=5):
        self.window_size = window_size
        self.step_size = step_size or window_size
        self.max_staleness = max_staleness
        self.min_length = min_length
        self.reset()

    def update_tracklet(self, tracklet: Tracklet, states: Dict[str, Any]):
        self._check_required_observations(states)
        tracklet.update_observations(states, self.frame_count)
        tracklet.increment_counter()
        return tracklet

    @abstractmethod
    def update(self, current_frame: Any, trackelts: List[Tracklet]) -> Tuple[List[Tracklet], List[Dict[str, Any]]]:
        pass

    def process_sequence_item(self, sequence: Any):
        self.frame_count += 1  # incremenmt first to match steps alive
        is_batched = isinstance(sequence, np.ndarray) and len(sequence.shape) == 4
        tracklets = self.alive_tracklets
        if is_batched:
            raise NotImplementedError("Batched tracking is not yet supported")

        assigned_tracklets, new_tracklets, unassigned_tracklets = self.update(sequence, tracklets)

        # Manage tracklet staleness
        assigned_tracklets = self.reset_staleness(assigned_tracklets)
        unassigned_tracklets = self.increment_staleness(unassigned_tracklets)
        non_stale_tracklets, stale_tracklets = self.separate_stale_tracklets(unassigned_tracklets)
        stale_tracklets = self.cleanup_tracklets(stale_tracklets)

        # Report tracklet status
        logger.debug(f"assigned: {len(assigned_tracklets)}, new: {len(new_tracklets)}, unassigned: {len(non_stale_tracklets)}, stale: {len(stale_tracklets)}")

        # Update alive and dead tracklets
        self.alive_tracklets = assigned_tracklets + new_tracklets + non_stale_tracklets
        self.dead_tracklets += stale_tracklets

    def track(self, sequence: Union[Iterable[Any], np.ndarray]) -> Tracklet:
        if not isinstance(sequence, (Iterable, np.ndarray)):
            raise ValueError("Input 'sequence' must be an iterable or numpy array of frames/batches")
        self.reset()
        self.pre_track()
        with tqdm(range(0, len(sequence) - self.window_size + 1, self.step_size), desc="Tracking Progress") as t:
            for i in t:
                self.process_sequence_item(sequence[i : i + self.window_size].squeeze())
                t.set_postfix_str(f"Active: {len(self.alive_tracklets)}, Dead: {len(self.dead_tracklets)}", refresh=True)
        self.alive_tracklets = self.cleanup_tracklets(self.alive_tracklets)
        print(self.alive_tracklets)
        print(self.dead_tracklets)
        self.post_track()
        bbdf = self.to_bbdf()
        return bbdf

    def cleanup_tracklets(self, tracklets):
        for i, _ in enumerate(tracklets):
            tracklets[i].cleanup()
        
        filter_short_tracklets = lambda tracklet: len(tracklet) >= self.min_length
        tracklets = list(filter(filter_short_tracklets, tracklets))
        return tracklets

    def increment_staleness(self, tracklets):
        for i, _ in enumerate(tracklets):
            tracklets[i].staleness += 1
        return tracklets

    def reset_staleness(self, tracklets):
        for i, _ in enumerate(tracklets):
            tracklets[i].staleness = 0
        return tracklets
    def pre_track(self):
        # Hook that subclasses can override
        pass

    def post_track(self):
        pass

    def reset(self):
        # Initialize the single object tracker
        logger.debug("Initializing tracker...")
        self.alive_tracklets = []
        self.dead_tracklets = []
        self.frame_count = 0
        logger.debug("Tracker initialized.")

    def _check_required_observations(self, target: Dict[str, Any]):
        missing_types = [required_type for required_type in self.required_observation_types if required_type not in target]

        if missing_types:
            required_types_str = ", ".join(self.required_observation_types)
            missing_types_str = ", ".join(missing_types)
            current_types_str = ", ".join(target.keys())

            raise ValueError(
                f"Input 'target' is missing the following required types: {missing_types_str}.\n"
                f"Required types: {required_types_str}\n"
                f"Current types in 'target': {current_types_str}"
            )

    def check_updated_state(self, state: Dict[str, Any]):
        if not isinstance(state, dict):
            raise ValueError("The `update` method must return a dictionary.")

        missing_types = [required_type for required_type in self.required_observation_types if required_type not in state]

        if missing_types:
            missing_types_str = ", ".join(missing_types)
            raise ValueError(f"The returned state from `update` is missing the following required types: {missing_types_str}.")

    def create_tracklet(self, state: Dict[str, Any]):
        tracklet = Tracklet(max_staleness=self.max_staleness)
        for required_type in self.required_observation_types:
            tracklet.register_observation_type(required_type)
        for required_type in self.required_state_types:
            tracklet.register_state_type(required_type)

        self._check_required_observations(state)
        self.update_tracklet(tracklet, state)
        return tracklet

    def to_bbdf(self):
        """Create a bounding box dataframe."""
        all_tracklets = self.alive_tracklets + self.dead_tracklets
        return pd.concat([t.to_bbdf() for t in all_tracklets], axis=1).sort_index()

    def separate_stale_tracklets(self, unassigned_tracklets):
        stale_tracklets, non_stale_tracklets = [], []
        for tracklet in unassigned_tracklets:
            if tracklet.is_stale():
                stale_tracklets.append(tracklet)
            else:
                non_stale_tracklets.append(tracklet)
        return non_stale_tracklets, stale_tracklets

    @property
    def required_observation_types(self):
        raise NotImplementedError

    @property
    def required_state_types(self):
        raise NotImplementedError

    @property
    def hparam_searh_space(self):
        return {}

    def create_hparam_dict(self):
        hparam_search_space = {}
        # Create a dictionary for all hyperparameters
        hparams = {"self": self.hparam_search_space} if hasattr(self, "hparam_search_space") else {}
        for attribute in vars(self):
            value = getattr(self, attribute)
            if hasattr(value, "hparam_search_space") and attribute not in hparam_search_space:
                hparams[attribute] = {}
                search_space = value.hparam_search_space
                for param_name, param_space in search_space.items():
                    hparams[attribute][param_name] = {
                        "type": param_space["type"],
                        "values": param_space.get("values"),
                        "low": param_space.get("low"),
                        "high": param_space.get("high"),
                    }
        return hparams

    def tune_hparams(
        self,
        frames_list,
        bbdf_gt_list,
        n_trials=100,
        hparam_search_space=None,
        verbose=False,
        return_study=False,
        use_bbdf=False,
        reuse_detections=False,
        sampler=None,
        pruner=None,
    ):
        def objective(trial: optuna.Trial):
            params = {}
            for attribute, param_space in hparams.items():
                params[attribute] = {}
                for param_name, param_values in param_space.items():
                    if param_values["type"] == "categorical":
                        params[attribute][param_name] = trial.suggest_categorical(param_name, param_values["values"])
                    elif param_values["type"] == "float":
                        params[attribute][param_name] = trial.suggest_float(param_name, param_values["low"], param_values["high"])
                    elif param_values["type"] == "logfloat":
                        params[attribute][param_name] = trial.suggest_float(
                            param_name,
                            param_values["low"],
                            param_values["high"],
                            log=True,
                        )
                    elif param_values["type"] == "int":
                        params[attribute][param_name] = trial.suggest_int(param_name, param_values["low"], param_values["high"])
                    else:
                        raise ValueError(f"Unknown parameter type: {param_values['type']}")

            # Apply the hyperparameters to the attributes of `self`
            for attribute, param_values in params.items():
                for param_name, param_value in param_values.items():
                    if attribute == "self":
                        setattr(self, param_name, param_value)
                    else:
                        setattr(getattr(self, attribute), param_name, param_value)

            scores = []
            for frames, bbdf_gt in zip(frames_list, bbdf_gt_list):
                self.reset()
                bbdf_pred = self.track(frames)
                score = hota_score(bbdf_pred, bbdf_gt)["HOTA"]
                scores.append(score)
                trial.report(np.mean(scores), step=len(scores))  # Report intermediate score
                if trial.should_prune():  # Check for pruning
                    raise optuna.TrialPruned()

            return np.mean(scores)  # return the average score

        hparams = hparam_search_space or self.create_hparam_dict()

        logger.info("Hyperparameter search space:")
        for attribute, param_space in hparams.items():
            logger.info(f"{attribute}:")
            for param_name, param_values in param_space.items():
                logger.info(f"\t{param_name}: {param_values}")
        if verbose:
            optuna.logging.set_verbosity(optuna.logging.INFO)
        else:
            optuna.logging.set_verbosity(optuna.logging.WARNING)

        if use_bbdf:
            raise NotImplementedError
        if reuse_detections:
            list_of_detections = []
            for frames in frames_list:
                for frame in frames:
                    list_of_detections.append(self.detection_model(frame)[0])

            # define dummy model
            dummy_detection_model = DummyDetectionModel(list_of_detections)
            og_detection_model = self.detection_model
            self.detection_model = dummy_detection_model

        if sampler is None:
            sampler = optuna.samplers.TPESampler(multivariate=True)
        if pruner is None:
            pruner = optuna.pruners.MedianPruner()

        study = optuna.create_study(direction="maximize", sampler=sampler, pruner=pruner)
        study.optimize(objective, n_trials=n_trials)

        if reuse_detections:
            # reset detection model
            self.detection_model = og_detection_model
        best_params = study.best_params
        best_iou = study.best_value
        if return_study:
            return best_params, best_iou, study
        return best_params, best_iou

    # def tune_hparams(
    #     self,
    #     frames_list: List[np.ndarray],
    #     bbdf_gt_list: List[pd.DataFrame],
    #     n_trials: int = 100,
    #     hparam_search_space: Optional[Dict[str, Any]] = None,
    #     verbose: bool = False,
    #     return_study: bool = False,
    #     use_bbdf: bool = False,
    #     reuse_detections: bool = False,
    #     sampler: Optional[optuna.samplers.BaseSampler] = None,
    #     pruner: Optional[optuna.pruners.BasePruner] = None,
    # ) -> Union[Tuple[Dict[str, Any], float], Tuple[Dict[str, Any], float, optuna.study.Study]]:
    #     """
    #     Tune hyperparameters using Optuna.

    #     Args:
    #         frames_list (List[np.ndarray]): List of frames to process.
    #         bbdf_gt_list (List[pd.DataFrame]): List of ground truth bounding box dataframes.
    #         n_trials (int, optional): Number of trials. Defaults to 100.
    #         hparam_search_space (Dict[str, Any], optional): Hyperparameter search space. Defaults to None.
    #         verbose (bool, optional): If True, output verbose logs. Defaults to False.
    #         return_study (bool, optional): If True, return the study object. Defaults to False.
    #         use_bbdf (bool, optional): If True, use bounding box dataframe. Defaults to False.
    #         reuse_detections (bool, optional): If True, reuse detections. Defaults to False.
    #         sampler (optuna.samplers.BaseSampler, optional): Sampler for Optuna. Defaults to None.
    #         pruner (optuna.pruners.BasePruner, optional): Pruner for Optuna. Defaults to None.

    #     Returns:
    #         Union[Tuple[Dict[str, Any], float], Tuple[Dict[str, Any], float, optuna.study.Study]]: Best parameters, best IOU, and optionally the study object.
    #     """
    #     def objective(trial: optuna.Trial) -> float:
    #         params = self._suggest_params(trial, hparams)
    #         self._apply_params(params)
    #         scores = self._compute_scores(frames_list, bbdf_gt_list)
    #         return np.mean(scores)

    #     hparams = self.create_hparam_dict(hparam_search_space)
    #     self._log_hparams(hparams, verbose)

    #     if use_bbdf:
    #         raise NotImplementedError
    #     if reuse_detections:
    #         list_of_detections = self._get_detections(frames_list)
    #         self._set_dummy_detection_model(list_of_detections)

    #     sampler = sampler or optuna.samplers.TPESampler(multivariate=True)
    #     pruner = pruner or optuna.pruners.MedianPruner()

    #     study = optuna.create_study(direction="maximize", sampler=sampler, pruner=pruner)
    #     study.optimize(objective, n_trials=n_trials)

    #     if reuse_detections:
    #         self._reset_detection_model()

    #     return self._get_study_results(study, return_study)
