"""HandLang Phase 6 — End-to-End Vision Integration.

Live webcam feed extracting landmarks, predicting gestures, stabilizing
into tokens, parsing the stream, and drawing on the Tkinter canvas.
"""

import logging
import sys
from typing import List

import cv2
import numpy as np

import config
from language.interpreter import Interpreter, InterpreterError, StepLimitExceeded
from language.lexer import lex
from language.parser import ParseError, Parser
from language.semantic import check
from language.tokens import Token, TokenType
from runtime.canvas import TurtleCanvas
from vision.hand_tracker import HandTracker
from vision.stabilizer import TokenStabilizer

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
    )


def execute_program(lexed_tokens: List[Token], canvas: TurtleCanvas) -> str:
    """Attempt to parse and run the current lexed token stream. Returns error message if any."""
    print("\n--- Executing Program ---")
    
    try:
        parser = Parser(lexed_tokens)
        program = parser.parse()
    except ParseError as exc:
        msg = f"Parse error: {exc}"
        print(f"✗ {msg}")
        return msg

    print(f"AST: {program}")

    errors = check(program)
    if errors:
        msg = f"Semantic error: {errors[0]}"
        for err in errors:
            print(f"✗ Semantic error: {err}")
        return msg

    try:
        interp = Interpreter()
        commands = interp.execute(program)
    except StepLimitExceeded as exc:
        msg = f"Execution error: {exc}"
        print(f"✗ {msg}")
        return msg
    except InterpreterError as exc:
        msg = f"Runtime error: {exc}"
        print(f"✗ {msg}")
        return msg

    print(f"✓ Drawing {len(commands)} line segment(s)")
    if commands:
        canvas.render(commands)
    else:
        print("(nothing to draw)")
    return ""


