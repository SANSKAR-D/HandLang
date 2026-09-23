"""MediaPipe Face Mesh wrapper.

Detects faces and extracts refined landmarks (including irises).
"""
import logging
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

import config

mp_face_mesh = mp.solutions.face_mesh


class FaceMeshWrapper:
    """Wrapper for MediaPipe Face Mesh."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=config.FACE_MESH_MAX_FACES,
            refine_landmarks=config.FACE_MESH_REFINE_LANDMARKS,
            min_detection_confidence=config.FACE_MESH_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.FACE_MESH_MIN_TRACKING_CONFIDENCE,
        )
        self.logger.info("MediaPipe Face Mesh initialized (refine_landmarks=%s)", config.FACE_MESH_REFINE_LANDMARKS)

    def process(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Process an OpenCV BGR frame and return landmarks.
        
        Args:
            frame: BGR image numpy array.
            
        Returns:
            An array of shape (N, 2) with normalized (x, y) coordinates,
            or None if no face is detected. N should be 478 if refine_landmarks=True.
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # To improve performance, optionally mark the image as not writeable
        rgb_frame.flags.writeable = False
        results = self._face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return None
            
        # We only care about the first face found
        face_landmarks = results.multi_face_landmarks[0]
        
        # Convert to numpy array of (x, y)
        points = np.zeros((len(face_landmarks.landmark), 2), dtype=np.float32)
        for i, landmark in enumerate(face_landmarks.landmark):
            points[i] = [landmark.x, landmark.y]
            
        return points
        
    def close(self):
        """Clean up MediaPipe resources."""
        self._face_mesh.close()
