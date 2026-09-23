# GazeCursor: Product Requirements Document

**Version:** 1.0
**Owner:** Sanskar
**Status:** Draft, ready for Phase 0

---

## 1. Overview

| Field | Detail |
|---|---|
| Product | GazeCursor: webcam-only gaze-controlled mouse with blink clicking |
| Platform | Windows / Linux / macOS desktop, Python 3.10+ |
| Timeline | ~3 weeks, 8 phases (Phase 0 to Phase 7) |
| Hardware | Standard laptop webcam (720p, ~30 FPS). No dedicated eye tracker. |

### 1.1 Problem statement

People who cannot use their hands (motor impairments, injuries) have limited access to computers, and dedicated eye trackers cost hundreds to thousands of dollars. A calibrated webcam solution can provide basic pointing and clicking at zero extra hardware cost.

### 1.2 Goals

1. Move the cursor by gaze with usable accuracy on large UI targets.
2. Click via deliberate blinks without triggering on natural blinks.
3. Run in real time on commodity hardware.
4. Produce measurable, reportable results (accuracy, latency, false-click rate).

### 1.3 Non-goals (v1)

- Eye-tracker-grade accuracy (sub-degree).
- Multi-monitor support.
- Mobile or tablet support.
- Reliable operation in very dark rooms or with heavily tinted glasses.

### 1.4 Target users

- **Primary:** users with limited hand mobility.
- **Secondary:** hands-free desktop use; recruiters and reviewers evaluating the project as a portfolio piece.

---

## 2. Success Metrics

| Metric | Target | Stretch |
|---|---|---|
| Mean gaze error after calibration | <= 150 px on 1920x1080 | <= 100 px |
| End-to-end latency (frame to cursor) | <= 80 ms | <= 50 ms |
| Frame rate | >= 25 FPS | >= 30 FPS |
| Deliberate-blink detection rate | >= 90% | >= 95% |
| False clicks from natural blinking | <= 1 per minute | <= 0.5 per minute |
| Calibration time | <= 60 s | <= 40 s |

These are targets, not promises. Measure real values and report them honestly, including misses.

---

## 3. Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-1 | Capture webcam frames on a dedicated thread | Must | 1 |
| FR-2 | Detect face and iris landmarks each frame | Must | 1 |
| FR-3 | Compute normalized iris position and Eye Aspect Ratio (EAR) | Must | 2 |
| FR-4 | Classify blinks by duration (natural / deliberate / double) | Must | 2 |
| FR-5 | Run a 9-point calibration and fit a regression model | Must | 3 |
| FR-6 | Map features to screen coordinates in real time | Must | 4 |
| FR-7 | Smooth output with a One Euro filter | Must | 4 |
| FR-8 | Move the OS cursor and issue left/right clicks | Must | 4, 5 |
| FR-9 | Freeze the cursor while a blink is in progress | Must | 5 |
| FR-10 | Include head-pose features in the model | Should | 5 |
| FR-11 | Dwell-click mode | Should | 5 |
| FR-12 | Save and load per-user calibration profiles | Should | 3 |
| FR-13 | Debug overlay (landmarks, FPS, gaze point) | Should | 1 |
| FR-14 | Hotkeys to pause/resume, kill, and recalibrate | Must | 4 |
| FR-15 | On-screen keyboard | Could | Stretch |

---

## 4. Non-Functional Requirements

- **Performance:** total processing per frame under 35 ms.
- **Safety:** an always-available kill hotkey (default `Ctrl+Shift+Q`) and a pause key (default `Esc`), implemented BEFORE any cursor movement is enabled, so a bad calibration can never trap the user without mouse control.
- **Privacy:** no video stored or transmitted. All processing is local.
- **Robustness:** when no face is detected, hold the last cursor position; never jump.
- **Maintainability:** modular structure, type hints, docstrings, unit tests for all pure logic.
- **Reproducibility:** pinned dependency versions; deterministic evaluation scripts.

---

## 5. System Architecture

```
Webcam -> [Capture thread] -> Face Mesh -> Feature extraction
                                                |
                      +-------------------------+
                      v                         v
              Blink state machine       Calibrated regression
                      |                         |
                      |                  One Euro filter
                      v                         v
                Click events -------> Cursor controller (OS)
```

### 5.1 Module layout

```
gazecursor/
├── main.py
├── config.py                # all tunable constants in one place
├── capture/
│   └── camera.py            # threaded webcam reader
├── vision/
│   ├── face_mesh.py         # MediaPipe wrapper
│   ├── features.py          # iris ratios, head pose, EAR
│   └── blink.py             # blink state machine
├── gaze/
│   ├── calibration.py       # 9-point wizard + data collection
│   ├── model.py             # regression fit / predict / save / load
│   └── filters.py           # One Euro filter
├── control/
│   ├── cursor.py            # OS mouse control + clamping
│   ├── hotkeys.py           # kill / pause / recalibrate
│   └── dwell.py             # dwell-click logic
├── ui/
│   ├── overlay.py           # OpenCV debug drawing
│   └── calib_screen.py      # fullscreen calibration dots
├── evaluation/
│   └── accuracy_test.py     # pixel-error benchmark + ablation
├── tests/                   # pytest suite
├── models/                  # saved per-user calibrations
├── results/                 # benchmark CSVs and plots
├── docs/
│   ├── PRD.md
│   ├── TESTPLAN.md
│   └── PROMPT.md
├── requirements.txt
└── README.md
```

### 5.2 Key technical decisions

