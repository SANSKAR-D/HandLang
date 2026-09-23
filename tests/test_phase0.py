"""Phase 0 automated tests.

Only one [A] test exists for Phase 0 in TESTPLAN.md:
  T0.3 – Test runner works (pytest exits with code 0).

We split it into two focused test functions, both mapped to T0.3.
"""

import importlib


def test_T0_3_config_importable() -> None:
    """T0.3: config module is importable and exposes expected constants."""
    config = importlib.import_module("config")

    # Camera constants
    assert hasattr(config, "CAMERA_INDEX"), "config.CAMERA_INDEX missing"
    assert isinstance(config.CAMERA_INDEX, int)
    assert config.CAMERA_INDEX >= 0

    # FPS test constant
    assert hasattr(config, "FPS_TEST_FRAME_COUNT"), "config.FPS_TEST_FRAME_COUNT missing"
    assert isinstance(config.FPS_TEST_FRAME_COUNT, int)
    assert config.FPS_TEST_FRAME_COUNT > 0

    # Logging constants
    assert hasattr(config, "LOG_LEVEL"), "config.LOG_LEVEL missing"
    assert hasattr(config, "LOG_FORMAT"), "config.LOG_FORMAT missing"


def test_T0_3_packages_importable() -> None:
    """T0.3: all sub-package __init__.py files are importable."""
    packages = ["capture", "vision", "gaze", "control", "ui", "evaluation"]
    for pkg in packages:
        mod = importlib.import_module(pkg)
        assert mod is not None, f"Failed to import package '{pkg}'"
