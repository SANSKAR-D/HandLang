# HandLang: Code with your Hands! 🖐️💻

**HandLang** is a fully functional, esoteric visual programming language that you write entirely by waving your hands in front of your webcam! 

Powered by Google's incredibly robust **MediaPipe Gesture AI**, HandLang maps your physical hand shapes to programming constructs in real-time. It features a complete custom compiler (Lexer, Parser, Semantic Analyzer, and Interpreter) that converts your gestures into an Abstract Syntax Tree (AST) and executes them to draw beautiful geometric art on a Turtle canvas.

---

## 🚀 Features
- **No Keyboard Required:** Write loops, variable logic, colors, and drawing commands entirely through hand gestures.
- **Robust AI Vision:** Uses a highly optimized Deep Learning Convolutional Neural Network (MediaPipe Tasks API) combined with custom coordinate heuristics (for Cross and Pinch) to ensure 100% collision-free gesture recognition.
- **Full Custom Compiler Stack:** 
  - **Lexer:** Combines digit gestures into multi-digit numbers on the fly, correctly splits IDs for variables, and immediately resolves `UNDO` commands.
  - **Parser:** Builds an Abstract Syntax Tree enforcing HandLang grammar.
  - **Semantic Checker:** Validates variable assignments and scope.
  - **Interpreter:** Executes the AST and renders commands to a Tkinter Turtle window.
- **Heads-Up Display (HUD):** A beautifully wrapped multi-line live view of your gesture stream right on your webcam feed, complete with real-time token counts, AST output, and clear error messages.

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
HandLang uses **16 unique inputs** by distinguishing between your **Left** and **Right** hand.
- Hold a gesture until its name pops up in the `Raw:` feed on the screen.
- Open your hand flat or put it down briefly between gestures to reset the stabilizer.

#### ⬅️ Left Hand: The Commands
Your left hand is your command palette.
| Gesture | Command | Description |
| :--- | :--- | :--- |
| **☝️ Pointing Up** | `FORWARD` | Moves the turtle forward (requires a number or variable). |
| **✌️ Peace Sign** | `TURN` | Turns the turtle right by degrees (requires a number or variable). |
| **✋ Open Palm** | `REPEAT` | Starts a loop (requires a number or variable). |
| **✊ Closed Fist** | `END` | Closes a loop. |
| **🤟 Spiderman** | `PEN_TOGGLE` | Lifts or drops the drawing pen. |
| **👍 Thumb Up** | `RUN` | Executes the entire program on the screen! |
| **👎 Thumb Down** | `UNDO` | Deletes the last command you typed. |
| **🤌 Pinch / OK** | `COLOR` | Changes the pen color (0=Black, 1=Red, 2=Green, 3=Blue, 4=Yellow, 5=Purple, 6=Cyan). |
| **✝️ Cross (Idx Up + Mid Right)** | `INC` | Increments a variable (`INC <var_id> <amount>`). |

#### ➡️ Right Hand: The Number Pad & Variables
Your right hand is used to type numbers and variables. Multiple numbers typed consecutively will combine automatically! (e.g., `1`, `5`, `0` = `150`).
| Gesture | Number / Command |
| :--- | :--- |
| **✊ Closed Fist** | `0` |
| **☝️ Pointing Up** | `1` |
| **✌️ Peace Sign** | `2` |
| **🤟 Spiderman** | `3` |
| **👍 Thumb Up** | `4` |
| **✋ Open Palm** | `5` |
| **👎 Thumb Down** | `6` |
| **🤌 Pinch / OK** | `VAR` | Sets or references a variable. E.g., `VAR 1 10` sets `v1 = 10`. |
| **✝️ Cross** | `INC` | Increments a variable (usable from either hand). |

*(Note: We only map digits 0-6. You can type 60 or 120 instead of 90, or combine digits like `5` + `0` = `50`.)*

---

## 🎨 Example Programs to Try

Type these sequences using your hands, then hit the Left Hand **RUN** gesture to watch the magic!

### 1. The Expanding Spiral (Using Variables & Increment)
*Code:* `VAR 1 5 REPEAT 20 FORWARD VAR 1 TURN 91 INC 1 3 END RUN`
*Description:* Sets variable 1 to 5. Loops 20 times, moving forward by variable 1, turning 91 degrees, and incrementing variable 1 by 3 each loop.

### 2. Rainbow Flower
*Code:* `COLOR 1 REPEAT 6 FORWARD 60 TURN 60 END COLOR 3 REPEAT 6 FORWARD 40 TURN 60 END COLOR 4 REPEAT 6 FORWARD 20 TURN 60 END RUN`
*Description:* Draws nested hexagons in Red, Blue, and Yellow.

### 3. Star (5-pointed)
*Code:* `COLOR 4 REPEAT 5 FORWARD 100 TURN 144 END RUN`
*Description:* Draws a classic 5-pointed yellow star (you'll need to enter 144 by typing 1, 4, 4).

### 4. Galaxy Spiral (The Best One!)
*Code:* `VAR 1 1 COLOR 2 REPEAT 100 FORWARD VAR 1 TURN 37 INC 1 1 END RUN`
*Description:* Creates a beautiful organic green spiral pattern that fans out endlessly!

---

## 🏗️ Architecture
- `main_vision.py`: The entry point that captures the webcam, runs vision, handles the HUD, and calls the interpreter.
- `vision/`: Handles hand tracking (`hand_tracker.py` using MediaPipe + custom heuristics) and debounces jitter (`stabilizer.py`).
- `language/`: Contains the HandLang compiler pipeline (`tokens.py`, `lexer.py`, `parser.py`, `semantic.py`, `interpreter.py`, `ast_nodes.py`).
- `runtime/canvas.py`: The Tkinter UI that physically draws the AST commands using turtle graphics.
