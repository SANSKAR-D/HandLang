# GazeCursor: Test Plan

**Companion to:** `PRD.md`
**Rule:** A phase is complete ONLY when every **Must** test in its gate passes. Do not start the next phase until then.

---

## How to use this document

1. After the AI finishes a phase, run the **Automated tests** with `pytest`.
2. Then perform each **Manual test** yourself and record the result in the **Test Log** at the bottom.
3. If any Must test fails, paste the failing test ID and your observation back to the AI and ask it to fix that phase. Do not move on.
4. When the whole gate is green, start the next phase.

**Legend:** `[A]` = automated (pytest), `[M]` = manual (you do it), `Must` = required to pass, `Should` = record result but does not block.

---

## Phase 0: Setup and Environment

| ID | Type | Test | Method | Pass criteria | Level |
|---|---|---|---|---|---|
| T0.1 | M | Fresh install | New venv, `pip install -r requirements.txt` | Installs with no errors | Must |
| T0.2 | M | Camera opens | Run `python main.py` | Prints resolution; 100 frames grabbed, no exceptions | Must |
| T0.3 | A | Test runner works | `pytest` | Exits with code 0 | Must |
| T0.4 | M | Baseline FPS | Time 300 raw frame reads | >= 25 FPS printed | Must |
| T0.5 | M | Folder structure | Compare against PRD section 5.1 | All folders and `__init__.py` files present | Should |

---

## Phase 1: Capture and Perception

| ID | Type | Test | Method | Pass criteria | Level |
|---|---|---|---|---|---|
| T1.1 | A | Landmark count | Unit test: run wrapper on a saved sample face image | 478 landmarks returned, all x,y in [0,1] | Must |
| T1.2 | A | No-face handling | Unit test: run wrapper on a blank/noise image | Returns a "no face" result, no exception | Must |
| T1.3 | M | No-face live | Cover the camera for 10 s, then uncover | No crash; overlay shows "no face"; tracking resumes | Must |
| T1.4 | A | Threaded capture returns latest | Unit test with a fake slow consumer | Consumer always receives the newest frame, never a queue backlog | Must |
| T1.5 | M | Throughput | Run live for 60 s with landmarks and overlay on | Average FPS >= 25 | Must |
| T1.6 | M | Lighting sanity | Test in bright, normal, and dim light | Tracked properly in at least 2 of 3 | Should |
| T1.7 | M | Clean shutdown | Press `q` or close the window | Camera released, process exits, no hanging thread | Must |

---

## Phase 2: Feature Extraction and Blink Detection

| ID | Type | Test | Method | Pass criteria | Level |
|---|---|---|---|---|---|
| T2.1 | A | EAR math | Synthetic landmarks: open eye vs flat eye | Open EAR > 0.25; closed EAR < 0.10 | Must |
| T2.2 | A | Iris ratio bounds | Synthetic eye geometry, iris at left/center/right/up/down | Ratios in [0,1]; center is approx 0.5; left < center < right | Must |
| T2.3 | A | State machine: natural | Scripted EAR sequence with a 0.15 s dip | Classified as natural; no click | Must |
| T2.4 | A | State machine: deliberate | Scripted EAR sequence with a 0.5 s dip | Classified as deliberate; one left-click event | Must |
| T2.5 | A | State machine: double | Two 0.5 s dips within 1 s | One right-click event; no extra left click | Must |
| T2.6 | A | State machine: jitter | EAR oscillating near threshold | No spurious events (hysteresis works) | Must |
| T2.7 | M | Baseline calibration | Run the 3 s baseline with eyes open | Baseline EAR printed and sensible (approx 0.2-0.4) | Must |
| T2.8 | M | Deliberate detection | 30 intentional blinks (about 0.5 s each) | >= 27/30 detected | Must |
| T2.9 | M | Natural blink rejection | Read a page normally for 2 minutes | <= 2 false click events logged | Must |
| T2.10 | M | Feature stability | Stare at a fixed point for 10 s | Iris ratio std-dev below 0.02 (record actual value) | Should |
| T2.11 | M | Gaze direction sanity | Look far left, right, up, down | Printed ratios move in the expected direction each time | Must |

---

## Phase 3: Calibration and Gaze Model

| ID | Type | Test | Method | Pass criteria | Level |
|---|---|---|---|---|---|
| T3.1 | A | Regression sanity (linear) | Synthetic data with a known linear map | Recovers map, error near 0 | Must |
| T3.2 | A | Regression sanity (poly) | Synthetic data with a known quadratic map | Poly model error < linear model error | Must |
| T3.3 | A | Outlier rejection | Inject 10% garbage samples into a point's data | Median/outlier filter removes them; result within tolerance | Must |
| T3.4 | A | Persistence | Fit, save, reload, predict | Predictions identical before and after reload | Must |
| T3.5 | A | Pixel-to-degree conversion | Known screen size, distance, resolution | Matches hand-computed value within 1% | Should |
| T3.6 | M | Sample quality | Run calibration; inspect log | >= 25 valid samples per dot after rejection | Must |
| T3.7 | M | Held-out accuracy | Evaluate on the 4 validation dots | Mean error <= 200 px (must) / <= 150 px (target) | Must |
| T3.8 | M | Model comparison | Fit linear and polynomial on the same data | Comparison table printed; record which wins | Must |
| T3.9 | M | Repeatability | Calibrate 3 times in a row | Mean error varies by < 30% across runs | Should |
| T3.10 | M | Calibration time | Time the wizard | <= 60 s | Should |
| T3.11 | M | Escape works | Press `Esc` mid-calibration | Calibration aborts cleanly, no crash, no saved bad model | Must |

---

## Phase 4: Real-Time Cursor Control

