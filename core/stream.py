import time
from typing import List, Optional

import cv2
import PIL.Image

from config import settings


class VideoStream:
    def __init__(self, video_path: Optional[str] = None, camera_index: Optional[int] = None):
        if video_path:
            self.cap = cv2.VideoCapture(video_path)
        else:
            idx = 0 if camera_index is None else camera_index
            self.cap = cv2.VideoCapture(idx)
        if not self.cap.isOpened():
            raise ValueError("Unable to open video source.")

    def close(self):
        if self.cap:
            self.cap.release()

    def _read_frame(self) -> Optional[PIL.Image.Image]:
        ret, frame = self.cap.read()
        if not ret:
            return None
        height, width = frame.shape[:2]
        if width > settings.MAX_WIDTH:
            scale = settings.MAX_WIDTH / width
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return PIL.Image.fromarray(frame_rgb)

    def get_frame_window(self, duration_s: float, fps: float) -> List[PIL.Image.Image]:
        frames: List[PIL.Image.Image] = []
        interval = 1.0 / max(fps, 0.1)
        start = time.time()
        while time.time() - start < duration_s:
            frame = self._read_frame()
            if frame is not None:
                frames.append(frame)
            time.sleep(interval)
        return frames


class VideoFileStreamer:
    def __init__(self, video_path: str, target_fps: float, max_width: int):
        self.video_path = video_path
        self.target_fps = target_fps
        self.max_width = max_width
        self.frame_interval = 1.0 / max(target_fps, 0.1)
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Unable to open video file: {video_path}")
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.original_fps = self.cap.get(cv2.CAP_PROP_FPS) or 0.0
        self.duration = (
            self.total_frames / self.original_fps if self.original_fps > 0 else 0.0
        )
        self.start_time: Optional[float] = None

    def close(self):
        if self.cap:
            self.cap.release()

    def start(self):
        self.start_time = time.time()

    def get_current_time(self) -> float:
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def is_finished(self) -> bool:
        if self.duration <= 0:
            return False
        return self.get_current_time() >= self.duration

    def _get_frame_at_index(self, frame_index: int) -> Optional[PIL.Image.Image]:
        frame_index = min(frame_index, self.total_frames - 1)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.cap.read()
        if not ret:
            return None
        height, width = frame.shape[:2]
        if width > self.max_width:
            scale = self.max_width / width
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return PIL.Image.fromarray(frame_rgb)

    def collect_frames_at_time(self, time_s: float, window_s: float) -> List[PIL.Image.Image]:
        if self.original_fps <= 0:
            return []
        start_frame = max(0, int(time_s * self.original_fps))
        frames_to_collect = max(1, int(window_s * self.target_fps))
        step = max(1, int(self.original_fps / self.target_fps))
        frames: List[PIL.Image.Image] = []
        for i in range(frames_to_collect):
            frame_index = start_frame + i * step
            if frame_index >= self.total_frames:
                break
            frame = self._get_frame_at_index(frame_index)
            if frame is not None:
                frames.append(frame)
        return frames

    def collect_frames_at_times(self, times_s: List[float], window_s: float) -> List[List[PIL.Image.Image]]:
        return [self.collect_frames_at_time(t, window_s) for t in times_s]

    def get_frame_for_current_time(self) -> Optional[PIL.Image.Image]:
        if self.start_time is None:
            return None
        current_time = self.get_current_time()
        if self.duration > 0 and current_time >= self.duration:
            return None
        target_frame = int(current_time * self.original_fps) if self.original_fps else 0
        return self._get_frame_at_index(target_frame)

    async def stream_frames(self, duration_s: Optional[float] = None):
        self.start()
        start = time.time()
        while True:
            if duration_s is not None and time.time() - start >= duration_s:
                break
            frame = self.get_frame_for_current_time()
            if frame is None:
                break
            yield frame
            time.sleep(self.frame_interval)

    def collect_frames(self, duration_s: Optional[float] = None) -> List[PIL.Image.Image]:
        self.start()
        frames: List[PIL.Image.Image] = []
        start = time.time()
        while True:
            if duration_s is not None and time.time() - start >= duration_s:
                break
            frame = self.get_frame_for_current_time()
            if frame is None:
                break
            frames.append(frame)
            time.sleep(self.frame_interval)
        return frames



