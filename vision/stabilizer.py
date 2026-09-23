"""HandLang token stabilizer.

Implements a state machine that debounces rapid classification changes.
A gesture must be held for N consecutive frames to emit a token.
"""

import logging

from language.tokens import GESTURE_TO_TOKEN, Token, TokenType

logger = logging.getLogger(__name__)


class TokenStabilizer:
    """State machine for debouncing gesture classifications.

    Args:
        frames_required: Number of consecutive identical gestures required
                         to emit a token.
    """

    def __init__(self, frames_required: int) -> None:
        self.frames_required = frames_required
        self.current_gesture: str | None = None
        self.count: int = 0
        self.position: int = 0

    def process_frame(self, gesture: str | None) -> Token | None:
        """Process a gesture from a single frame and potentially emit a token.

        Args:
            gesture: The gesture label (e.g., "FIST", "ONE", "NONE") or None
                     if no hand is detected/confidence is too low.

        Returns:
            A Token if one is emitted this frame, else None.
        """
        # "NONE" or actually None both mean no valid gesture
        if gesture == "NONE" or gesture is None:
            # We don't reset immediately, we could implement a grace period,
            # but for now, any gap resets the stabilizer.
            self.current_gesture = None
            self.count = 0
            return None

        # Same gesture as previous frame
        if gesture == self.current_gesture:
            self.count += 1
            if self.count == self.frames_required:
                return self._emit(gesture)
            return None

        # New gesture
        self.current_gesture = gesture
        self.count = 1
        
        # If N=1, emit immediately
        if self.count == self.frames_required:
            return self._emit(gesture)
            
        return None

    def _emit(self, gesture: str) -> Token | None:
        """Helper to create and emit the token."""
        # Convert label to TokenType
        # Handle DIGIT_x
        tt = None
        if gesture.startswith("DIGIT_"):
            try:
                tt = getattr(TokenType, gesture)
            except AttributeError:
                pass
        else:
            tt = GESTURE_TO_TOKEN.get(gesture)

        if tt is None:
            logger.warning("Stabilizer emitted unknown gesture: %s", gesture)
            return None

        token = Token(type=tt, position=self.position)
        self.position += 1
        
        logger.info("Stabilized token: %s", token.type.name)
        
        # To avoid continuous emission if they hold the gesture,
        # we can either reset count to 0 or negative.
        # The simplest is to reset the current gesture so they have to break
        # it (e.g., to NONE or another gesture) before it counts again.
        # But for now, we'll just set count to 0. The next frame will be 1.
        # Actually, let's set it so they have to break it, or we use a cooldown.
        # For simplicity, we just reset count to 0 so holding it re-emits after N frames.
        # The PRD says "debounce: a token is emitted only when held ~0.5s".
        # If they hold it for 1s, they get 2 tokens. This is fine for e.g. FORWARD FORWARD.
        self.count = 0
        return token
