"""Debug drawing overlay routines."""

import cv2
import numpy as np

import config


# MediaPipe indices for the eyes
LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
LEFT_IRIS_CENTER_INDEX = 468
RIGHT_IRIS_CENTER_INDEX = 473


def draw_landmarks(frame: np.ndarray, landmarks: np.ndarray) -> None:
    """Draw eye contours and iris centers on the frame.
    
    Args:
        frame: The BGR image to draw on (modified in place).
        landmarks: Normalized landmark array of shape (N, 2).
    """
    h, w = frame.shape[:2]
    
    def to_pixel(normalized_pt):
        return int(normalized_pt[0] * w), int(normalized_pt[1] * h)

    # Draw left eye contour
    left_eye_pts = np.array([to_pixel(landmarks[idx]) for idx in LEFT_EYE_INDICES], dtype=np.int32)
    cv2.polylines(frame, [left_eye_pts], isClosed=True, color=config.COLOR_EYE_CONTOUR, thickness=1)
    
    # Draw right eye contour
    right_eye_pts = np.array([to_pixel(landmarks[idx]) for idx in RIGHT_EYE_INDICES], dtype=np.int32)
    cv2.polylines(frame, [right_eye_pts], isClosed=True, color=config.COLOR_EYE_CONTOUR, thickness=1)
    
    # Draw iris centers
    if len(landmarks) > RIGHT_IRIS_CENTER_INDEX:
        l_iris = to_pixel(landmarks[LEFT_IRIS_CENTER_INDEX])
        r_iris = to_pixel(landmarks[RIGHT_IRIS_CENTER_INDEX])
        
        cv2.circle(frame, l_iris, 2, config.COLOR_IRIS, -1)
        cv2.circle(frame, r_iris, 2, config.COLOR_IRIS, -1)


def draw_status(frame: np.ndarray, fps: float, face_detected: bool) -> None:
    """Draw FPS and warnings.
    
    Args:
        frame: The BGR image to draw on (modified in place).
        fps: Current frames per second.
        face_detected: Whether a face is currently detected.
    """
    cv2.putText(
        frame, 
        f"FPS: {fps:.1f}", 
        (10, 30), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        0.7, 
        config.COLOR_TEXT, 
        2
    )
    
    if not face_detected:
        cv2.putText(
            frame, 
            "No face detected", 
            (10, 60), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            config.COLOR_WARNING, 
            2
        )


def draw_baseline_progress(frame: np.ndarray, progress: float) -> None:
    """Draw a progress bar for the baseline calibration phase."""
    h, w = frame.shape[:2]
    
    cv2.putText(
        frame, 
        "Hold eyes open naturally to calibrate...", 
        (w // 2 - 200, h - 70), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        0.7, 
        config.COLOR_TEXT, 
        2
    )
    
    # Progress bar
    bar_w = 400
    bar_h = 20
    x = w // 2 - bar_w // 2
    y = h - 40
    
    cv2.rectangle(frame, (x, y), (x + bar_w, y + bar_h), config.COLOR_TEXT, 2)
    fill_w = int(bar_w * progress)
    if fill_w > 0:
        cv2.rectangle(frame, (x, y), (x + fill_w, y + bar_h), config.COLOR_TEXT, -1)


def draw_features(frame: np.ndarray, ear: float, ratio_l: tuple, ratio_r: tuple) -> None:
    """Draw EAR and iris ratios."""
    text1 = f"EAR: {ear:.3f}"
    text2 = f"L Iris: ({ratio_l[0]:.2f}, {ratio_l[1]:.2f})"
    text3 = f"R Iris: ({ratio_r[0]:.2f}, {ratio_r[1]:.2f})"
    
    cv2.putText(frame, text1, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_TEXT, 2)
    cv2.putText(frame, text2, (10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_TEXT, 2)
    cv2.putText(frame, text3, (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_TEXT, 2)


def draw_events(frame: np.ndarray, recent_events: list[tuple[str, float]], current_time: float) -> None:
    """Draw click events that fade out over time."""
    h, w = frame.shape[:2]
    
    y = h // 2
    for event, timestamp in recent_events:
        age = current_time - timestamp
        if age < 1.0:
            # Flash bright yellow
            color = (0, 255, 255)
            cv2.putText(
                frame, 
                event, 
                (w // 2 - 100, y), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1.5, 
                color, 
                3
            )
            y += 50

