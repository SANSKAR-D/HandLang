"""GazeCursor – main entry point.

Phase 2 deliverable: Console/overlay logging of features and blink events. No cursor control yet.
"""

import logging
import sys
import time

import cv2

import config
from capture.camera import Camera
from ui import overlay
from vision.face_mesh import FaceMeshWrapper
from vision import features
from vision.blink import BlinkStateMachine


def setup_logging() -> None:
    """Configure the root logger from :mod:`config` constants."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
    )


def run_app() -> None:
    """Run the main application loop."""
    logger = logging.getLogger(__name__)

    try:
        camera = Camera().start()
    except RuntimeError as exc:
        logger.error("Failed to start camera: %s", exc)
        sys.exit(1)

    face_mesh = FaceMeshWrapper()

    # Wait for the first frame
    frame = None
    logger.info("Waiting for first camera frame...")
    for _ in range(50):
        frame = camera.read()
        if frame is not None:
            break
        time.sleep(0.1)

    if frame is None:
        logger.error("Timeout waiting for first frame")
        camera.stop()
        sys.exit(1)

    window_name = "GazeCursor"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    logger.info("Starting main loop. Press 'q' or close the window to exit.")

    frame_count = 0
    start_time = time.perf_counter()
    fps = 0.0
    
    # Baselining state
    is_baselining = True
    baseline_start_time = time.perf_counter()
    baseline_ears = []
    
    # State machine and events
    blink_sm = None
    recent_events = []

    try:
        while True:
            current_time = time.perf_counter()
            
            # Clean up old events
            recent_events = [(e, t) for e, t in recent_events if current_time - t < 2.0]

            # 1. Capture
            frame = camera.read()
            if frame is None:
                time.sleep(0.01)
                continue

            # 2. Process Landmarks
            landmarks = face_mesh.process(frame)

            # 3. Features & Logic
            if landmarks is not None:
                overlay.draw_landmarks(frame, landmarks)
                
                ear_l, ear_r = features.get_both_ear(landmarks)
                avg_ear = (ear_l + ear_r) / 2.0
                
                ratio_l = features.compute_iris_ratio(landmarks, features.LEFT_EYE, features.LEFT_IRIS)
                ratio_r = features.compute_iris_ratio(landmarks, features.RIGHT_EYE, features.RIGHT_IRIS)
                
                if is_baselining:
                    baseline_ears.append(avg_ear)
                    elapsed = current_time - baseline_start_time
                    progress = min(1.0, elapsed / config.BASELINE_DURATION_SECONDS)
                    overlay.draw_baseline_progress(frame, progress)
                    
                    if elapsed >= config.BASELINE_DURATION_SECONDS:
                        if len(baseline_ears) > 10:
                            baseline_val = sum(baseline_ears) / len(baseline_ears)
                            logger.info("Baseline calibration complete. EAR baseline: %.3f", baseline_val)
                            blink_sm = BlinkStateMachine(baseline_val)
                            is_baselining = False
                        else:
                            # Not enough data (e.g. face lost)
                            baseline_start_time = current_time
                            baseline_ears.clear()
                            logger.warning("Calibration failed: not enough face frames. Retrying...")
                else:
                    # Normal running mode
                    overlay.draw_features(frame, avg_ear, ratio_l, ratio_r)
                    
                    new_events = blink_sm.update(avg_ear, current_time)
                    for ev in new_events:
                        recent_events.append((ev, current_time))
                        print(f"[{current_time:.2f}] EVENT: {ev} | Ratios: L({ratio_l[0]:.2f}, {ratio_l[1]:.2f}) R({ratio_r[0]:.2f}, {ratio_r[1]:.2f})")
            else:
                if is_baselining:
                    # Reset baseline if face is lost
                    baseline_start_time = current_time
                    baseline_ears.clear()

            # Calculate rolling FPS every 10 frames
            frame_count += 1
            if frame_count % 10 == 0:
                elapsed = time.perf_counter() - start_time
                fps = 10 / max(elapsed, 0.001)
                start_time = time.perf_counter()

            overlay.draw_status(frame, fps, face_detected=(landmarks is not None))
            overlay.draw_events(frame, recent_events, current_time)

            # 4. Display
            cv2.imshow(window_name, frame)

            # 5. Events / Exit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            
            # Check if window was closed via the 'X' button
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.exception("Unexpected error in main loop")
    finally:
        logger.info("Shutting down...")
        camera.stop()
        face_mesh.close()
        cv2.destroyAllWindows()


def main() -> None:
    """Entry point for GazeCursor."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("GazeCursor starting (Phase 2)")
    run_app()
    logger.info("Phase 2 exit complete")


if __name__ == "__main__":
    main()
