"""
Fast Computer Use Executor
Robust action execution with retry, verification, and drag-and-drop support
"""

import time
import pyautogui
from PIL import Image
import imagehash
from typing import Tuple, Optional, Dict, Any
from enum import Enum

from multi_strategy_locator import MultiStrategyLocator, LocatorStrategy
from coordinate_normalizer import CoordinateNormalizer


class ActionType(Enum):
    """Supported action types"""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG = "drag"
    TYPE = "type"
    PRESS = "press"
    SCROLL = "scroll"


class ExecutionResult:
    """Result of action execution"""
    def __init__(self):
        self.success = False
        self.action_type: Optional[ActionType] = None
        self.target_location: Optional[Tuple[int, int]] = None
        self.strategy_used: Optional[LocatorStrategy] = None
        self.confidence: float = 0.0
        self.attempts: int = 0
        self.ui_changed: bool = False
        self.error_message: Optional[str] = None
        self.execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'action_type': self.action_type.value if self.action_type else None,
            'target_location': self.target_location,
            'strategy_used': self.strategy_used.value if self.strategy_used else None,
            'confidence': self.confidence,
            'attempts': self.attempts,
            'ui_changed': self.ui_changed,
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms
        }


class FastComputerUseExecutor:
    """
    Execute computer use actions with robustness features:
    - Multi-strategy element location
    - Retry with exponential backoff
    - Pre/post action verification
    - Drag-and-drop support
    - Detailed logging
    """
    
    def __init__(self, 
                 max_retries: int = 3,
                 ui_settle_time: float = 0.5,
                 verbose: bool = True):
        """
        Initialize Fast Computer Use Executor
        
        Args:
            max_retries: Maximum retry attempts per action
            ui_settle_time: Time to wait for UI to settle (seconds)
            verbose: Print detailed execution logs
        """
        self.max_retries = max_retries
        self.ui_settle_time = ui_settle_time
        self.verbose = verbose
        
        if self.verbose:
            print("🚀 Initializing Fast Computer Use Executor...")
        
        # Initialize components
        self.locator = MultiStrategyLocator(verbose=verbose)
        self.normalizer = CoordinateNormalizer()
        
        # Safety
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1     # Small delay between actions
        
        if self.verbose:
            print("✅ Executor ready")
            print(f"   Max retries: {self.max_retries}")
            print(f"   UI settle time: {ui_settle_time}s")
    
    def execute_click(self, 
                     target_description: str,
                     fallback_coords: Optional[Tuple[int, int]] = None,
                     button: str = 'left') -> ExecutionResult:
        """
        Execute click action with retry and verification
        
        Args:
            target_description: What to click (e.g., "Submit button")
            fallback_coords: Normalized (0-1000) fallback coordinates
            button: Mouse button ('left', 'right', 'middle')
        
        Returns:
            ExecutionResult
        """
        result = ExecutionResult()
        result.action_type = ActionType.CLICK
        start_time = time.time()
        
        if self.verbose:
            print(f"\n🖱️  CLICK: '{target_description}'")
            print("=" * 70)
        
        for attempt in range(1, self.max_retries + 1):
            result.attempts = attempt
            
            if attempt > 1 and self.verbose:
                print(f"\n🔄 Retry attempt {attempt}/{self.max_retries}")
            
            # Take pre-action screenshot
            screenshot_before = pyautogui.screenshot()
            
            # Locate element
            x, y, confidence, strategy = self.locator.locate_element(
                screenshot_before,
                target_description,
                fallback_coords
            )
            
            if x is None:
                if attempt < self.max_retries:
                    retry_delay = 1.0 * attempt
                    if self.verbose:
                        print(f"   ⏳ Element not found. Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                    continue
                else:
                    result.error_message = "Element not found after all retries"
                    result.execution_time_ms = (time.time() - start_time) * 1000
                    return result
            
            # Execute click
            result.target_location = (x, y)
            result.strategy_used = strategy
            result.confidence = confidence
            
            if self.verbose:
                print(f"   🎯 Clicking at ({x}, {y}) using {strategy.value}")
            
            pyautogui.click(x, y, button=button)
            
            # Wait for UI to settle
            time.sleep(self.ui_settle_time)
            
            # Take post-action screenshot
            screenshot_after = pyautogui.screenshot()
            
            # Verify UI changed
            result.ui_changed = self._detect_ui_change(screenshot_before, screenshot_after)
            
            if self.verbose:
                print(f"   {'✅' if result.ui_changed else '⚠️ '} UI changed: {result.ui_changed}")
            
            result.success = True
            result.execution_time_ms = (time.time() - start_time) * 1000
            
            if self.verbose:
                print(f"   ✅ Click executed in {result.execution_time_ms:.0f}ms")
            
            return result
        
        result.error_message = "Max retries exceeded"
        result.execution_time_ms = (time.time() - start_time) * 1000
        return result
    
    def execute_drag_drop(self,
                         start_description: str,
                         end_description: str,
                         duration: float = 0.5) -> ExecutionResult:
        """
        Execute drag-and-drop action
        
        Args:
            start_description: Element to drag from
            end_description: Element to drag to
            duration: Duration of drag in seconds
        
        Returns:
            ExecutionResult
        """
        result = ExecutionResult()
        result.action_type = ActionType.DRAG
        start_time = time.time()
        
        if self.verbose:
            print(f"\n🖱️  DRAG: '{start_description}' → '{end_description}'")
            print("=" * 70)
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        
        # Locate start element
        start_x, start_y, conf1, strat1 = self.locator.locate_element(screenshot, start_description)
        
        if start_x is None:
            result.error_message = f"Start element not found: {start_description}"
            result.execution_time_ms = (time.time() - start_time) * 1000
            if self.verbose:
                print(f"   ❌ {result.error_message}")
            return result
        
        if self.verbose:
            print(f"   🎯 Start: ({start_x}, {start_y}) using {strat1.value}")
        
        # Locate end element
        end_x, end_y, conf2, strat2 = self.locator.locate_element(screenshot, end_description)
        
        if end_x is None:
            result.error_message = f"End element not found: {end_description}"
            result.execution_time_ms = (time.time() - start_time) * 1000
            if self.verbose:
                print(f"   ❌ {result.error_message}")
            return result
        
        if self.verbose:
            print(f"   🎯 End: ({end_x}, {end_y}) using {strat2.value}")
        
        # Execute drag
        pyautogui.moveTo(start_x, start_y)
        time.sleep(0.2)
        
        if self.verbose:
            print(f"   🖱️  Dragging...")
        
        pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)
        time.sleep(self.ui_settle_time)
        
        result.success = True
        result.target_location = (end_x, end_y)
        result.confidence = min(conf1, conf2)
        result.strategy_used = strat1 if conf1 < conf2 else strat2
        result.execution_time_ms = (time.time() - start_time) * 1000
        
        if self.verbose:
            print(f"   ✅ Drag completed in {result.execution_time_ms:.0f}ms")
        
        return result
    
    def execute_type(self, text: str, interval: float = 0.05) -> ExecutionResult:
        """
        Type text
        
        Args:
            text: Text to type
            interval: Interval between keystrokes
        
        Returns:
            ExecutionResult
        """
        result = ExecutionResult()
        result.action_type = ActionType.TYPE
        start_time = time.time()
        
        if self.verbose:
            print(f"\n⌨️  TYPE: '{text}'")
            print("=" * 70)
        
        pyautogui.write(text, interval=interval)
        time.sleep(self.ui_settle_time)
        
        result.success = True
        result.execution_time_ms = (time.time() - start_time) * 1000
        
        if self.verbose:
            print(f"   ✅ Typed in {result.execution_time_ms:.0f}ms")
        
        return result
    
    def execute_press(self, key: str) -> ExecutionResult:
        """
        Press a key
        
        Args:
            key: Key to press (e.g., 'enter', 'escape', 'tab')
        
        Returns:
            ExecutionResult
        """
        result = ExecutionResult()
        result.action_type = ActionType.PRESS
        start_time = time.time()
        
        if self.verbose:
            print(f"\n⌨️  PRESS: {key}")
            print("=" * 70)
        
        pyautogui.press(key)
        time.sleep(self.ui_settle_time)
        
        result.success = True
        result.execution_time_ms = (time.time() - start_time) * 1000
        
        if self.verbose:
            print(f"   ✅ Pressed in {result.execution_time_ms:.0f}ms")
        
        return result
    
    def execute_scroll(self, direction: str = 'down', amount: int = 3) -> ExecutionResult:
        """
        Scroll
        
        Args:
            direction: 'up', 'down', 'left', 'right'
            amount: Scroll amount
        
        Returns:
            ExecutionResult
        """
        result = ExecutionResult()
        result.action_type = ActionType.SCROLL
        start_time = time.time()
        
        if self.verbose:
            print(f"\n📜 SCROLL: {direction} ({amount})")
            print("=" * 70)
        
        if direction == 'down':
            pyautogui.scroll(-amount)
        elif direction == 'up':
            pyautogui.scroll(amount)
        elif direction == 'left':
            pyautogui.hscroll(-amount)
        elif direction == 'right':
            pyautogui.hscroll(amount)
        
        time.sleep(self.ui_settle_time)
        
        result.success = True
        result.execution_time_ms = (time.time() - start_time) * 1000
        
        if self.verbose:
            print(f"   ✅ Scrolled in {result.execution_time_ms:.0f}ms")
        
        return result
    
    def _detect_ui_change(self, 
                         img_before: Image.Image, 
                         img_after: Image.Image,
                         threshold: int = 5) -> bool:
        """
        Detect if UI changed between screenshots
        
        Args:
            img_before: Screenshot before action
            img_after: Screenshot after action
            threshold: Perceptual hash difference threshold
        
        Returns:
            True if significant change detected
        """
        hash_before = imagehash.average_hash(img_before)
        hash_after = imagehash.average_hash(img_after)
        
        difference = hash_before - hash_after
        return difference > threshold


