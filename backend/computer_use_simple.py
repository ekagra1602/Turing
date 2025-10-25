"""
Simple Computer Use with Screenshots and PyAutoGUI
Works with ANY application - just open it and let the AI control it!
"""

import time
import io
from typing import Dict, Any, List, Tuple

import pyautogui
from PIL import Image

from google import genai
from google.genai import types
from google.genai.types import Content, Part


# Safety - prevent accidental mouse movements to corners
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5  # Small pause between actions


def denormalize_x(x: int, screen_width: int) -> int:
    """Convert normalized x coordinate (0-1000) to actual pixel coordinate."""
    return int(x / 1000 * screen_width)


def denormalize_y(y: int, screen_height: int) -> int:
    """Convert normalized y coordinate (0-1000) to actual pixel coordinate."""
    return int(y / 1000 * screen_height)


def take_screenshot() -> bytes:
    """Take a screenshot and return as PNG bytes."""
    screenshot = pyautogui.screenshot()

    # Convert to bytes
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr.getvalue()


def get_safari_url() -> str:
    """Get the current URL from Safari using AppleScript."""
    import subprocess

    try:
        script = '''
        tell application "Safari"
            get URL of current tab of front window
        end tell
        '''
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    # Fallback URL if we can't get it
    return "about:blank"


def execute_action(fname: str, args: Dict[str, Any], screen_width: int, screen_height: int) -> Dict[str, Any]:
    """
    Execute a single action using PyAutoGUI.

    Args:
        fname: Function name to execute
        args: Arguments for the function
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels

    Returns:
        Result dictionary
    """
    result = {}

    try:
        if fname == "open_web_browser":
            # Can't directly open browser, user should have it open
            result["note"] = "Browser should already be open"

        elif fname == "wait_5_seconds":
            time.sleep(5)

        elif fname == "navigate":
            # Type URL in address bar (user must have cursor there or we click it)
            url = args["url"]
            pyautogui.hotkey('command', 'l')  # Focus address bar (Cmd+L on Mac)
            time.sleep(0.5)
            pyautogui.write(url, interval=0.05)
            pyautogui.press('return')

        elif fname == "click_at":
            x = denormalize_x(args["x"], screen_width)
            y = denormalize_y(args["y"], screen_height)
            pyautogui.click(x, y)

        elif fname == "hover_at":
            x = denormalize_x(args["x"], screen_width)
            y = denormalize_y(args["y"], screen_height)
            pyautogui.moveTo(x, y)

        elif fname == "type_text_at":
            x = denormalize_x(args["x"], screen_width)
            y = denormalize_y(args["y"], screen_height)
            text = args["text"]
            press_enter = args.get("press_enter", True)
            clear_before_typing = args.get("clear_before_typing", True)

            # Click at position
            pyautogui.click(x, y)
            time.sleep(0.3)

            # Clear if needed
            if clear_before_typing:
                pyautogui.hotkey('command', 'a')
                pyautogui.press('backspace')

            # Type text
            pyautogui.write(text, interval=0.05)

            # Press enter if needed
            if press_enter:
                pyautogui.press('return')

        elif fname == "key_combination":
            keys = args["keys"]
            # Parse key combination (e.g., "Control+C")
            if "+" in keys:
                parts = [k.strip().lower() for k in keys.split("+")]
                # Map to pyautogui key names
                key_map = {
                    'control': 'ctrl',
                    'ctrl': 'ctrl',
                    'command': 'command',
                    'meta': 'command',
                    'shift': 'shift',
                    'alt': 'alt',
                    'option': 'option'
                }
                mapped_keys = [key_map.get(k, k) for k in parts]
                pyautogui.hotkey(*mapped_keys)
            else:
                pyautogui.press(keys.lower())

        elif fname == "scroll_document":
            direction = args["direction"]
            if direction == "down":
                pyautogui.scroll(-3)  # Negative scrolls down
            elif direction == "up":
                pyautogui.scroll(3)   # Positive scrolls up
            elif direction == "left":
                pyautogui.hscroll(-3)
            elif direction == "right":
                pyautogui.hscroll(3)

        elif fname == "scroll_at":
            x = denormalize_x(args["x"], screen_width)
            y = denormalize_y(args["y"], screen_height)
            direction = args["direction"]
            magnitude = args.get("magnitude", 800)

            # Move to position first
            pyautogui.moveTo(x, y)

            # Scroll based on magnitude
            scroll_amount = int(magnitude / 100)
            if direction == "down":
                pyautogui.scroll(-scroll_amount)
            elif direction == "up":
                pyautogui.scroll(scroll_amount)
            elif direction == "left":
                pyautogui.hscroll(-scroll_amount)
            elif direction == "right":
                pyautogui.hscroll(scroll_amount)

        elif fname == "drag_and_drop":
            start_x = denormalize_x(args["x"], screen_width)
            start_y = denormalize_y(args["y"], screen_height)
            dest_x = denormalize_x(args["destination_x"], screen_width)
            dest_y = denormalize_y(args["destination_y"], screen_height)

            pyautogui.moveTo(start_x, start_y)
            pyautogui.dragTo(dest_x, dest_y, duration=0.5)

        elif fname == "go_back":
            pyautogui.hotkey('command', '[')  # Browser back on Mac

        elif fname == "go_forward":
            pyautogui.hotkey('command', ']')  # Browser forward on Mac

        elif fname == "search":
            # Open new tab and go to Google
            pyautogui.hotkey('command', 't')  # New tab
            time.sleep(0.5)
            pyautogui.write('google.com', interval=0.05)
            pyautogui.press('return')

        else:
            result["warning"] = f"Unknown function: {fname}"

        # Small delay after action
        time.sleep(0.5)

    except Exception as e:
        result["error"] = str(e)

    return result


