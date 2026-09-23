"""Blink state machine."""
import enum
import logging

import config


class BlinkState(enum.Enum):
    OPEN = 1
    CLOSING = 2
    CLOSED = 3
    OPENING = 4


class BlinkStateMachine:
    def __init__(self, baseline_ear: float):
        self.logger = logging.getLogger(__name__)
        self.baseline = baseline_ear
        self.close_thresh = baseline_ear * config.EAR_CLOSE_THRESHOLD_RATIO
        self.open_thresh = baseline_ear * config.EAR_OPEN_THRESHOLD_RATIO
        
        self.state = BlinkState.OPEN
        self.onset_time = 0.0
        
        self.pending_left_click = False
        self.left_click_time = 0.0
        
    def update(self, current_ear: float, timestamp: float) -> list[str]:
        """Update state machine with current EAR. Returns list of events."""
        events = []
        
        # 1. Check for pending left clicks timing out
        if self.pending_left_click:
            if (timestamp - self.left_click_time) > config.DOUBLE_BLINK_TIMEOUT:
                events.append("LEFT_CLICK")
                self.pending_left_click = False
                self.logger.info("Emitted LEFT_CLICK (timeout)")

        # 2. State transitions
        if self.state == BlinkState.OPEN:
            if current_ear < self.close_thresh:
                self.state = BlinkState.CLOSING
                self.onset_time = timestamp
                
        elif self.state == BlinkState.CLOSING:
            if current_ear < self.close_thresh:
                self.state = BlinkState.CLOSED
            elif current_ear > self.open_thresh:
                self.state = BlinkState.OPEN
                
        elif self.state == BlinkState.CLOSED:
            if current_ear > self.open_thresh:
                self.state = BlinkState.OPENING
                self.opening_time = timestamp
                
        elif self.state == BlinkState.OPENING:
            if current_ear > self.open_thresh:
                duration = self.opening_time - self.onset_time
                self.state = BlinkState.OPEN
                
                if duration < config.BLINK_MIN_DELIBERATE_DURATION:
                    self.logger.debug("Natural blink (%.2fs)", duration)
                elif duration <= config.BLINK_MAX_DELIBERATE_DURATION:
                    self.logger.info("Deliberate blink (%.2fs)", duration)
                    if self.pending_left_click:
                        events.append("RIGHT_CLICK")
                        self.pending_left_click = False
                        self.logger.info("Emitted RIGHT_CLICK")
                    else:
                        self.pending_left_click = True
                        self.left_click_time = timestamp
                else:
                    self.logger.debug("Oversized blink (%.2fs)", duration)
            elif current_ear < self.close_thresh:
                self.state = BlinkState.CLOSED
                
        return events