def test_executor():
    """Test fast computer use executor"""
    print("=" * 70)
    print("Fast Computer Use Executor Test")
    print("=" * 70)
    print()
    
    executor = FastComputerUseExecutor(verbose=True)
    
    print("\n⚠️  This test will control your mouse!")
    print("Move mouse to top-left corner to abort (failsafe)")
    print()
    
    try:
        user_input = input("Press Enter to start test, or Ctrl+C to cancel: ")
    except (EOFError, KeyboardInterrupt):
        print("\nTest cancelled")
        return
    
    # Test 1: Click on a UI element
    print("\n" + "=" * 70)
    print("Test 1: Click")
    print("=" * 70)
    
    result = executor.execute_click("Finder", fallback_coords=(100, 900))
    print(f"\nResult: {result.to_dict()}")
    
    time.sleep(2)
    
    # Test 2: Type text
    print("\n" + "=" * 70)
    print("Test 2: Type")
    print("=" * 70)
    
    result = executor.execute_type("Hello from AgentFlow!")
    print(f"\nResult: {result.to_dict()}")
    
    time.sleep(1)
    
    # Test 3: Press key
    print("\n" + "=" * 70)
    print("Test 3: Press Escape")
    print("=" * 70)
    
    result = executor.execute_press("escape")
    print(f"\nResult: {result.to_dict()}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_executor()