def run_computer_use_task(task: str, turn_limit: int = 20, verbose: bool = True):
    """
    Run a computer use task with screenshots and PyAutoGUI.

    Args:
        task: Task description for the AI
        turn_limit: Maximum number of turns
        verbose: Print detailed output
    """
    try:
        # Get screen size
        screen_width, screen_height = pyautogui.size()

        if verbose:
            print(f"✅ Screen detected: {screen_width}x{screen_height}")
            print(f"✅ Mouse position: {pyautogui.position()}")
            print()
            print(f"📋 Task: {task}")
            print()

    except Exception as e:
        print(f"❌ Error: Cannot access screen or mouse")
        print(f"   {e}")
        print()
        print("You may need to grant Accessibility permissions:")
        print("System Settings > Privacy & Security > Accessibility")
        raise

    # Initialize Gemini client
    try:
        client = genai.Client()
        if verbose:
            print("✅ Gemini AI connected")
    except Exception as e:
        print(f"❌ Error: Cannot connect to Gemini API")
        print(f"   {e}")
        print()
        print("Check your GOOGLE_API_KEY environment variable")
        raise

    # Configuration
    config = types.GenerateContentConfig(
        system_instruction="""You are controlling a computer desktop.

You can see screenshots and perform actions like clicking, typing, and scrolling.
The user has their applications already open - you just need to navigate and extract information.

Important:
- Be precise with coordinates
- Wait for pages to load (use wait_5_seconds if needed)
- If you encounter a login page, tell the user to log in manually
- Describe what you see in each screenshot
""",
        tools=[
            types.Tool(
                computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_BROWSER
                )
            )
        ],
        thinking_config=types.ThinkingConfig(include_thoughts=True),
    )

    # Take initial screenshot
    if verbose:
        print("📸 Taking initial screenshot...")

    try:
        screenshot_bytes = take_screenshot()
        if verbose:
            print(f"✅ Screenshot captured ({len(screenshot_bytes)} bytes)")
    except Exception as e:
        print(f"❌ Failed to take screenshot: {e}")
        raise

    # Initialize conversation
    if verbose:
        print("🔧 Initializing conversation with AI...")

    contents = [
        Content(role="user", parts=[
            Part(text=task),
            Part.from_bytes(data=screenshot_bytes, mime_type='image/png')
        ])
    ]

    if verbose:
        print(f"✅ Conversation ready (turn limit: {turn_limit})")
        print()

    # Agent loop
    final_response = ""

    for turn in range(turn_limit):
        if verbose:
            print("=" * 70)
            print(f"🔄 TURN {turn + 1}/{turn_limit}")
            print("=" * 70)
            print("🧠 AI is analyzing screenshot and deciding action...")

        # Generate response
        response = client.models.generate_content(
            model='gemini-2.5-computer-use-preview-10-2025',
            contents=contents,
            config=config,
        )

        candidate = response.candidates[0]
        contents.append(candidate.content)

        # Check for function calls
        function_calls = [part.function_call for part in candidate.content.parts if part.function_call]

        if not function_calls:
            # Task complete
            text_response = " ".join([
                part.text for part in candidate.content.parts
                if part.text and not getattr(part, 'thought', None)
            ])
            if verbose:
                print(f"AI finished: {text_response}")
            final_response = text_response
            break

        # Execute actions
        if verbose:
            print(f"Executing {len(function_calls)} action(s)...")

        for fc in function_calls:
            if verbose:
                print(f"  -> {fc.name}")
            result = execute_action(fc.name, fc.args, screen_width, screen_height)
            if result.get("error"):
                print(f"     Error: {result['error']}")

        # Wait a bit for UI to update
        time.sleep(1)

        # Take new screenshot
        if verbose:
            print("Capturing new state...")
        screenshot_bytes = take_screenshot()

        # Get current browser URL (required by Gemini API for browser environment)
        current_url = get_safari_url()
        
        # Create function responses
        function_responses = []
        for fc in function_calls:
            function_responses.append(
                types.FunctionResponse(
                    name=fc.name,
                    response={"status": "executed", "url": current_url},
                    parts=[
                        types.FunctionResponsePart(
                            inline_data=types.FunctionResponseBlob(
                                mime_type="image/png",
                                data=screenshot_bytes
                            )
                        )
                    ]
                )
            )

        # Add to conversation
        contents.append(
            Content(
                role="user",
                parts=[Part(function_response=fr) for fr in function_responses]
            )
        )

    else:
        final_response = f"Task did not complete within {turn_limit} turns."
        if verbose:
            print(final_response)

    return final_response


if __name__ == "__main__":
    import os

    if "GOOGLE_API_KEY" not in os.environ:
        print("Error: GOOGLE_API_KEY not set")
        exit(1)

    print("=" * 70)
    print("Simple Computer Use - PyAutoGUI Version")
    print("=" * 70)
    print()
    print("This will control your actual screen with mouse and keyboard!")
    print()
    print("IMPORTANT:")
    print("1. Open Safari (or any browser)")
    print("2. Make sure it's visible on screen")
    print("3. Don't touch mouse/keyboard during execution")
    print()

    input("Press Enter when ready...")

    print()
    print("Starting in 3 seconds...")
    time.sleep(3)

    # Example task
    task = """
    Navigate to canvas.asu.edu and wait for it to load.

    If you see a login page, tell me to log in.
    If already logged in, find and list all my enrolled courses.
    """

    result = run_computer_use_task(task, turn_limit=25, verbose=True)

    print("\n" + "=" * 70)
    print("RESULT:")
    print("=" * 70)
    print(result)
    print("=" * 70)
