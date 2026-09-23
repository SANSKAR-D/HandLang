import cv2
import mediapipe as mp
import numpy as np

import config

class HandTracker:
    """Detects hands in images and returns 3D landmarks + AI Gesture Recognition."""

    def __init__(self) -> None:
        BaseOptions = mp.tasks.BaseOptions
        GestureRecognizer = mp.tasks.vision.GestureRecognizer
        GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path='models/gesture_recognizer.task'),
            running_mode=VisionRunningMode.IMAGE,
            num_hands=1
        )
        self.recognizer = GestureRecognizer.create_from_options(options)

    def process(self, frame_bgr: np.ndarray) -> tuple[str, float, np.ndarray, str]:
        """Process a BGR frame and return gesture, confidence, landmarks, handedness.

        Returns:
            Tuple of (gesture_label, confidence, landmarks_array, handedness_str).
            Returns ("NONE", 0.0, None, "NONE") if no hand is detected.
        """
        # MediaPipe requires RGB images
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        results = self.recognizer.recognize(mp_image)

        if not results.gestures or not results.hand_landmarks:
            return "NONE", 0.0, None, "NONE"

        # Get best gesture
        top_gesture = results.gestures[0][0]
        gesture_name = top_gesture.category_name
        confidence = top_gesture.score
        
        # Handedness (Left/Right)
        handedness = results.handedness[0][0].category_name
        
        # Get landmarks
        hand_landmarks = results.hand_landmarks[0]
        landmarks = np.zeros((21, 3), dtype=np.float32)
        for i, lm in enumerate(hand_landmarks):
            landmarks[i] = [lm.x, lm.y, lm.z]

        return gesture_name, confidence, landmarks, handedness

    def close(self) -> None:
        """Release MediaPipe resources."""
        self.recognizer.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
