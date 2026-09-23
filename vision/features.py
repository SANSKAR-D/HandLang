"""Feature extraction from landmarks (EAR and Iris Ratios)."""
from typing import Tuple

import numpy as np

# Left eye indices: 33 (outer), 160 (top-outer), 158 (top-inner), 133 (inner), 153 (bot-inner), 144 (bot-outer)
LEFT_EYE = [33, 160, 158, 133, 153, 144]
# Right eye indices: 362 (inner), 385 (top-inner), 387 (top-outer), 263 (outer), 373 (bot-outer), 380 (bot-inner)
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

LEFT_IRIS = 468
RIGHT_IRIS = 473


def compute_ear(landmarks: np.ndarray, eye_indices: list[int]) -> float:
    """Compute Eye Aspect Ratio for a single eye.
    
    Args:
        landmarks: Shape (N, 2)
        eye_indices: List of 6 indices [p0, p1, p2, p3, p4, p5]
    """
    p0, p1, p2, p3, p4, p5 = eye_indices
    
    # Verticals
    v1 = np.linalg.norm(landmarks[p1] - landmarks[p5])
    v2 = np.linalg.norm(landmarks[p2] - landmarks[p4])
    
    # Horizontal
    h = np.linalg.norm(landmarks[p0] - landmarks[p3])
    
    if h == 0:
        return 0.0
        
    return float((v1 + v2) / (2.0 * h))


def get_both_ear(landmarks: np.ndarray) -> Tuple[float, float]:
    """Return (left_ear, right_ear)."""
    return (
        compute_ear(landmarks, LEFT_EYE),
        compute_ear(landmarks, RIGHT_EYE)
    )


def compute_iris_ratio(landmarks: np.ndarray, eye_indices: list[int], iris_idx: int) -> Tuple[float, float]:
    """Compute normalized iris (x, y) ratio via vector projection.
    
    Returns (ratio_x, ratio_y) in roughly [0, 1].
    x=0 is at the left side of the eye (screen space), x=1 is at the right side.
    y=0 is at the top of the eye, y=1 is at the bottom.
    """
    p_outer = landmarks[eye_indices[0]]
    p_inner = landmarks[eye_indices[3]]
    
    p_top = (landmarks[eye_indices[1]] + landmarks[eye_indices[2]]) / 2.0
    p_bot = (landmarks[eye_indices[4]] + landmarks[eye_indices[5]]) / 2.0
    
    p_iris = landmarks[iris_idx]
    
    # Ensure h_vec points from left (smaller x) to right (larger x)
    if p_outer[0] < p_inner[0]:
        h_vec = p_inner - p_outer
        origin_x = p_outer
    else:
        h_vec = p_outer - p_inner
        origin_x = p_inner
        
    # Ensure v_vec points from top (smaller y) to bottom (larger y)
    if p_top[1] < p_bot[1]:
        v_vec = p_bot - p_top
        origin_y = p_top
    else:
        v_vec = p_top - p_bot
        origin_y = p_bot

    iris_vec_x = p_iris - origin_x
    iris_vec_y = p_iris - origin_y
    
    h_len2 = np.dot(h_vec, h_vec)
    v_len2 = np.dot(v_vec, v_vec)
    
    ratio_x = np.dot(iris_vec_x, h_vec) / h_len2 if h_len2 > 0 else 0.5
    ratio_y = np.dot(iris_vec_y, v_vec) / v_len2 if v_len2 > 0 else 0.5
    
    return float(np.clip(ratio_x, 0.0, 1.0)), float(np.clip(ratio_y, 0.0, 1.0))
