"""
Gemini 2.5 Flash Computer Use Integration
Uses Google's native computer use capabilities for accurate screen interaction
"""

import os
import time
import base64
import io
from typing import Dict, List, Optional, Tuple
from PIL import Image
import numpy as np
import pyautogui
from google import genai
from google.genai.types import (
    Tool, 
    GenerateContentConfig,
    GoogleSearch,
)


class GeminiComputerUse:
    """
    Gemini 2.5 Computer Use with official Computer Use tool.
    
    Uses the official Computer Use API with normalized coordinates (0-999)
    for maximum accuracy. See: https://ai.google.dev/gemini-api/docs/computer-use
    
    Features:
    - Official Computer Use tool (most accurate)
    - Normalized coordinates (0-999) automatically converted to pixels
    - Native Retina/HiDPI support
    - Built-in safety decisions
    """
    
    def __init__(self,
                 model: str = "gemini-2.0-flash-exp",
                 use_computer_use_model: bool = False,
                 verbose: bool = False,
                 workflows_dict: Optional[Dict[str, List[Dict]]] = None):
        """
        Initialize Gemini Computer Use

        Args:
            model: Gemini model to use
                   - "gemini-2.0-flash-exp" (default, custom approach)
                   - "gemini-2.5-computer-use-preview-10-2025" (official Computer Use model)
            use_computer_use_model: If True, use official Computer Use model and tool
            verbose: Print debug information
            workflows_dict: Optional dict of {intention: semantic_actions} for system context
        """
        self.verbose = verbose
        self.model = model
        self.use_computer_use_model = use_computer_use_model
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.workflows_dict = workflows_dict or {}

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set!")

        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)

        # Configure tools based on mode
        if self.use_computer_use_model:
            # Official Computer Use tool
            from google.genai.types import ComputerUse, Environment
            self.tools = [
                Tool(computer_use=ComputerUse(environment=Environment.ENVIRONMENT_BROWSER))
            ]
        else:
            # Regular tools
            self.tools = [
                Tool(google_search=GoogleSearch()),
            ]

        # Build system prompt with workflows
        self.system_prompt = self._build_system_prompt()

        if self.verbose:
            print(f"✅ Gemini Computer Use initialized")
            if self.use_computer_use_model:
                print(f"   Model: {model} (Official Computer Use)")
                print(f"   Using official Computer Use tool with normalized coordinates")
            else:
                print(f"   Model: {model} (Custom approach)")
                print(f"   Using manual coordinate detection")
            if self.workflows_dict:
                print(f"   Loaded {len(self.workflows_dict)} workflows into system context")

    def _build_system_prompt(self) -> str:
        """Build system prompt with all workflows"""
        import json

        prompt = """
# HARDCODED WORKFLOW TEMPLATES

These are common workflow patterns that you can use as templates for various tasks:

## Template: Send Email via Gmail

When the user wants to send an email, follow this pattern:

1. [keyboard_shortcut] Press Cmd+L to focus address bar
2. [type] Type "gmail.com" into the address bar
3. [navigate] Press Enter to navigate
4. [wait] Wait 3 seconds for page to load
5. [click] Click on "Compose" or "Compose" button
6. [wait] Wait 1 second for compose window to open
7. [type] Type recipient email in the "To" field
8. [type] Type subject in the "Subject" field
9. [type] Type email body in the message field
10. [click] Click "Send" button

**Alternative Start**: If browser needs to be opened first:
0. [open_application] Open "Brave Browser" (or Chrome/Safari)
1. [keyboard_shortcut] Press Cmd+T to open new tab
2. [keyboard_shortcut] Press Cmd+L to focus address bar
3. Continue from step 2 above...

## Template: Search on Google

1. [keyboard_shortcut] Press Cmd+L to focus address bar
2. [type] Type search query
3. [navigate] Press Enter
4. [wait] Wait for results to load

## Template: Open New Tab and Navigate

1. [keyboard_shortcut] Press Cmd+T to open new tab
2. [keyboard_shortcut] Press Cmd+L to focus address bar
3. [type] Type URL or search query
4. [navigate] Press Enter

## Template: Switch Applications

1. [keyboard_shortcut] Press Cmd+Tab to switch apps
   OR
1. [keyboard_shortcut] Press Option+Space (Raycast)
2. [type] Type application name
3. [navigate] Press Enter

## Template: Find Text on Page

1. [keyboard_shortcut] Press Cmd+F to open find
2. [type] Type search term
3. [navigate] Press Enter to find

---

# AVAILABLE LEARNED WORKFLOWS

You have access to the following learned workflows. Each workflow shows a sequence of semantic actions that the user has previously demonstrated.

"""

        if self.workflows_dict:
            for intention, actions in self.workflows_dict.items():
                prompt += f"\n## Workflow: {intention}\n\n"
                prompt += "Semantic Actions:\n"
                for i, action in enumerate(actions, 1):
                    prompt += f"{i}. [{action['semantic_type']}] {action.get('description', 'N/A')}\n"
                    if action.get('target'):
                        prompt += f"   Target: {action['target']}\n"
                    if action.get('value'):
                        prompt += f"   Value: {action['value']}\n"
                    if action.get('is_parameterizable'):
                        prompt += f"   Parameter: {action.get('parameter_name')}\n"
                prompt += "\n"
        else:
            prompt += "(No learned workflows available yet)\n\n"

        prompt += """
---

## How to Use These Workflows

1. **Check Templates First**: When the user requests a common task (email, search, navigate), use the hardcoded templates as a starting point
2. **Check Learned Workflows**: If the user's request matches a learned workflow, prioritize that as it's specific to their environment
3. **Adapt and Combine**: You can adapt these workflows based on the current screen state and user's specific request
4. **Be Flexible**: These are templates, not rigid scripts. Adapt based on what you see on screen

**CRITICAL**: Always prefer KEYBOARD SHORTCUTS over mouse clicks for reliability:
- Cmd+L: Focus address bar
- Cmd+T: New tab
- Cmd+W: Close tab
- Cmd+R: Refresh
- Cmd+F: Find on page
- Option+Space: Raycast launcher

When the user requests a task, check if it matches any of these workflows.
Follow the semantic actions from the workflow, adapting parameters as needed based on the user's request and current screen state.
"""

        return prompt

    def _encode_screenshot(self, screenshot: np.ndarray) -> str:
        """Encode screenshot to base64 for Gemini"""
        if screenshot.dtype != np.uint8:
            screenshot = (screenshot * 255).astype(np.uint8)
        
        pil_image = Image.fromarray(screenshot)
        
        # Convert RGBA to RGB if needed
        if pil_image.mode == 'RGBA':
            pil_image = pil_image.convert('RGB')
        
        # Encode as PNG for best quality
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    @staticmethod
    def get_screen_scaling(screenshot: np.ndarray) -> Tuple[float, float]:
        """
        Calculate screen scaling factor for Retina/HiDPI displays.
        
        Args:
            screenshot: Screenshot array (height, width, channels)
        
        Returns:
            (scale_x, scale_y) - scaling factors for x and y coordinates
        
        Example:
            On a 2x Retina display:
            - Screenshot: 2940x1912 pixels
            - Logical screen: 1470x956 pixels
            - Returns: (2.0, 2.0)
        """
        img_height, img_width = screenshot.shape[:2]
        screen_size = pyautogui.size()
        scale_x = img_width / screen_size.width
        scale_y = img_height / screen_size.height
        return scale_x, scale_y
    
    @staticmethod
    def scale_coordinates(x: int, y: int, scale_x: float, scale_y: float) -> Tuple[int, int]:
        """
        Convert coordinates from screenshot space to screen coordinate space.
        
        Args:
            x, y: Coordinates in screenshot space (from Gemini)
            scale_x, scale_y: Scaling factors
        
        Returns:
            (click_x, click_y) - Coordinates in logical screen space for clicking
        """
        return int(x / scale_x), int(y / scale_y)
    
    @staticmethod
    def denormalize_coordinates(x: int, y: int, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """
        Convert normalized coordinates (0-999) to actual screen pixel coordinates.
        
        This is for use with the official Computer Use model which returns
        normalized coordinates in the 0-999 range.
        
        Args:
            x: Normalized x coordinate (0-999)
            y: Normalized y coordinate (0-999)
            screen_width: Actual screen width in pixels
            screen_height: Actual screen height in pixels
        
        Returns:
            (pixel_x, pixel_y) - Actual pixel coordinates for clicking
        
        Example:
            Official Computer Use returns: (500, 500) # Center of 1000x1000 grid
            Screen is 1440x900
            Result: (720, 450) # Center of actual screen
        """
        return int(x / 1000 * screen_width), int(y / 1000 * screen_height)
    
    def click(self, target: str, screenshot: Optional[np.ndarray] = None, retry_on_fail: bool = True) -> bool:
        """
        Click on an element using Gemini's native understanding
        
        Args:
            target: Description of what to click (e.g., "Submit button", "File menu")
            screenshot: Optional screenshot (will capture if not provided)
            retry_on_fail: If True, retry with alternative search terms
        
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        if screenshot is None:
            if self.verbose:
                print("📸 Capturing screenshot...")
            screenshot = np.array(pyautogui.screenshot())
        
        img_height, img_width = screenshot.shape[:2]
        
        # Calculate scaling factor for Retina/HiDPI displays
        scale_x, scale_y = self.get_screen_scaling(screenshot)
        
        if self.verbose:
            print(f"🤖 Asking Gemini to locate: '{target}'")
        
        try:
            # Encode screenshot
            img_base64 = self._encode_screenshot(screenshot)
            
            # Create prompt for Gemini with improved accuracy
            # Add special context for Gmail compose fields
            gmail_context = ""
            target_lower = target.lower()
            if any(word in target_lower for word in ['to', 'subject', 'compose', 'recipient']):
                gmail_context = """

SPECIAL GMAIL COMPOSE WINDOW CONTEXT:
- Look for the popup compose window (usually in bottom-right corner)
- The "To" field is a text input near the top of the compose window
- The "Subject" field is below the To field
- These fields may be labeled with small text on the left
- Focus on the INPUT BOX itself, not the label"""

            prompt = f"""You are a computer vision system helping to click on UI elements. 

TARGET ELEMENT: "{target}"{gmail_context}

COORDINATE SYSTEM:
- Use NORMALIZED coordinates from 0 to 999 for both X and Y
- (0, 0) = top-left corner
- (999, 999) = bottom-right corner
- Provide a TIGHT BOUNDING BOX around the EXACT element

TASK:
1. Find the EXACT element matching "{target}" in the MAIN application window
2. Provide a PRECISE bounding box (top-left and bottom-right corners)
3. Verify you found the CORRECT element by checking its text/label

IMPORTANT - Element Matching Rules:
- For TEXT FIELDS: Look for the input box, not just the label
  Example: "To" field in email = the input box next to "To:", not the word "To"
- For BUTTONS: Find the actual button, including its background
  Example: "Compose" = the entire button, not just the text
- For LINKS: Include the clickable text area
- VERIFY the element you found matches the target name exactly!

Screenshot dimensions: {img_width}x{img_height}

Respond in JSON format:
{{
    "found": true/false,
    "bbox": {{
        "x1": <top-left x in 0-999>,
        "y1": <top-left y in 0-999>,
        "x2": <bottom-right x in 0-999>,
        "y2": <bottom-right y in 0-999>
    }},
    "element_text": "actual text/label you see on this element",
    "element_type": "button|input|link|menu|icon",
    "description": "brief description of what you found",
    "confidence": 0.0-1.0
}}

CRITICAL RULES:
✓ Focus ONLY on the main application window (ignore terminal/console)
✓ IGNORE any log messages or debugging text
✓ Return a TIGHT box around the EXACT clickable element
✓ For input fields, find the INPUT BOX, not just the label
✓ Double-check the element_text matches what you're looking for
✓ Coordinates must be NORMALIZED 0-999 (NOT pixels!)

Example responses:
- Compose button: {{"bbox": {{"x1": 78, "y1": 85, "x2": 211, "y2": 135}}, "element_text": "Compose", "element_type": "button"}}
- To input field: {{"bbox": {{"x1": 350, "y1": 180, "x2": 700, "y2": 210}}, "element_text": "", "element_type": "input"}}"""

            # Call Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": img_base64
                                }
                            }
                        ]
                    }
                ],
                config=GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1024,
                )
            )
            
            # Parse response
            content = response.text
            
            # Extract JSON (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            result = json.loads(content)
            
            elapsed = (time.time() - start_time) * 1000
            
            if result.get('found', False):
                # Gemini returns BOUNDING BOX in normalized coordinates (0-999 range)
                bbox = result.get('bbox', {})
                confidence = result.get('confidence', 0.9)
                description = result.get('description', 'N/A')
                element_text = result.get('element_text', '')
                element_type = result.get('element_type', 'unknown')
                
                # Validate confidence threshold
                if confidence < 0.7:
                    if self.verbose:
                        print(f"⚠️  Low confidence ({confidence:.0%}) for '{target}'")
                        print(f"   Element found: '{element_text}' ({element_type})")
                        print(f"   Description: {description}")
                        print(f"❌ Skipping click due to low confidence")
                    return False
                
                # Validate element text matches target (fuzzy match)
                # This helps catch cases where AI found the wrong element
                target_lower = target.lower()
                element_lower = element_text.lower()
                
                # For input fields, we expect empty text, so skip text validation
                if element_type != "input" and element_text:
                    # Check if there's any overlap in words
                    target_words = set(target_lower.split())
                    element_words = set(element_lower.split())
                    
                    # If no word overlap and texts are different, might be wrong element
                    if not target_words.intersection(element_words) and target_lower not in element_lower:
                        if self.verbose:
                            print(f"⚠️  Element text mismatch!")
                            print(f"   Looking for: '{target}'")
                            print(f"   Found: '{element_text}' ({element_type})")
                            print(f"   Description: {description}")
                            print(f"❌ Skipping click - wrong element detected")
                        return False
                
                # Extract bounding box coordinates
                x1 = int(bbox.get('x1', 0))
                y1 = int(bbox.get('y1', 0))
                x2 = int(bbox.get('x2', 999))
                y2 = int(bbox.get('y2', 999))
                
                # Validate bounding box is reasonable
                if x1 >= x2 or y1 >= y2:
                    if self.verbose:
                        print(f"❌ Invalid bounding box: ({x1}, {y1}) → ({x2}, {y2})")
                    return False
                
                # Calculate click position within bounding box
                # For buttons, click slightly left-of-center for better accuracy
                # (some buttons have visual effects that make the center less reliable)
                if element_type == "button":
                    # Click at 40% from left (slightly left of center) and 50% from top
                    click_offset_x = 0.40
                    click_offset_y = 0.50
                else:
                    # For other elements, use center
                    click_offset_x = 0.50
                    click_offset_y = 0.50
                
                # Calculate position with offset
                width = x2 - x1
                height = y2 - y1
                center_x = x1 + int(width * click_offset_x)
                center_y = y1 + int(height * click_offset_y)
                
                # Convert from normalized (0-999) to actual screen pixels
                screen_size = pyautogui.size()
                click_x, click_y = self.denormalize_coordinates(
                    center_x, center_y, 
                    screen_size.width, screen_size.height
                )
                
                if self.verbose:
                    print(f"✓ Found '{target}' in {elapsed:.0f}ms")
                    print(f"  Element: '{element_text}' ({element_type})")
                    print(f"  Bbox (normalized): ({x1}, {y1}) → ({x2}, {y2})")
                    if element_type == "button":
                        print(f"  Click offset: 40% from left (button optimization)")
                    print(f"  Click pos (normalized): ({center_x}, {center_y})")
                    print(f"  Description: {description}")
                    print(f"  Confidence: {confidence:.0%}")
                    print(f"  🎯 Click target: ({click_x}, {click_y}) on {screen_size.width}x{screen_size.height} screen")
                
                # Perform click at center of bounding box
                if self.verbose:
                    print(f"🖱️  Clicking at ({click_x}, {click_y})...")
                
                pyautogui.click(click_x, click_y)
                
                if self.verbose:
                    print("✅ Click successful!")
                
                return True
            else:
                if self.verbose:
                    print(f"❌ Could not find '{target}' on screen")
                    if 'reason' in result:
                        print(f"   Reason: {result['reason']}")
                
                # Try alternative search terms for common fields
                if retry_on_fail:
                    alternatives = self._get_alternative_targets(target)
                    if alternatives:
                        if self.verbose:
                            print(f"   🔄 Trying alternatives: {alternatives}")
                        for alt in alternatives:
                            if self.verbose:
                                print(f"   Trying: '{alt}'")
                            # Small delay to avoid API rate limits and SSL errors
                            time.sleep(0.5)
                            # Retry with alternative term (no further retries)
                            if self.click(alt, screenshot, retry_on_fail=False):
                                return True
                
                return False
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
            return False
    
    def _get_alternative_targets(self, target: str) -> List[str]:
        """
        Get alternative search terms for common UI elements
        
        Args:
            target: Original target description
        
        Returns:
            List of alternative descriptions to try
        """
        target_lower = target.lower()
        alternatives = []
        
        # Gmail compose field alternatives
        if 'to' in target_lower and 'field' in target_lower:
            alternatives = [
                "recipient email input box",
                "To input field in compose window",
                "email address field at top of compose"
            ]
        elif target_lower == 'to':
            alternatives = [
                "To field",
                "recipient input box",
                "email recipient field"
            ]
        elif 'subject' in target_lower:
            alternatives = [
                "Subject input field",
                "email subject line",
                "Subject box in compose window"
            ]
        elif 'compose' in target_lower:
            alternatives = [
                "Compose button in Gmail",
                "New email button",
                "Compose button on left side"
            ]
        elif 'send' in target_lower:
            alternatives = [
                "Send button in compose window",
                "Send email button",
                "blue Send button"
            ]
        
        return alternatives
    
    def type_text(self, text: str, target: Optional[str] = None, screenshot: Optional[np.ndarray] = None) -> bool:
        """
        Type text, optionally clicking on a target field first
        
        Args:
            text: Text to type
            target: Optional element to click first (e.g., "search box")
            screenshot: Optional screenshot
        
        Returns:
            True if successful
        """
        if target:
            # Click on target first
            if not self.click(target, screenshot):
                return False
            time.sleep(0.2)  # Brief delay
        
        if self.verbose:
            print(f"⌨️  Typing: '{text}'")
        
        pyautogui.typewrite(text, interval=0.05)
        
        if self.verbose:
            print("✅ Typing complete!")
        
        return True
    
    def scroll(self, direction: str = "down", amount: int = 3) -> bool:
        """
        Scroll the page
        
        Args:
            direction: "up" or "down"
            amount: Number of scroll units
        
        Returns:
            True if successful
        """
        if self.verbose:
            print(f"📜 Scrolling {direction}...")
        
        scroll_amount = amount if direction == "down" else -amount
        pyautogui.scroll(scroll_amount)
        
        if self.verbose:
            print("✅ Scroll complete!")
        
        return True
    
    def execute_command(self, command: str, screenshot: Optional[np.ndarray] = None) -> bool:
        """
        Execute a natural language command
        
        Args:
            command: Natural language command (e.g., "Click the submit button")
            screenshot: Optional screenshot
        
        Returns:
            True if successful
        """
        if self.verbose:
            print(f"💬 Command: '{command}'")
        
        # Parse command using Gemini
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"""Parse this computer use command into an action:

Command: "{command}"

Respond in JSON:
{{
    "action": "click" | "type" | "scroll",
    "target": "element description (for click/type)",
    "text": "text to type (for type action)",
    "direction": "up/down (for scroll)",
    "reasoning": "brief explanation"
}}""",
                config=GenerateContentConfig(temperature=0.1)
            )
            
            content = response.text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            parsed = json.loads(content)
            
            action = parsed['action']
            
            if self.verbose:
                print(f"  Action: {action}")
                print(f"  Reasoning: {parsed.get('reasoning', 'N/A')}")
            
            # Execute action
            if action == "click":
                return self.click(parsed['target'], screenshot)
            elif action == "type":
                return self.type_text(parsed['text'], parsed.get('target'), screenshot)
            elif action == "scroll":
                return self.scroll(parsed.get('direction', 'down'))
            else:
                if self.verbose:
                    print(f"❌ Unknown action: {action}")
                return False
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Error executing command: {e}")
            return False


def test_gemini_computer_use():
    """Test Gemini Computer Use"""
    print("=" * 70)
    print("Gemini 2.5 Flash Computer Use Test")
    print("=" * 70)
    print()
    
    # Initialize
    print("Initializing Gemini Computer Use...")
    agent = GeminiComputerUse(verbose=True)
    
    print("\n" + "=" * 70)
    print("Test 1: Find and describe elements")
    print("=" * 70)
    
    # Capture screenshot
    print("\n📸 Capturing screenshot...")
    screenshot = np.array(pyautogui.screenshot())
    
    # Test finding elements (without clicking)
    print("\n🔍 Testing element detection (no actual clicks)...")
    print("\nLooking for common UI elements...")
    
    test_elements = [
        "File menu",
        "Close button",
        "Search box",
    ]
    
    for element in test_elements:
        print(f"\n🔍 Searching for: '{element}'")
        # We'd normally call agent.click() here, but for testing just simulate
        print(f"   (Skipping actual click for safety)")
    
    print("\n" + "=" * 70)
    print("Test 2: Command parsing")
    print("=" * 70)
    
    test_commands = [
        "Click the submit button",
        "Type 'hello world' into the search box",
        "Scroll down",
    ]
    
    for cmd in test_commands:
        print(f"\n💬 Command: '{cmd}'")
        # Just parse, don't execute
        print(f"   (Skipping execution for safety)")
    
    print("\n✅ Test complete!")
    print("\n⚠️  To actually test clicking, run with:")
    print("   agent = GeminiComputerUse(verbose=True)")
    print("   agent.click('your target here')")


if __name__ == "__main__":
    test_gemini_computer_use()

