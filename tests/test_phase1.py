"""Phase 1 automated tests.

T1.1 - Landmark count (wrapper returns 478 landmarks for a face).
T1.2 - No-face handling (returns None for blank image).
T1.4 - Threaded capture returns latest (slow consumer test).
"""
import time
from typing import Optional
import urllib.request
import os

import cv2
import numpy as np

from capture.camera import Camera
from vision.face_mesh import FaceMeshWrapper


def get_sample_face() -> Optional[np.ndarray]:
    """Download a standard sample face image if not exists, and load it."""
    os.makedirs("tests/data", exist_ok=True)
    path = "tests/data/sample_face.jpg"
    if not os.path.exists(path):
        # A reliable URL to a public domain face image (Lenna).
        url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"
        try:
            urllib.request.urlretrieve(url, path)
        except Exception:
            return None
            
    img = cv2.imread(path)
    return img


def test_T1_1_landmark_count():
    """T1.1: run wrapper on a saved sample face image -> 478 landmarks, x,y in [0,1]."""
    img = get_sample_face()
    if img is None:
        assert False, "Failed to load sample face image"
        
    wrapper = FaceMeshWrapper()
    landmarks = wrapper.process(img)
    wrapper.close()
    
    assert landmarks is not None, "Failed to detect face in sample image"
    assert landmarks.shape == (478, 2), f"Expected 478 landmarks, got {landmarks.shape[0]}"
    
    # Check bounds (allowing a tiny margin for MediaPipe points that might extend slightly off-image)
    assert np.all(landmarks >= -0.1) and np.all(landmarks <= 1.1), "Landmarks out of expected bounds"


def test_T1_2_no_face_handling():
    """T1.2: run wrapper on a blank/noise image -> Returns 'no face' (None), no exception."""
    blank_img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    wrapper = FaceMeshWrapper()
    landmarks = wrapper.process(blank_img)
    wrapper.close()
    
    assert landmarks is None, "Expected None for blank image, got landmarks"


def test_T1_4_threaded_capture_returns_latest(monkeypatch):
    """T1.4: Unit test with a fake slow consumer -> Consumer always receives newest frame.
    
    We monkeypatch cv2.VideoCapture to return predictable frames.
    """
    class MockCap:
        def __init__(self, *args):
            self.frame_idx = 0
            
        def isOpened(self):
            return True
            
        def read(self):
            # Return a frame where the first pixel encodes the frame index
            img = np.zeros((10, 10, 3), dtype=np.uint32)
            img[0, 0, 0] = self.frame_idx
            self.frame_idx += 1
            # Simulate high FPS camera (e.g., fast read)
            time.sleep(0.01)
            return True, img
            
        def release(self):
            pass

    monkeypatch.setattr(cv2, "VideoCapture", MockCap)
    
    cam = Camera(camera_index=0)
    cam.start()
    
    try:
        time.sleep(0.1)  # wait for thread to start and read some frames
        
        frame1 = cam.read()
        assert frame1 is not None
        idx1 = frame1[0, 0, 0]
        
        # Simulate a SLOW consumer (e.g. processing took 0.2 seconds)
        time.sleep(0.2)
        
        frame2 = cam.read()
        idx2 = frame2[0, 0, 0]
        
        # The thread reads a frame every 0.01 seconds. In 0.2s it should have read ~20 frames.
        # So idx2 should be much larger than idx1.
        assert idx2 > idx1 + 5, f"Expected a much newer frame, but got {idx2} after {idx1}. Frame buffer might be queuing!"
    finally:
        cam.stop()