| ID | Type | Test | Method | Pass criteria | Level |
|---|---|---|---|---|---|
| T4.1 | A | Filter noise reduction | Feed noisy constant signal to One Euro filter | Output variance reduced by >= 70% | Must |
| T4.2 | A | Filter responsiveness | Feed a step change | Output reaches 90% of step within 200 ms (at 30 FPS) | Must |
| T4.3 | A | Clamping | Feed out-of-range predictions | Output always within [0, W-1] x [0, H-1] | Must |
| T4.4 | A | No-face hold | Feed a no-face sequence | Cursor target holds last value, no jump | Must |
| T4.5 | M | Kill switch | Press kill hotkey during movement, 10 times | Control stops within 100 ms, 10/10 | Must |
| T4.6 | M | Pause/resume | Press pause, look around, resume | Cursor frozen while paused; resumes correctly | Must |
| T4.7 | M | Hotkeys work first | Start app with a deliberately bad/no model | Hotkeys still work; mouse never trapped | Must |
| T4.8 | M | Screen bounds | Look at all four corners | Cursor stays on screen, no crash | Must |
| T4.9 | M | Jitter | Fixate a target for 10 s | Cursor drift within 40 px radius | Should |
| T4.10 | M | Latency | Measure camera-to-cursor delay (timestamp log or slow-mo phone video) | <= 80 ms (record actual) | Should |
| T4.11 | M | Target acquisition | Reach 5 large buttons (>= 150 px) | >= 4/5 reached within 3 s each | Must |

---

## Phase 5: Click Integration and Robustness

| ID | Type | Test | Method | Pass criteria | Level |
|---|---|---|---|---|---|
| T5.1 | A | Latch logic | Simulate gaze history, then a blink onset | Click position equals gaze from ~150 ms before onset | Must |
| T5.2 | A | Cooldown | Fire two clicks 100 ms apart | Second is suppressed | Must |
| T5.3 | A | Dwell logic | Simulate gaze held in radius for 1 s, then moving out | Click fires at 1 s; resets if gaze leaves the radius | Must |
| T5.4 | A | Freeze during blink | Simulate EAR dropping mid-movement | Cursor output constant while eye is closing/closed | Must |
| T5.5 | M | Click accuracy | 20 button clicks by blink | >= 18/20 land on the intended button | Must |
| T5.6 | M | Latch offset | Blink while looking at a button | Click lands within 60 px of target in >= 90% of trials | Must |
| T5.7 | M | Right click | 10 double-blinks | >= 8/10 register as right click; no stray left clicks | Must |
| T5.8 | M | Head-pose gain | Move head about +/-10 degrees; measure error with and without pose features | Error with pose lower; record the difference | Must |
| T5.9 | M | Dwell mode | 10 dwell clicks on large targets | >= 9/10 succeed | Should |
| T5.10 | M | Dwell false positives | 60 s of reading with dwell on | <= 1 accidental click | Should |
| T5.11 | M | Natural use | 5-minute task: open browser, click 5 links, close a tab, no mouse | Completed hands-free | Must |
| T5.12 | M | False clicks | 5 minutes of normal viewing | <= 5 unintended clicks (<= 1/min) | Must |

---

## Phase 6: Evaluation and Ablation

| ID | Type | Test | Method | Pass criteria | Level |
|---|---|---|---|---|---|
| T6.1 | A | Reproducibility | Run benchmark script twice on saved data | Identical numbers | Must |
| T6.2 | A | Metric functions | Unit tests for mean/median error and jitter on known arrays | Match hand calculations | Must |
| T6.3 | M | Ablation completeness | Inspect results table | All 4 configurations filled, no empty cells | Must |
| T6.4 | M | Multi-session | At least 3 sessions (different people or lighting) | Mean and spread reported | Must |
| T6.5 | M | Targets check | Compare against PRD section 2 | Each metric marked met / not met, with reasons for misses | Must |
| T6.6 | M | Plots | Open generated plots | Axes labeled, units shown, readable | Should |

---

## Phase 7: Packaging, Docs, and Demo

| ID | Type | Test | Method | Pass criteria | Level |
|---|---|---|---|---|---|
| T7.1 | M | Clean install | Fresh venv, follow README exactly | Works end to end, no undocumented steps | Must |
| T7.2 | A | Full test suite | `pytest` | All pass | Must |
| T7.3 | A | Lint | `ruff check .` | No errors | Must |
| T7.4 | M | Peer test | A friend installs and calibrates without your help | Working cursor in under 10 minutes | Should |
| T7.5 | M | Demo review | Watch the video cold | Shows calibration, navigation, click, results clearly | Must |
| T7.6 | M | README completeness | Check for overview, GIF, install, usage, results, limitations | All sections present | Must |

---

## Test Log

Copy one block per phase attempt. Keep the failures; they show real engineering process.

```
Phase: __        Attempt: __        Date: __
Automated: pytest result (paste summary) __

Test ID | Result (Pass/Fail) | Measured value | Notes
--------|--------------------|----------------|------
T_._    |                    |                |
T_._    |                    |                |

Gate status: PASS / FAIL
Failing tests to fix: __
```

---

## Results Summary (fill in during Phase 6)

| Metric | Target | Measured | Met? |
|---|---|---|---|
| Mean gaze error (px) | <= 150 | | |
| Latency (ms) | <= 80 | | |
| FPS | >= 25 | | |
| Deliberate-blink detection | >= 90% | | |
| False clicks / min | <= 1 | | |
| Calibration time (s) | <= 60 | | |

### Ablation table

| Configuration | Mean error (px) | Median (px) | Jitter (px) |
|---|---|---|---|
| Iris ratio + linear | | | |
| + polynomial ridge | | | |
| + head pose | | | |
| + One Euro filter | | | |
