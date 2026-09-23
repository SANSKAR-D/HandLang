"""Phase 0 automated tests — T0.2."""

import importlib


def test_T0_2_config_importable() -> None:
    """T0.2: config module importable with expected constants."""
    cfg = importlib.import_module("config")
    assert hasattr(cfg, "MAX_INTERPRETER_STEPS")
    assert hasattr(cfg, "CANVAS_WIDTH")
    assert hasattr(cfg, "TURTLE_COLORS")
    assert hasattr(cfg, "LOG_LEVEL")


def test_T0_2_packages_importable() -> None:
    """T0.2: all sub-packages importable."""
    for pkg in ("vision", "language", "runtime", "ui", "tools"):
        importlib.import_module(pkg)
