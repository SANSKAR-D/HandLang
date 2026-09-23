"""Phase 2 automated tests.

T2.1: EAR math
T2.2: Iris ratio bounds
T2.3 - T2.6: State machine variants
"""
import pytest
import numpy as np

import config
from vision.features import compute_ear, LEFT_EYE, compute_iris_ratio, LEFT_IRIS
from vision.blink import BlinkStateMachine, BlinkState


def test_T2_1_ear_math():
    """T2.1: EAR math (Synthetic landmarks: open eye vs flat eye)."""
    # Open eye
    landmarks = np.zeros((478, 2))
    # Horizontal
    landmarks[LEFT_EYE[0]] = [0.0, 0.5]
    landmarks[LEFT_EYE[3]] = [1.0, 0.5]
    # Verticals
    landmarks[LEFT_EYE[1]] = [0.25, 0.2]
    landmarks[LEFT_EYE[5]] = [0.25, 0.8]
    landmarks[LEFT_EYE[2]] = [0.75, 0.2]
    landmarks[LEFT_EYE[4]] = [0.75, 0.8]
    
    open_ear = compute_ear(landmarks, LEFT_EYE)
    assert open_ear > 0.25, f"Expected open EAR > 0.25, got {open_ear}"
    
    # Flat eye
    landmarks[LEFT_EYE[1]] = [0.25, 0.48]
    landmarks[LEFT_EYE[5]] = [0.25, 0.52]
    landmarks[LEFT_EYE[2]] = [0.75, 0.48]
    landmarks[LEFT_EYE[4]] = [0.75, 0.52]
    
    flat_ear = compute_ear(landmarks, LEFT_EYE)
    assert flat_ear < 0.10, f"Expected closed EAR < 0.10, got {flat_ear}"


def test_T2_2_iris_ratio_bounds():
    """T2.2: Iris ratio bounds."""
    landmarks = np.zeros((478, 2))
    landmarks[LEFT_EYE[0]] = [0.0, 0.5] # Left
    landmarks[LEFT_EYE[3]] = [1.0, 0.5] # Right
    landmarks[LEFT_EYE[1]] = [0.5, 0.0] # Top
    landmarks[LEFT_EYE[2]] = [0.5, 0.0]
    landmarks[LEFT_EYE[4]] = [0.5, 1.0] # Bot
    landmarks[LEFT_EYE[5]] = [0.5, 1.0]
    
    # Left iris
    landmarks[LEFT_IRIS] = [0.0, 0.5]
    rx_left, ry = compute_iris_ratio(landmarks, LEFT_EYE, LEFT_IRIS)
    
    # Center iris
    landmarks[LEFT_IRIS] = [0.5, 0.5]
    rx_center, ry = compute_iris_ratio(landmarks, LEFT_EYE, LEFT_IRIS)
    
    # Right iris
    landmarks[LEFT_IRIS] = [1.0, 0.5]
    rx_right, ry = compute_iris_ratio(landmarks, LEFT_EYE, LEFT_IRIS)
    
    assert 0.0 <= rx_left <= 1.0
    assert 0.0 <= rx_center <= 1.0
    assert 0.0 <= rx_right <= 1.0
    
    assert abs(rx_center - 0.5) < 0.01, f"Expected ~0.5, got {rx_center}"
    assert rx_left < rx_center < rx_right


def test_T2_3_state_machine_natural():
    """T2.3: Natural blink."""
    sm = BlinkStateMachine(baseline_ear=0.30)
    
    t = 0.0
    # open
    ev = sm.update(0.30, t)
    assert not ev
    
    # closed
    t += 0.1
    ev = sm.update(0.10, t)
    
    # wait 0.15s (natural)
    t += 0.15
    ev = sm.update(0.10, t)
    
    # open
    t += 0.05
    ev = sm.update(0.30, t)
    
    # Advance time to clear timeout
    t += 1.5
    ev = sm.update(0.30, t)
    
    assert "LEFT_CLICK" not in ev
    assert "RIGHT_CLICK" not in ev


def test_T2_4_state_machine_deliberate():
    """T2.4: Deliberate blink gives left click after timeout."""
    sm = BlinkStateMachine(baseline_ear=0.30)
    t = 0.0
    sm.update(0.30, t)
    
    # closed
    t += 0.1
    sm.update(0.10, t)
    
    # wait 0.5s (deliberate)
    t += 0.5
    sm.update(0.10, t)
    
    # opening
    t += 0.05
    sm.update(0.30, t)
    
    # open (resolves blink)
    t += 0.05
    ev = sm.update(0.30, t)
    assert not ev  # No click yet, it's pending
    
    # Wait for timeout
    t += config.DOUBLE_BLINK_TIMEOUT + 0.1
    ev = sm.update(0.30, t)
    assert "LEFT_CLICK" in ev


def test_T2_5_state_machine_double():
    """T2.5: Double blink -> right click."""
    sm = BlinkStateMachine(baseline_ear=0.30)
    t = 0.0
    sm.update(0.30, t)
    
    # Blink 1
    t += 0.1
    sm.update(0.10, t) # CLOSING
    t += 0.5
    sm.update(0.10, t) # CLOSED
    t += 0.1
    sm.update(0.30, t) # OPENING
    t += 0.05
    sm.update(0.30, t) # OPEN
    
    assert sm.pending_left_click
    
    # Blink 2 (within 1s)
    t += 0.2
    sm.update(0.10, t) # CLOSING
    t += 0.5
    sm.update(0.10, t) # CLOSED
    t += 0.1
    sm.update(0.30, t) # OPENING
    t += 0.05
    ev = sm.update(0.30, t) # OPEN
    
    assert "RIGHT_CLICK" in ev
    assert not sm.pending_left_click
    
    # Wait out the timeout to ensure no spurious left clicks
    t += config.DOUBLE_BLINK_TIMEOUT + 0.1
    ev = sm.update(0.30, t)
    assert "LEFT_CLICK" not in ev


def test_T2_6_state_machine_jitter():
    """T2.6: Jitter near threshold doesn't cause events."""
    sm = BlinkStateMachine(baseline_ear=0.30)
    t = 0.0
    sm.update(0.30, t)
    
    # Oscillate near close_thresh (0.21)
    for _ in range(20):
        t += 0.1
        sm.update(0.22, t)
        t += 0.1
        sm.update(0.20, t)  # 0.20 < 0.21, but won't trigger full open/close cycle because open_thresh is 0.24
        
    t += 1.5
    ev = sm.update(0.30, t)
    assert "LEFT_CLICK" not in ev
