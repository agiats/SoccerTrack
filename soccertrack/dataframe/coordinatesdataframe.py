from __future__ import annotations

import json
from ast import literal_eval
from typing import Mapping, Optional, Union, Any

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation
from mplsoccer import Pitch
from numpy.typing import ArrayLike, NDArray

from soccertrack.types import _pathlike
from soccertrack.logger import logger
from soccertrack.dataframe.base import SoccerTrackMixin


class CoordinatesDataFrame(SoccerTrackMixin, pd.DataFrame):

    _metadata = [
        "source_keypoints",
        "target_keypoints",
    ]

    @property
    def _constructor(self):
        return CoordinatesDataFrame

    @property
    def H(self) -> NDArray[np.float64]:
        """Calculate the homography transformation matrix from pitch to video
        space.

        Returns:
            NDArray[np.float64]: homography transformation matrix.
        """
        H, *_ = cv2.findHomography(
            self.source_keypoints, self.target_keypoints, cv2.RANSAC, 5.0
        )
        return H

    def set_keypoints(
        self,
        source_keypoints: Optional[ArrayLike] = None,
        target_keypoints: Optional[ArrayLike] = None,
        mapping: Optional[Mapping] = None,
        mapping_file: Optional[_pathlike] = None,
    ) -> None:
        """Set the keypoints for the homography transformation. Make sure that
        the target keypoints are the pitch coordinates. Also each keypoint must
        be a tuple of (Lon, Lat) or (x, y) coordinates.

        Args:
            source_keypoints (Optional[ArrayLike], optional): Keypoints in pitch space. Defaults to None.
            target_keypoints (Optional[ArrayLike], optional): Keypoints in video space. Defaults to None.
        """

        if mapping_file is not None:
            with open(mapping_file, "r") as f:
                mapping = json.load(f)
        if mapping is not None:
            target_keypoints, source_keypoints = [], []
            for target_kp, source_kp in mapping.items():
                if isinstance(target_kp, str):
                    target_kp = literal_eval(target_kp)
                if isinstance(source_kp, str):
                    source_kp = literal_eval(source_kp)
                target_keypoints.append(target_kp)
                source_keypoints.append(source_kp)

        self.source_keypoints = np.array(source_keypoints)
        self.target_keypoints = np.array(target_keypoints)

    def to_pitch_coordinates(self, drop=True):
        """Convert image coordinates to pitch coordinates."""
        transformed_groups = []
        for i, g in self.iter_players():
            pts = g[[(i[0], i[1], "Lon"), (i[0], i[1], "Lat")]].values
            x, y = cv2.perspectiveTransform(np.asarray([pts]), self.H).squeeze().T
            g[(i[0], i[1], "x")] = x
            g[(i[0], i[1], "y")] = y

            if drop:
                g.drop(columns=[(i[0], i[1], "Lon"), (i[0], i[1], "Lat")], inplace=True)
            transformed_groups.append(g)

        return self._constructor(pd.concat(transformed_groups, axis=1))

    # def visualize_frames

    @staticmethod
    def from_numpy(arr: np.ndarray):
        """Create a CoordinatesDataFrame from a numpy array of either shape (L, N, 2) or (L, N * 2) where L is the number of frames, N is the number of players and 2 is the number of coordinates (x, y).

        Args:
            arr (np.ndarray): Numpy array.

        Returns:
            CoordinatesDataFrame: CoordinatesDataFrame.
        """
        assert arr.ndim in (2, 3), "Array must be of shape (L, N, 2) or (L, N * 2)"
        if arr.ndim == 3:
            arr = arr.reshape(arr.shape[0], -1)

        df = pd.DataFrame(arr)

        team_ids = [0] * 22 + [1] * 22 + ["ball"] * 2
        _players = list(np.linspace(0, 10, 22).round().astype(int))

        player_ids = _players + _players + [0, 0]
        attributes = ["x", "y"] * 23

        idx = pd.MultiIndex.from_arrays(
            [team_ids, player_ids, attributes],
        )

        # change multicolumn
        df = CoordinatesDataFrame(df.values, index=df.index, columns=idx)

        df.rename_axis(["TeamID", "PlayerID", "Attributes"], axis=1, inplace=True)
        df.index.name = "frame"

        return CoordinatesDataFrame(df)

    def visualize_frame(
        self,
        frame_idx: int,
        save_path: Optional[_pathlike] = None,
        ball_key: str = "ball",
        home_key: str = "0",
        away_key: str = "1",
        marker_kwargs: Optional[dict[str, Any]] = None,
        ball_kwargs: Optional[dict[str, Any]] = None,
        home_kwargs: Optional[dict[str, Any]] = None,
        away_kwargs: Optional[dict[str, Any]] = None,
        save_kwargs: Optional[dict[str, Any]] = None,
    ):
        """Visualize a single frame.

        Args:
            frame_idx: Frame number.
            save_path: Path to save the image. Defaults to None.
            ball_key: Key for the ball. Defaults to "ball".
            home_key: Key for the home team. Defaults to "0".
            away_key: Key for the away team. Defaults to "1".
            marker_kwargs: Keyword arguments for the markers.
            ball_kwargs: Keyword arguments specifically for the ball marker.
            home_kwargs: Keyword arguments specifically for the home team markers.
            away_kwargs: Keyword arguments specifically for the away team markers.
            save_kwargs: Keyword arguments for the save function.

        Note:
            `marker_kwargs` will be used for all markers but will be overwritten by `ball_kwargs`, `home_kwargs` and `away_kwargs`. All keyword arguments are passed to `plt.plot`. `save_kwargs` are passed to `plt.savefig`.
        """

        _marker_kwargs = dict(
            marker="o",
            markeredgecolor="None",
            linestyle="None",
            **(marker_kwargs) or {},
        )
        _ball_kwargs = dict(
            _marker_kwargs, zorder=3, ms=6, markerfacecolor="w", **(ball_kwargs) or {}
        )
        _home_kwargs = dict(
            _marker_kwargs, ms=10, markerfacecolor="b", **(home_kwargs) or {}
        )
        _away_kwargs = dict(
            _marker_kwargs, ms=10, markerfacecolor="r", **(away_kwargs) or {}
        )
        _save_kwargs = dict(facecolor="black", pad_inches=0.0, **(save_kwargs) or {})

        _df = self.copy()
        _df = _df[_df.index == frame_idx]

        df_ball = _df[ball_key]
        df_home = _df[home_key]
        df_away = _df[away_key]
        pitch = Pitch(
            pitch_color="black",
            line_color=(0.3, 0.3, 0.3),
            pitch_type="custom",
            pitch_length=105,
            pitch_width=68,
            label=False,
        )

        fig, ax = pitch.draw(figsize=(8, 5.2))

        ax.plot(
            df_ball.loc[:, (slice(None), "x")],
            df_ball.loc[:, (slice(None), "y")],
            **_ball_kwargs,
        )
        ax.plot(
            df_away.loc[:, (slice(None), "x")],
            df_away.loc[:, (slice(None), "y")],
            **_away_kwargs,
        )
        ax.plot(
            df_home.loc[:, (slice(None), "x")],
            df_home.loc[:, (slice(None), "y")],
            **_home_kwargs,
        )

        if save_path is not None:
            fig.savefig(save_path, **_save_kwargs)

    def visualize_frames(
        self,
        save_path: _pathlike,
        ball_key: str = "ball",
        home_key: str = "0",
        away_key: str = "1",
        marker_kwargs: Optional[dict[str, Any]] = None,
        ball_kwargs: Optional[dict[str, Any]] = None,
        home_kwargs: Optional[dict[str, Any]] = None,
        away_kwargs: Optional[dict[str, Any]] = None,
        save_kwargs: Optional[dict[str, Any]] = None,
    ):
        """Visualize a single frame.

        Args:
            frame_idx: Frame number.
            save_path: Path to save the image. Defaults to None.
            ball_key: Key for the ball. Defaults to "ball".
            home_key: Key for the home team. Defaults to "0".
            away_key: Key for the away team. Defaults to "1".
            marker_kwargs: Keyword arguments for the markers.
            ball_kwargs: Keyword arguments specifically for the ball marker.
            home_kwargs: Keyword arguments specifically for the home team markers.
            away_kwargs: Keyword arguments specifically for the away team markers.
            save_kwargs: Keyword arguments for the save function.

        Note:
            `marker_kwargs` will be used for all markers but will be overwritten by `ball_kwargs`, `home_kwargs` and `away_kwargs`. All keyword arguments are passed to `plt.plot`. `save_kwargs` are passed to `FuncAnimation.save`.
        """
        _marker_kwargs = dict(
            marker="o",
            markeredgecolor="None",
            linestyle="None",
            **(marker_kwargs) or {},
        )
        _ball_kwargs = dict(
            _marker_kwargs, zorder=3, ms=6, markerfacecolor="w", **(ball_kwargs) or {}
        )
        _home_kwargs = dict(
            _marker_kwargs, ms=10, markerfacecolor="b", **(home_kwargs) or {}
        )
        _away_kwargs = dict(
            _marker_kwargs, ms=10, markerfacecolor="r", **(away_kwargs) or {}
        )
        _save_kwargs = dict(
            dpi=100,
            fps=10,
            extra_args=["-vcodec", "libx264", "-pix_fmt", "yuv420p"],
            savefig_kwargs=dict(facecolor="black", pad_inches=0.0),
            **(save_kwargs) or {},
        )

        _df = self.copy()

        df_ball = _df[ball_key]
        df_home = _df[home_key]
        df_away = _df[away_key]
        pitch = Pitch(
            pitch_color="black",
            line_color=(0.3, 0.3, 0.3),
            pitch_type="custom",
            pitch_length=105,
            pitch_width=68,
            label=False,
        )

        fig, ax = pitch.draw(figsize=(8, 5.2))

        ball, *_ = ax.plot([], [], **_ball_kwargs)
        away, *_ = ax.plot([], [], **_away_kwargs)
        home, *_ = ax.plot([], [], **_home_kwargs)

        def animate(i):
            """Function to animate the data. Each frame it sets the data for the players and the ball."""
            # set the ball data with the x and y positions for the ith frame
            ball.set_data(
                df_ball.loc[:, (slice(None), "x")].iloc[i],
                df_ball.loc[:, (slice(None), "y")].iloc[i],
            )

            # set the player data using the frame id
            away.set_data(
                df_away.loc[:, (slice(None), "x")].iloc[i],
                df_away.loc[:, (slice(None), "y")].iloc[i],
            )
            home.set_data(
                df_home.loc[:, (slice(None), "x")].iloc[i],
                df_home.loc[:, (slice(None), "y")].iloc[i],
            )
            return ball, away, home

        anim = FuncAnimation(fig, animate, frames=len(_df), blit=True)

        try:
            anim.save(save_path, **_save_kwargs)
        except Exception as e:
            logger.error(
                "BrokenPipeError: Saving animation failed, which might be an ffmpeg problem. Trying again with different codec."
            )
            _save_kwargs["extra_args"] = ["-vcodec", "mpeg4", "-pix_fmt", "yuv420p"]
            try:
                anim.save(save_path, **_save_kwargs)
            except Exception as e:
                logger.error(
                    "Saving animation failed again. Exiting without saving the animation."
                )
                print(e)

    # @property
    # def _constructor_sliced(self):
    #     raise NotImplementedError("This pandas method constructs pandas.Series object, which is not yet implemented in {self.__name__}.")