| Decision | Choice | Reason |
|---|---|---|
| Landmark source | MediaPipe Face Mesh, `refine_landmarks=True` | Provides iris landmarks (indices 468-477) |
| Gaze features | Iris position normalized by eye corners and eyelids, plus head yaw/pitch | Distance-invariant; head pose corrects for head movement |
| Regression | Polynomial (degree 2) + Ridge via scikit-learn | Captures curved eye-angle to screen mapping; compare against linear |
| Smoothing | One Euro Filter | Adaptive: steady when still, responsive when moving |
| Blink detection | EAR with per-user baseline and duration state machine | Simple, robust, explainable |
| Click timing | Latch gaze from ~150 ms before blink onset | Prevents cursor jump when the eye closes |
| Cursor control | `pynput` (or `pyautogui` fallback) | Cross-platform |

---

## 4. Phased Delivery Plan

Each phase has a goal, tasks, a deliverable, and a **test gate** defined in `TESTPLAN.md`. A phase is complete only when its gate passes.

### Phase 0: Setup and Environment
**Goal:** Reproducible project skeleton.
**Tasks:** repo and venv, `requirements.txt` (pinned), folder structure, `.gitignore`, logging config, `config.py`, README stub, webcam access check.
**Deliverable:** `python main.py` prints webcam resolution and measured FPS.

### Phase 1: Capture and Perception
**Goal:** Reliable face, eye, and iris landmarks in real time.
**Tasks:** threaded `Camera` class (latest-frame buffer, drops stale frames); MediaPipe Face Mesh wrapper with `refine_landmarks=True`; overlay drawing eye contours and iris centers; graceful no-face handling.
**Deliverable:** live window showing landmarks and FPS.

### Phase 2: Feature Extraction and Blink Detection
**Goal:** Turn landmarks into stable numeric features and detect clicks.
**Tasks:** normalized iris ratios per eye; EAR for both eyes; 3-second per-user open-eye baseline; blink state machine (OPEN, CLOSING, CLOSED, OPENING) with duration classification (natural < 0.25 s, deliberate 0.4-0.8 s, double = two deliberate within 1 s); debug logging of features and events.
**Deliverable:** console/overlay logging of features and blink events. No cursor control yet.

### Phase 3: Calibration and Gaze Model
**Goal:** Learn the mapping from eye features to screen coordinates.
**Tasks:** fullscreen 9-point calibration UI (dot, short settle delay, ~30 samples, outlier rejection); 4 held-out validation points; `GazeModel` with linear and polynomial-ridge variants; save/load per user via joblib; error in pixels and degrees of visual angle.
**Deliverable:** calibration script producing a saved model and an error report.

### Phase 4: Real-Time Cursor Control
**Goal:** Live gaze-driven cursor movement with smoothing.
**Tasks:** implement hotkeys (kill, pause) FIRST; One Euro filter with tunable parameters; fixation snap / deadzone; connect model to OS cursor with screen-bounds clamping; hold last position on no-face.
**Deliverable:** cursor follows gaze in real time; hotkeys verified.

### Phase 5: Click Integration and Robustness
**Goal:** Reliable clicking on top of live cursor control, plus head-pose handling.
**Tasks:** blink to left click, double-blink to right click; cursor latching and freeze during blink; head-pose features via `cv2.solvePnP` added to the model (recalibrate); dwell-click mode with progress ring; click cooldown.
**Deliverable:** full hands-free pointing and clicking.

### Phase 6: Evaluation and Ablation
**Goal:** Produce the numbers and tables for the README and resume.
**Tasks:** `accuracy_test.py` (20 random targets, predicted vs true); ablation across four configurations (linear; + polynomial ridge; + head pose; + One Euro filter); measure FPS, latency, click accuracy, false clicks per minute; run at least 3 users or 3 sessions with different lighting.
**Deliverable:** `results/` folder with CSVs, plots, summary table.

### Phase 7: Packaging, Docs, and Demo
**Goal:** Presentable and easy for a stranger to run.
**Tasks:** README (overview, demo GIF, install, usage, calibration guide, results, limitations, future work); type hints, docstrings, lint clean; 60-90 second demo video.
**Deliverable:** public-ready repository.

---

## 5. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Accuracy too low for usability | Medium | High | Snap-to-target or zoom-on-dwell; demo with large targets |
| Lighting sensitivity | High | Medium | Document conditions; startup brightness warning |
| Glasses reflections | Medium | Medium | Document as limitation; test with and without |
| Cursor trap from bad calibration | Medium | High | Kill/pause hotkeys built before movement (Phase 4) |
| Calibration drift over time | High | Medium | Quick recalibration hotkey; optional click-based correction |
| Latency creep | Medium | Medium | Profile each stage; keep capture threaded |

---

## 6. Known Limitations (to state in README)

Webcam gaze tracking is not eye-tracker grade. Expect roughly 2-4 degrees of visual angle error: enough for large buttons, tabs, and menu items, but not small links. Lighting, glasses, and camera position all affect results.

---

## 7. Definition of Done

- All phase test gates passed, or exceptions documented with reasons.
- Section 2 metrics measured and reported, met or not met.
- Public repo with README, demo video, results table, and limitations.
- A stranger can install and use it by following the README alone.

---

## 8. Stretch Goals (post v1)

- On-screen keyboard with dwell typing and word prediction.
- Silent recalibration: use click locations to correct drift automatically.
- Web dashboard (React + FastAPI) showing session gaze heatmaps.
- Snap-to-UI-element mode using accessibility APIs.
