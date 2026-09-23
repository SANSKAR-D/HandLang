"""HandLang token types and Token dataclass.

The token set is intentionally small because hand gestures are a
low-bandwidth input (~8-12 reliably distinguishable shapes).
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    """Every token type in the HandLang language."""

    # --- Gesture command tokens ---
    FORWARD = auto()
    TURN = auto()
    REPEAT = auto()
    END = auto()
    PEN_TOGGLE = auto()
    VAR = auto()
    COLOR = auto()
    IF = auto()
    RUN = auto()
    UNDO = auto()

    # --- Raw digit tokens (from gesture classifier, combined by lexer) ---
    DIGIT_0 = auto()
    DIGIT_1 = auto()
    DIGIT_2 = auto()
    DIGIT_3 = auto()
    DIGIT_4 = auto()
    DIGIT_5 = auto()
    DIGIT_6 = auto()
    DIGIT_7 = auto()
    DIGIT_8 = auto()
    DIGIT_9 = auto()

    # --- Lexer-produced ---
    NUMBER = auto()

    # --- Special ---
    EOF = auto()


# Map digit token types to their integer value
DIGIT_VALUES: dict[TokenType, int] = {
    TokenType.DIGIT_0: 0,
    TokenType.DIGIT_1: 1,
    TokenType.DIGIT_2: 2,
    TokenType.DIGIT_3: 3,
    TokenType.DIGIT_4: 4,
    TokenType.DIGIT_5: 5,
    TokenType.DIGIT_6: 6,
    TokenType.DIGIT_7: 7,
    TokenType.DIGIT_8: 8,
    TokenType.DIGIT_9: 9,
}


# Using MediaPipe GestureRecognizer (7 Gestures)
# Left Hand = Commands
# Right Hand = Digits (0 to 6)
GESTURE_TO_TOKEN: dict[str, TokenType] = {
    # Left Hand -> Commands
    "Left_Pointing_Up": TokenType.FORWARD,
    "Left_Victory": TokenType.TURN,
    "Left_Open_Palm": TokenType.REPEAT,
    "Left_Closed_Fist": TokenType.END,
    "Left_ILoveYou": TokenType.PEN_TOGGLE,
    "Left_Thumb_Up": TokenType.RUN,
    "Left_Thumb_Down": TokenType.UNDO,
    
    # Right Hand -> Digits (0, 1, 2, 3, 4, 5, 6)
    "Right_Closed_Fist": TokenType.DIGIT_0,
    "Right_Pointing_Up": TokenType.DIGIT_1,
    "Right_Victory": TokenType.DIGIT_2,
    "Right_ILoveYou": TokenType.DIGIT_3,
    "Right_Thumb_Up": TokenType.DIGIT_4,
    "Right_Open_Palm": TokenType.DIGIT_5,
    "Right_Thumb_Down": TokenType.DIGIT_6,
}


# Map keyboard token names to token types (for the keyboard demo)
NAME_TO_TOKEN: dict[str, TokenType] = {
    "FORWARD": TokenType.FORWARD,
    "TURN": TokenType.TURN,
    "REPEAT": TokenType.REPEAT,
    "END": TokenType.END,
    "PEN_TOGGLE": TokenType.PEN_TOGGLE,
    "VAR": TokenType.VAR,
    "COLOR": TokenType.COLOR,
    "IF": TokenType.IF,
    "RUN": TokenType.RUN,
    "UNDO": TokenType.UNDO,
}


@dataclass
class Token:
    """A single token in the HandLang token stream.

    Attributes:
        type: The kind of token.
        value: Payload for NUMBER tokens (int); None for others.
        position: Index in the original gesture/token stream, for error messages.
    """

    type: TokenType
    value: Any = None
    position: int = 0

    def __repr__(self) -> str:
        if self.value is not None:
            return f"Token({self.type.name}, {self.value}, pos={self.position})"
        return f"Token({self.type.name}, pos={self.position})"
