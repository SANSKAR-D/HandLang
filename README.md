# HandLang: Code with your Hands! 🖐️💻

**HandLang** is a fully functional, esoteric visual programming language that you write entirely by waving your hands in front of your webcam! 

Powered by Google's incredibly robust **MediaPipe Gesture AI**, HandLang maps your physical hand shapes to programming constructs in real-time. It features a complete custom compiler (Lexer, Parser, Semantic Analyzer, and Interpreter) that converts your gestures into an Abstract Syntax Tree (AST) and executes them to draw beautiful geometric art on a Turtle canvas.

---

## 🚀 Features
- **No Keyboard Required:** Write loops, variable logic, and drawing commands entirely through hand gestures.
- **Robust AI Vision:** Uses a highly optimized Deep Learning Convolutional Neural Network (MediaPipe Tasks API) trained on millions of hands for zero-jitter, 100% collision-free gesture recognition.
- **Full Custom Compiler Stack:** 
  - **Lexer:** Combines digit gestures into multi-digit numbers on the fly and immediately resolves `UNDO` commands.
  - **Parser:** Builds an Abstract Syntax Tree enforcing HandLang grammar.
  - **Semantic Checker:** Validates variable assignments and scope.
  - **Interpreter:** Executes the AST and renders commands to a Tkinter Turtle window.
- **Heads-Up Display (HUD):** A beautifully wrapped multi-line live view of your gesture stream right on your webcam feed, complete with real-time error messages (e.g., "Parse error: Expected a number").

---

## 🛠️ Installation

1. Make sure you have `uv` (the fast Python package manager) installed.
2. Clone this repository.
3. Install dependencies:
   ```bash
   uv sync
   ```
4. **Download the AI Model**: You must download the MediaPipe gesture recognizer model into the `models/` directory:
   ```bash
   mkdir -p models
   curl -o models/gesture_recognizer.task -L https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task
   ```

---

## 🎮 How to Play

Start the live camera interface:
```bash
uv run python main_vision.py
```

### The Gesture Keyboard
HandLang uses **14 unique inputs** by distinguishing between your **Left** and **Right** hand.
- Hold a gesture until its name pops up in the `Raw:` feed on the screen.
- Then, put that hand down and hold up the next gesture!

#### ⬅️ Left Hand: The Commands
Your left hand is your command palette.
| Gesture | Command | Description |
| :--- | :--- | :--- |
| **☝️ Pointing Up** | `FORWARD` | Moves the turtle forward (requires a number). |
| **✌️ Peace Sign** | `TURN` | Turns the turtle right by degrees (requires a number). |
| **✋ Open Palm** | `REPEAT` | Starts a loop (requires a number). |
| **✊ Closed Fist** | `END` | Closes a loop. |
| **🤟 Spiderman/ILoveYou** | `PEN_TOGGLE` | Lifts or drops the drawing pen. |
| **👍 Thumb Up** | `RUN` | Executes the entire program on the screen! |
| **👎 Thumb Down** | `UNDO` | Deletes the last command you typed. |

#### ➡️ Right Hand: The Number Pad
Your right hand is used to type numbers. Multiple numbers typed consecutively will combine! (e.g., `1`, `0`, `0` = `100`).
| Gesture | Number |
| :--- | :--- |
| **✊ Closed Fist** | `0` |
| **☝️ Pointing Up** | `1` |
| **✌️ Peace Sign** | `2` |
| **🤟 Spiderman** | `3` |
| **👍 Thumb Up** | `4` |
| **✋ Open Palm** | `5` |
| **👎 Thumb Down** | `6` |

*(Note: Because we only have digits 0-6, you cannot type 7, 8, or 9. Instead of turning 90 degrees, try turning 60 or 120 degrees to draw hexagons and triangles!)*

---

## 🎨 Example Programs to Try

Hold these gestures in order, then hit the Left Hand **RUN** gesture to watch the magic!

### 1. The Hexagon Spirograph (Advanced)
*Code:* `REPEAT 12 REPEAT 6 FORWARD 50 TURN 60 END TURN 30 END RUN`
*Draws a beautiful mandala of 12 interlocking hexagons.*

### 2. A Simple Triangle
*Code:* `REPEAT 3 FORWARD 100 TURN 120 END RUN`

### 3. Dotted Line
*Code:* `REPEAT 4 FORWARD 20 PEN_TOGGLE FORWARD 20 PEN_TOGGLE END RUN`

---

## 🏗️ Architecture
- `main_vision.py`: The entry point that captures the webcam, runs vision, handles the HUD, and calls the interpreter.
- `vision/`: Handles hand tracking (`hand_tracker.py` using MediaPipe) and debounces jitter (`stabilizer.py`).
- `language/`: Contains the HandLang compiler pipeline (`lexer.py`, `parser.py`, `semantic.py`, `interpreter.py`).
- `runtime/canvas.py`: The Tkinter UI that physically draws the AST commands.
