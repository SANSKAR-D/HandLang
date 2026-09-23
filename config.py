"""GazeCursor – all tunable constants.

Every magic number lives here.  Modules import from config instead of
hard-coding values.  Grouped by subsystem; later phases append sections.
"""

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
CAMERA_INDEX: int = 0
"""Default video-capture device index (0 = first webcam)."""

FPS_TEST_FRAME_COUNT: int = 300
"""Number of raw frames grabbed when measuring baseline FPS (Phase 0)."""

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = "INFO"
"""Root logger level.  Set to 'DEBUG' for verbose diagnostics."""

LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
"""Format string for log messages."""

# ---------------------------------------------------------------------------
# MediaPipe Face Mesh
# ---------------------------------------------------------------------------
FACE_MESH_MAX_FACES: int = 1
"""Maximum number of faces to detect."""

FACE_MESH_REFINE_LANDMARKS: bool = True
"""Must be True to output the 468-477 iris landmarks."""

FACE_MESH_MIN_DETECTION_CONFIDENCE: float = 0.5
"""Minimum confidence value ([0.0, 1.0]) for face detection to be considered successful."""

FACE_MESH_MIN_TRACKING_CONFIDENCE: float = 0.5
"""Minimum confidence value ([0.0, 1.0]) for face tracking to be considered successful."""

# ---------------------------------------------------------------------------
# UI / Overlay
# ---------------------------------------------------------------------------
COLOR_EYE_CONTOUR: tuple[int, int, int] = (0, 255, 0)
"""Color for drawing eye contours (BGR)."""

COLOR_IRIS: tuple[int, int, int] = (0, 0, 255)
"""Color for drawing iris centers (BGR)."""

COLOR_TEXT: tuple[int, int, int] = (255, 255, 255)
"""Color for overlay text (BGR)."""

COLOR_WARNING: tuple[int, int, int] = (0, 0, 255)
"""Color for warning text like 'No face detected' (BGR)."""

# ---------------------------------------------------------------------------
# Blink and Features
# ---------------------------------------------------------------------------
BASELINE_DURATION_SECONDS: float = 3.0
"""How long to collect EAR data to establish the user's baseline."""

EAR_CLOSE_THRESHOLD_RATIO: float = 0.70
"""Multiplier on baseline EAR. If EAR drops below this, eye is closing."""

EAR_OPEN_THRESHOLD_RATIO: float = 0.80
"""Multiplier on baseline EAR. If EAR rises above this, eye is opening."""

BLINK_MIN_DELIBERATE_DURATION: float = 0.25
"""Minimum seconds for a blink to be considered deliberate (vs natural)."""

BLINK_MAX_DELIBERATE_DURATION: float = 0.80
"""Maximum seconds for a blink to be considered deliberate."""

DOUBLE_BLINK_TIMEOUT: float = 1.0
"""Seconds to wait after a deliberate blink for a second one (for right click)."""


