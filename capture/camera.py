"""Threaded webcam capture.

Reads from the camera in a background thread and keeps only the latest frame.
This prevents OpenCV from building up a queue of old frames if processing is slow.
"""
import logging
import threading
import time
from typing import Optional

import cv2
import numpy as np

import config


class Camera:
    """Threaded webcam capture returning only the most recent frame."""

    def __init__(self, camera_index: int = config.CAMERA_INDEX):
        self.logger = logging.getLogger(__name__)
        self.camera_index = camera_index
        self._cap = cv2.VideoCapture(self.camera_index)
        
        if not self._cap.isOpened():
            self.logger.error("Failed to open camera index %d", self.camera_index)
            raise RuntimeError(f"Cannot open camera index {self.camera_index}")
            
        self._lock = threading.Lock()
        self._latest_frame: Optional[np.ndarray] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> "Camera":
        """Start the background capture thread."""
        self._running = True
        self._thread = threading.Thread(target=self._update, daemon=True)
        self._thread.start()
        self.logger.info("Camera capture thread started")
        return self

    def _update(self) -> None:
        """Background loop continuously reading frames."""
        while self._running:
            ret, frame = self._cap.read()
            if ret:
                with self._lock:
                    self._latest_frame = frame
            else:
                self.logger.warning("Failed to grab frame from camera")
                time.sleep(0.01)

    def read(self) -> Optional[np.ndarray]:
        """Get the most recent frame. Returns a copy to prevent modification issues."""
        with self._lock:
            if self._latest_frame is not None:
                return self._latest_frame.copy()
            return None

    def stop(self) -> None:
        """Stop the background thread and release the camera."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._cap.release()
        self.logger.info("Camera capture thread stopped and camera released")
