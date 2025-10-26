#!/usr/bin/env python3
"""
Check Canvas Syllabus - Example Script
Executes the Canvas syllabus workflow with different course names
"""

from dotenv import load_dotenv
load_dotenv()

from gemini_workflow_executor import GeminiWorkflowExecutor
from visual_memory import VisualWorkflowMemory


def check_syllabus(course_name):
    """Check syllabus for any course"""

    print("=" * 70)
    print("Canvas Syllabus Checker")
    print("=" * 70)
    print()

    # Initialize
    memory = VisualWorkflowMemory()
    executor = GeminiWorkflowExecutor(memory=memory, verbose=True)

    # Find the canvas syllabus workflow
    print()
    print("🔍 Looking for Canvas syllabus workflow...")

    workflows = memory.list_workflows(status='ready')
    canvas_wf = None

    for wf in workflows:
        description = wf.get('description', '').lower()
        name = wf.get('name', '').lower()

        # Look for syllabus + canvas keywords
        if ('syllabus' in description or 'syllabus' in name) and \
           ('canvas' in description or 'canvas' in name):
            canvas_wf = wf
            print(f"✅ Found workflow: {wf['name']}")
            break

    if not canvas_wf:
        print()
        print("❌ No Canvas syllabus workflow found!")
        print()
        print("To record this workflow:")
        print("  1. Run: ./START_RECORDER.sh")
        print("  2. Click Record")
        print("  3. Open browser and navigate to Canvas")
        print("  4. Click on any course")
        print("  5. Click 'Syllabus' in sidebar")
        print("  6. Scroll through syllabus")
        print("  7. Stop and Analyze")
        print()
        return False

    # Load full workflow to check parameters
    full_wf = memory.get_workflow(canvas_wf['workflow_id'])

    # Determine parameter name
    param_name = 'course_name'
    if full_wf.get('parameters'):
        # Use the actual parameter name from the workflow
        param_name = full_wf['parameters'][0]['name']

    # Execute with new course name
    print()
    print("=" * 70)
    print(f"🎯 Checking syllabus for: {course_name}")
    print("=" * 70)
    print()

    parameters = {param_name: course_name}
    success, results = executor.execute_workflow(full_wf, parameters)

    print()
    print("=" * 70)
    if success:
        print(f"✅ Successfully checked syllabus for {course_name}!")
    else:
        print(f"⚠️  Failed to check syllabus")
    print("=" * 70)
    print()

    return success


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print()
        print("Usage: python check_canvas.py 'Course Name'")
        print()
        print("Examples:")
        print("  python check_canvas.py 'Machine Learning'")
        print("  python check_canvas.py 'Data Visualization'")
        print("  python check_canvas.py 'CSE 578: Data Visualization (2025 Fall C)'")
        print()
        sys.exit(1)

    course = sys.argv[1]
    check_syllabus(course)
