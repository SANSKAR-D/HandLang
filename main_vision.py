"""HandLang Phase 6 — End-to-End Vision Integration.

Live webcam feed extracting landmarks, predicting gestures, stabilizing
into tokens, parsing the stream, and drawing on the Tkinter canvas.
"""

import logging
import sys
from typing import List

import cv2

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


def draw_hud(frame: cv2.Mat, gesture: str, conf: float, raw_stream: List[Token], lexed_stream: List[Token], error_msg: str) -> None:
    """Draw the heads-up display on the OpenCV frame."""
    # Active gesture
    color = (0, 255, 0) if conf >= config.STABILIZER_CONFIDENCE_THRESHOLD else (0, 0, 255)
    cv2.putText(frame, f"Gesture: {gesture} ({conf:.2f})", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                
    # Raw stream
    raw_str = " ".join([t.type.name for t in raw_stream[-6:]])  # Show last 6
    if len(raw_stream) > 6: raw_str = "... " + raw_str
    cv2.putText(frame, f"Raw: {raw_str}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    # Lexed stream (what the parser actually sees) - Wrapped across lines!
    lexed_names = [
        f"{t.type.name}({t.value})" if t.value is not None else t.type.name
        for t in lexed_stream if t.type != TokenType.EOF
    ]
    
    max_chars_per_line = 40
    y_offset = 110
    current_line = "Prog: "
    
    for name in lexed_names:
        if len(current_line) + len(name) + 1 > max_chars_per_line:
            cv2.putText(frame, current_line, (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            y_offset += 30
            current_line = "      " + name
        else:
            current_line += " " + name if current_line != "Prog: " else name
            
    cv2.putText(frame, current_line, (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
    if error_msg:
        cv2.putText(frame, error_msg, (10, y_offset + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


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
            draw_hud(display, gesture, conf, raw_tokens, lexed_tokens, last_error)
            cv2.imshow("HandLang Live", display)
            
            # Non-blocking canvas update
            try:
                canvas.root.update_idletasks()
                canvas.root.update()
            except Exception:
                # Thrown if user closes the Tkinter window manually
                break

            if cv2.waitKey(1) == 27:  # ESC
                break

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
