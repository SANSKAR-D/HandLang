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
    sidebar_w = 200
    bottom_h = 130
    
    # 1. Right Sidebar (Cheat Sheet)
    cv2.rectangle(overlay, (w - sidebar_w, 0), (w, h), (20, 20, 25), -1)
    
    # 2. Bottom Bar (Program Stream)
    cv2.rectangle(overlay, (0, h - bottom_h), (w - sidebar_w, h), (25, 25, 30), -1)
    
    # 3. Top-Left Pill (Active Gesture)
    cv2.rectangle(overlay, (10, 10), (320, 50), (30, 30, 35), -1)
    
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

    # --- Draw Cheat Sheet ---
    cv2.putText(frame, "LEFT HAND", (w - sidebar_w + 15, 30), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1)
    left_lines = [
        "Point : FWD",
        "Peace : TURN",
        "Palm  : REPEAT",
        "Fist  : END",
        "Spider: PEN",
        "ThumbU: RUN",
        "ThumbD: UNDO"
    ]
    cy = 55
    for text in left_lines:
        cv2.putText(frame, text, (w - sidebar_w + 15, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 255, 150), 1)
        cy += 25
        
    cv2.putText(frame, "RIGHT HAND", (w - sidebar_w + 15, cy + 15), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1)
    cy += 45
    right_lines = [
        "Fist  : 0",
        "Point : 1",
        "Peace : 2",
        "Spider: 3",
        "ThumbU: 4",
        "Palm  : 5",
        "ThumbD: 6"
    ]
    for text in right_lines:
        cv2.putText(frame, text, (w - sidebar_w + 15, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 255, 255), 1)
        cy += 25

    # --- Draw Program Stream ---
    # Safe character limit for the bottom bar (approx 13px per char)
    max_chars_per_line = int((w - sidebar_w - 30) / 13) 

    # Raw stream (Truncate to prevent overlap)
    raw_str = " > ".join([t.type.name for t in raw_stream[-6:]])
    if len(raw_stream) > 6: 
        raw_str = "... " + raw_str
        
    full_raw_text = f"Raw: {raw_str}"
    if len(full_raw_text) > max_chars_per_line:
        # Keep only the end of the raw stream so we see the newest tokens
        full_raw_text = "Raw: ..." + full_raw_text[-(max_chars_per_line - 10):]
        
    cv2.putText(frame, full_raw_text, (15, h - bottom_h + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    # Lexed Stream (Wrapped dynamically based on available width)
    lexed_names = [
        f"{t.type.name}({t.value})" if t.value is not None else t.type.name
        for t in lexed_stream if t.type != TokenType.EOF
    ]
    
    y_offset = h - bottom_h + 55
    current_line = "AST: "
    for name in lexed_names:
        if len(current_line) + len(name) + 1 > max_chars_per_line:
            cv2.putText(frame, current_line, (15, y_offset), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 220, 0), 1)
            y_offset += 25
            current_line = "     " + name
        else:
            current_line += " " + name if current_line != "AST: " else name
            
    cv2.putText(frame, current_line, (15, y_offset), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 220, 0), 1)
    
    # --- Draw Critical Errors ---
    if error_msg:
        # Truncate error message if it's too long
        display_err = error_msg
        if len(display_err) > 60:
            display_err = display_err[:57] + "..."
        display_err += " (Press 'c' or UNDO to clear)"
            
        err_w = min(w - 20, len(display_err) * 11)
        cv2.rectangle(overlay, (int(w/2) - int(err_w/2) - 10, int(h/2) - 30), (int(w/2) + int(err_w/2) + 10, int(h/2) + 10), (0, 0, 200), -1)
        # Re-apply blending just for the error box so it pops
        cv2.addWeighted(overlay, 0.9, frame, 0.1, 0, frame)
        cv2.putText(frame, display_err, (int(w/2) - int(err_w/2), int(h/2) - 5), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)


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