def draw_hud(frame: cv2.Mat, gesture: str, conf: float, raw_stream: List[Token], lexed_stream: List[Token], error_msg: str, landmarks: np.ndarray) -> None:
    """Draw a highly structured, professional UI layout on the OpenCV frame."""
    h, w, _ = frame.shape
    overlay = frame.copy()

    # Layout Dimensions
    sidebar_w = 230     # Wider sidebar to fit all text
    bottom_h = 120

    # 1. Right Sidebar (Cheat Sheet)
    cv2.rectangle(overlay, (w - sidebar_w, 0), (w, h), (20, 20, 25), -1)

    # 2. Bottom Bar (Program Stream)
    cv2.rectangle(overlay, (0, h - bottom_h), (w - sidebar_w, h), (25, 25, 30), -1)

    # 3. Top-Left Pill (Active Gesture)
    cv2.rectangle(overlay, (10, 10), (340, 50), (30, 30, 35), -1)

    # Apply alpha blending for glassmorphism
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    # --- Draw 3D Hand Skeleton ---
    if landmarks is not None:
        HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index
            (5, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (9, 13), (13, 14), (14, 15), (15, 16),  # Ring
            (13, 17), (17, 18), (18, 19), (19, 20),  # Pinky
            (0, 17)  # Wrist to pinky base
        ]
        for p1, p2 in HAND_CONNECTIONS:
            x1, y1 = int(landmarks[p1][0] * w), int(landmarks[p1][1] * h)
            x2, y2 = int(landmarks[p2][0] * w), int(landmarks[p2][1] * h)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 65), 2)  # Hacker Green

        for lm in landmarks:
            cx, cy = int(lm[0] * w), int(lm[1] * h)
            cv2.circle(frame, (cx, cy), 4, (200, 255, 200), -1)

    # --- Draw Active Gesture ---
    color = (0, 255, 100) if conf >= config.STABILIZER_CONFIDENCE_THRESHOLD else (0, 0, 255)
    cv2.putText(frame, f"Active: {gesture}", (20, 37), cv2.FONT_HERSHEY_DUPLEX, 0.6, color, 1)

    # --- Draw Cheat Sheet (smaller font + tighter line spacing to fit everything) ---
    FONT      = cv2.FONT_HERSHEY_SIMPLEX
    FONT_HDR  = cv2.FONT_HERSHEY_DUPLEX
    FS        = 0.42       # item font scale
    LS        = 19         # line spacing in pixels
    X         = w - sidebar_w + 10

    cy = 22
    cv2.putText(frame, "LEFT HAND", (X, cy), FONT_HDR, 0.48, (255, 255, 255), 1)
    cy += 4
    left_lines = [
        ("Point ", "FWD",    (150, 255, 150)),
        ("Peace ", "TURN",   (150, 255, 150)),
        ("Palm  ", "REPEAT", (150, 255, 150)),
        ("Fist  ", "END",    (150, 255, 150)),
        ("Spider", "PEN",    (150, 255, 150)),
        ("ThumbU", "RUN",    (100, 255, 100)),
        ("ThumbD", "UNDO",   (100, 200, 255)),
        ("Pinch ", "COLOR",  (255, 200, 100)),
        ("Cross ", "INC",    (255, 150, 255)),
    ]
    for gesture_name, token_name, clr in left_lines:
        cy += LS
        cv2.putText(frame, f"{gesture_name}: {token_name}", (X, cy), FONT, FS, clr, 1)

    cy += LS + 4
    cv2.putText(frame, "RIGHT HAND", (X, cy), FONT_HDR, 0.48, (255, 255, 255), 1)
    right_lines = [
        ("Fist  ", "0 (digit)",   (150, 255, 255)),
        ("Point ", "1",           (150, 255, 255)),
        ("Peace ", "2",           (150, 255, 255)),
        ("Spider", "3",           (150, 255, 255)),
        ("ThumbU", "4",           (150, 255, 255)),
        ("Palm  ", "5",           (150, 255, 255)),
        ("ThumbD", "6",           (150, 255, 255)),
        ("Pinch ", "VAR",         (255, 200, 100)),
        ("Cross ", "INC",         (255, 150, 255)),
    ]
    for gesture_name, token_name, clr in right_lines:
        cy += LS
        if cy < h - 5:   # Don't draw past bottom of frame
            cv2.putText(frame, f"{gesture_name}: {token_name}", (X, cy), FONT, FS, clr, 1)

    # --- Draw Program Stream (bottom bar) ---
    avail_w = w - sidebar_w - 20
    # Approx chars that fit per line at font scale 0.45
    chars_per_line = int(avail_w / 10)

    # Raw stream: show only last 5 tokens
    raw_tail = raw_stream[-5:]
    raw_str = " > ".join([t.type.name for t in raw_tail])
    if len(raw_stream) > 5:
        raw_str = "... " + raw_str
    cv2.putText(frame, raw_str, (10, h - bottom_h + 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (160, 160, 160), 1)

    # Lexed stream: show only the LAST N tokens that fit in 2 lines
    lexed_tokens = [t for t in lexed_stream if t.type != TokenType.EOF]
    lexed_names = [
        f"{t.type.name}({t.value})" if t.value is not None else t.type.name
        for t in lexed_tokens
    ]

    # Build display from the END backwards to always show newest tokens
    line1, line2 = "", ""
    for name in reversed(lexed_names):
        candidate = name + (" " + line1 if line1 else "")
        if len(candidate) <= chars_per_line:
            line1 = candidate
        else:
            candidate2 = name + (" " + line2 if line2 else "")
            if not line2 and len(candidate2) <= chars_per_line:
                line2 = candidate2
                break
            else:
                break

    prefix = "..." if len(lexed_names) > len((line2 + " " + line1).split()) else ""
    if line2:
        cv2.putText(frame, prefix + line2, (10, h - bottom_h + 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 220, 0), 1)
        cv2.putText(frame, "    " + line1, (10, h - bottom_h + 72),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 220, 0), 1)
    else:
        cv2.putText(frame, prefix + line1, (10, h - bottom_h + 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 220, 0), 1)

    # Token count badge
    total = len(lexed_tokens)
    cv2.putText(frame, f"[{total} tokens]", (10, h - bottom_h + 98),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 120), 1)

    # --- Draw Critical Errors ---
    if error_msg:
        display_err = error_msg[:60] + ("..." if len(error_msg) > 60 else "")
        display_err += " (c=clear)"
        err_w = min(w - 20, len(display_err) * 10)
        cv2.rectangle(overlay,
                      (int(w/2) - int(err_w/2) - 10, int(h/2) - 30),
                      (int(w/2) + int(err_w/2) + 10, int(h/2) + 10),
                      (0, 0, 180), -1)
        cv2.addWeighted(overlay, 0.9, frame, 0.1, 0, frame)
        cv2.putText(frame, display_err,
                    (int(w/2) - int(err_w/2), int(h/2) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)


def main() -> None:
    setup_logging()

    print("=" * 60)
    print("  HandLang — Live Vision Integration (MediaPipe AI)")
    print("=" * 60)

    try:
        tracker = HandTracker()
    except Exception as e:
        print(f"✗ Failed to load MediaPipe GestureRecognizer: {e}")
        print("  Are you missing the gesture_recognizer.task model file in models/?")
        return

    print("  Model loaded! Starting camera...")

    stab = TokenStabilizer(config.STABILIZER_FRAMES_REQUIRED)
    canvas = TurtleCanvas()
    cap = cv2.VideoCapture(config.CAMERA_INDEX)

    raw_tokens: List[Token] = []
    lexed_tokens: List[Token] = []
    last_error = ""

    print("  Ready! Hold a gesture to type a token. Hold Thumb Up to RUN.")
    print("  Press ESC to exit.")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Flip the frame so it acts like a mirror
            frame = cv2.flip(frame, 1)
            display = frame.copy()

            # 1. Vision (Gesture AI)
            raw_gesture, conf, landmarks, handedness = tracker.process(frame)
            
            # Combine Handedness and Gesture Name
            gesture = f"{handedness}_{raw_gesture}" if raw_gesture != "NONE" else "NONE"

            if landmarks is not None:
                # Draw a dot on the wrist to show tracking is working
                wrist = landmarks[0]
                h, w, _ = display.shape
                cx, cy = int(wrist[0] * w), int(wrist[1] * h)
                cv2.circle(display, (cx, cy), 5, (255, 0, 255), -1)

            # 2. Stabilize
            new_token = stab.process_frame(gesture)
            
            # 3. Handle Token
            if new_token:
                last_error = ""
                raw_tokens.append(new_token)
                
                # Lex the stream to combine digits and apply UNDOs instantly
                lexed_tokens = lex(raw_tokens)
                
                # If they hit RUN, execute the lexed stream
                if new_token.type == TokenType.RUN:
                    last_error = execute_program(lexed_tokens, canvas)
                    # Clear streams after running if it succeeded!
                    if not last_error:
                        raw_tokens.clear()
                        lexed_tokens.clear()
                    else:
                        # Pop the RUN token so they can fix it
                        raw_tokens.pop()
                        lexed_tokens = lex(raw_tokens)

            # 4. Draw HUD and Canvas
            draw_hud(display, gesture, conf, raw_tokens, lexed_tokens, last_error, landmarks)
            cv2.imshow("HandLang Live", display)
            
            # Non-blocking canvas update
            try:
                canvas.root.update_idletasks()
                canvas.root.update()
            except Exception:
                # Thrown if user closes the Tkinter window manually
                break

            key = cv2.waitKey(1)
            if key == 27:  # ESC
                break
            elif key == ord('c'):
                last_error = ""
                raw_tokens.clear()
                lexed_tokens.clear()

    finally:
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()
        try:
            canvas.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
