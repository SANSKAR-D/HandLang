"""Automated tests for Phase 5 (Classifier & Stabilizer)."""

import os
import tempfile

import numpy as np

from language.tokens import Token, TokenType
from vision.classifier import GestureClassifier
from vision.stabilizer import TokenStabilizer

# ── Classifier Tests ────────────────────────────────────────────────────────


def test_T5_1_classifier_load() -> None:
    """T5.1: Classifier load without error."""
    clf = GestureClassifier()
    # Loading non-existent returns False, does not crash
    assert clf.load("non_existent_model.joblib") is False
    
    # Train dummy model, save and load
    X = np.random.rand(10, 9)
    y = np.array(["FIST"] * 5 + ["PALM"] * 5)
    clf.train(X, y)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "model.joblib")
        clf.save(path)
        
        clf2 = GestureClassifier()
        assert clf2.load(path) is True
        assert clf2.is_loaded


def test_T5_2_classifier_inference() -> None:
    """T5.2: Inference on known feature vector."""
    clf = GestureClassifier()
    # Train dummy model
    X = np.zeros((10, 9))
    X[0:5] = 1.0 # FIST
    X[5:10] = 0.0 # PALM
    y = np.array(["FIST"] * 5 + ["PALM"] * 5)
    clf.train(X, y)
    
    label, conf = clf.predict(np.ones(9))
    assert label == "FIST"
    assert conf > 0.8
    
    label, conf = clf.predict(np.zeros(9))
    assert label == "PALM"


# ── Stabilizer Tests ────────────────────────────────────────────────────────


def test_T5_3_stabilizer_emit() -> None:
    """T5.3: Send 10 FIST frames, emits REPEAT on frame 10 (N=10)."""
    stab = TokenStabilizer(frames_required=10)
    
    emitted = []
    for _ in range(9):
        token = stab.process_frame("FIST")
        if token: emitted.append(token)
    assert len(emitted) == 0
    
    token = stab.process_frame("FIST")
    assert token is not None
    assert token.type == TokenType.REPEAT


def test_T5_4_stabilizer_debounce() -> None:
    """T5.4: 5 FIST, 2 PALM, 5 FIST -> emits nothing (N=10)."""
    stab = TokenStabilizer(frames_required=10)
    
    for _ in range(5):
        assert stab.process_frame("FIST") is None
        
    for _ in range(2):
        assert stab.process_frame("PALM") is None
        
    for _ in range(5):
        assert stab.process_frame("FIST") is None


def test_T5_7_undo_gesture() -> None:
    """T5.7: Emits UNDO token."""
    stab = TokenStabilizer(frames_required=5)
    
    # "THUMBS_DOWN" maps to UNDO
    for _ in range(4):
        stab.process_frame("THUMBS_DOWN")
        
    token = stab.process_frame("THUMBS_DOWN")
    assert token is not None
    assert token.type == TokenType.UNDO
