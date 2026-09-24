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

        # Get landmarks early so we can use them for custom gestures
        hand_landmarks = results.hand_landmarks[0]
        landmarks = np.zeros((21, 3), dtype=np.float32)
        for i, lm in enumerate(hand_landmarks):
            landmarks[i] = [lm.x, lm.y, lm.z]

        # ── Custom Cross gesture ✝ (index UP + middle SIDEWAYS, ring+pinky curled) ──
        # Index pointing UP: more vertical travel than horizontal, tip above knuckle.
        idx_dy = landmarks[5][1] - landmarks[8][1]   # positive = tip is ABOVE knuckle
        idx_dx = abs(landmarks[8][0] - landmarks[5][0])
        index_vertical = idx_dy > 0.06 and idx_dy > idx_dx   # up and more vertical than horizontal

        # Middle pointing SIDEWAYS: more horizontal travel than vertical, and extended.
        mid_dx = abs(landmarks[12][0] - landmarks[9][0])
        mid_dy = abs(landmarks[12][1] - landmarks[9][1])
        middle_horizontal = mid_dx > 0.06 and mid_dx > mid_dy  # sideways and more horizontal than vertical

        # Ring and pinky must be curled down
        ring_dn  = landmarks[16][1] > landmarks[13][1]
        pinky_dn = landmarks[20][1] > landmarks[17][1]

        if index_vertical and middle_horizontal and ring_dn and pinky_dn:
            handedness = results.handedness[0][0].category_name
            return "Cross", 1.0, landmarks, handedness

        # ── Custom Pinch / OK gesture (thumb tip ↔ index tip distance) ──
        # Landmark 4 = thumb tip, Landmark 8 = index tip
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        pinch_dist = np.linalg.norm(thumb_tip - index_tip)
        PINCH_THRESHOLD = 0.06  # Normalized coords (tune if needed)
        if pinch_dist < PINCH_THRESHOLD:
            handedness = results.handedness[0][0].category_name
            return "OK_Pinch", 1.0, landmarks, handedness

        # Get best gesture from MediaPipe
        top_gesture = results.gestures[0][0]
        gesture_name = top_gesture.category_name
        confidence = top_gesture.score
        
        # Handedness (Left/Right)
        handedness = results.handedness[0][0].category_name

        return gesture_name, confidence, landmarks, handedness

    def close(self) -> None:
        """Release MediaPipe resources."""
        self.recognizer.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
