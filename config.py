"""HandLang – all tunable constants.

Every magic number lives here. Modules import from config instead of
hard-coding values.
"""

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = "INFO"
"""Root logger level."""

LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
"""Format string for log messages."""

# ---------------------------------------------------------------------------
# Camera (Phases 4+)
# ---------------------------------------------------------------------------
CAMERA_INDEX: int = 0
"""Default video-capture device index."""

MP_MIN_DETECTION_CONFIDENCE: float = 0.7
MP_MIN_TRACKING_CONFIDENCE: float = 0.5

# ---------------------------------------------------------------------------
# Stabilizer (Phase 5+)
# ---------------------------------------------------------------------------
STABILIZER_FRAMES_REQUIRED: int = 15
"""Consecutive frames of the same gesture to emit a token (~0.5 s at 30 FPS)."""

STABILIZER_CONFIDENCE_THRESHOLD: float = 0.8
"""Minimum classifier confidence to consider a frame."""

# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------
MAX_INTERPRETER_STEPS: int = 10_000
"""Hard cap on interpreter steps to prevent infinite loops."""

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
CANVAS_WIDTH: int = 800
"""Turtle canvas width in pixels."""

CANVAS_HEIGHT: int = 600
"""Turtle canvas height in pixels."""

CANVAS_BG_COLOR: str = "black"
"""Canvas background color."""

# ---------------------------------------------------------------------------
# Turtle colors (indexed by COLOR command argument)
# ---------------------------------------------------------------------------
TURTLE_COLORS: list[str] = [
    "white", "red", "green", "blue",
    "yellow", "cyan", "magenta", "orange",
]
"""Available colors for the turtle pen."""
