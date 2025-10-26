#!/usr/bin/env python3
"""
Gemini 2.5 Video Analyzer
Watches recorded screen videos and extracts semantic workflow understanding

This is the "brain" that learns by observation - like teaching an intern.
"""

import os
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from google import genai
from google.genai.types import GenerateContentConfig


class VideoWorkflowAnalyzer:
    """
    Analyzes screen recordings using Gemini 2.5 to understand user workflows.

    The goal: Learn how the user does things, so the executor can mimic their style.
    """

    def __init__(self, model: str = "gemini-2.0-flash-exp", verbose: bool = True):
        """
        Initialize video analyzer

        Args:
            model: Gemini model to use
                   - "gemini-2.0-flash-exp" (1M context, up to 1hr video)
                   - "gemini-2.5-flash" (experimental, best quality)
            verbose: Print detailed analysis
        """
        self.verbose = verbose
        self.model = model

        # Initialize Gemini
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required!")

        self.client = genai.Client(api_key=self.api_key)

        if self.verbose:
            print("✅ Video Workflow Analyzer initialized")
            print(f"   Model: {model}")

    def analyze_workflow_video(self,
                               video_path: Path,
                               workflow_name: str,
                               workflow_description: str = "") -> Dict:
        """
        Analyze a workflow video and extract semantic understanding

        Args:
            video_path: Path to recorded video
            workflow_name: Name of the workflow
            workflow_description: Optional user description

        Returns:
            Dict with semantic_actions, parameters, overall_intention
        """
        if self.verbose:
            print("\n" + "=" * 70)
            print("🧠 ANALYZING WORKFLOW VIDEO")
            print("=" * 70)
            print(f"\nWorkflow: {workflow_name}")
            print(f"Video: {video_path}")
            print(f"Size: {video_path.stat().st_size / 1024 / 1024:.1f} MB")

        # Upload video to Gemini
        if self.verbose:
            print("\n📤 Uploading video to Gemini...")

        try:
            video_file = self.client.files.upload(file=str(video_path))

            if self.verbose:
                print(f"   ✓ Uploaded: {video_file.name}")
                print(f"   ✓ State: {video_file.state}")

            # Wait for processing
            if self.verbose:
                print("\n⏳ Waiting for video processing...")

            while video_file.state == "PROCESSING":
                time.sleep(2)
                video_file = self.client.files.get(name=video_file.name)

            if video_file.state != "ACTIVE":
                raise ValueError(f"Video processing failed: {video_file.state}")

            if self.verbose:
                print("   ✓ Video ready for analysis")

        except Exception as e:
            print(f"❌ Failed to upload video: {e}")
            raise

        # Analyze the video
        if self.verbose:
            print("\n🎬 Analyzing video with Gemini...")

        analysis_prompt = f"""You are watching a screen recording of a user performing a workflow on their computer.

Workflow Name: "{workflow_name}"
Description: "{workflow_description if workflow_description else 'Not provided'}"

Your task: Watch this video carefully and understand EXACTLY what the user did, step by step.

Think of yourself as an intern learning from watching an expert work. Pay attention to:
- What applications they opened
- What they clicked on
- What they typed
- How they navigated
- Their style and approach

Please analyze the video and provide:

1. **Semantic Actions**: A step-by-step breakdown of what the user did, described in natural language
2. **Parameters**: Any values that could be substituted (e.g., "Machine Learning" course name, "ABC-123" ticket ID)
3. **Overall Intention**: What was the user trying to accomplish?
4. **Style Notes**: How did they do it? Any patterns or preferences?

Respond in this JSON format:
{{
    "overall_intention": "Brief description of the workflow goal",
    "semantic_actions": [
        {{
            "step_number": 1,
            "semantic_type": "open_application" | "click_element" | "type_text" | "scroll" | "navigate" | "wait",
            "description": "Natural language description of this action",
            "target": "What element/app/field (if applicable)",
            "value": "Typed text or parameter value (if applicable)",
            "timestamp_seconds": 0.0,
            "confidence": 0.0-1.0,
            "is_parameterizable": true/false,
            "parameter_name": "course_name | ticket_id | etc (if parameterizable)"
        }}
    ],
    "identified_parameters": [
        {{
            "name": "course_name",
            "example_value": "Machine Learning",
            "type": "string",
            "description": "Which parameter this represents"
        }}
    ],
    "style_notes": "How the user performed this workflow - their approach, tools used, navigation patterns",
    "estimated_duration_seconds": 0.0
}}

CRITICAL INSTRUCTIONS:
- Be VERY specific about what elements were clicked (e.g., "Chrome icon in dock" not just "application")
- Include ALL visible actions, even small ones (scrolling, waiting, etc.)
- Mark any value that could vary as parameterizable (course names, ticket IDs, search terms, etc.)
- Describe actions in a way that another AI could reproduce them on a different screen
- Focus on WHAT the user did, not HOW it appeared on screen
- Think like an intern learning the workflow to repeat it later

Example good action:
{{
    "step_number": 1,
    "semantic_type": "open_application",
    "description": "User opened Chrome browser using Spotlight search",
    "target": "Chrome",
    "value": null,
    "is_parameterizable": false,
    "confidence": 0.95
}}

Example bad action:
{{
    "description": "User clicked something at the top"
}}

Begin analysis now."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": analysis_prompt},
                            {"file_data": {"file_uri": video_file.uri, "mime_type": video_file.mime_type}}
                        ]
                    }
                ],
                config=GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                )
            )

            content = response.text

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            analysis = json.loads(content)

            if self.verbose:
                print("\n" + "=" * 70)
                print("✅ ANALYSIS COMPLETE")
                print("=" * 70)
                print(f"\nGoal: {analysis.get('overall_intention', 'N/A')}")
                print(f"Actions: {len(analysis.get('semantic_actions', []))}")
                print(f"Parameters: {len(analysis.get('identified_parameters', []))}")
                print()

                # Print semantic actions
                print("📋 Semantic Actions:")
                print("-" * 70)
                for action in analysis.get('semantic_actions', [])[:10]:  # First 10
                    print(f"{action['step_number']}. {action['description']}")
                    if action.get('is_parameterizable'):
                        print(f"   → Parameter: {action.get('parameter_name')}")
                if len(analysis.get('semantic_actions', [])) > 10:
                    print(f"   ... and {len(analysis['semantic_actions']) - 10} more")
                print()

                # Print parameters
                if analysis.get('identified_parameters'):
                    print("🎯 Parameters:")
                    print("-" * 70)
                    for param in analysis['identified_parameters']:
                        print(f"• {param['name']}: {param['example_value']}")
                    print()

            # Cleanup: delete uploaded file
            try:
                self.client.files.delete(name=video_file.name)
                if self.verbose:
                    print("🗑️  Cleaned up uploaded video from Gemini")
            except:
                pass

            return analysis

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            raise


def test_video_analyzer():
    """Test video analyzer on a sample recording"""
    print("=" * 70)
    print("Video Workflow Analyzer Test")
    print("=" * 70)
    print()

    # Check for recordings
    recordings_dir = Path(__file__).parent / "recordings"
    if not recordings_dir.exists():
        print("❌ No recordings directory found")
        print(f"   Record a video first using video_recorder.py")
        return

    videos = list(recordings_dir.glob("*.mp4"))
    if not videos:
        print("❌ No video recordings found")
        print(f"   Record a video first using video_recorder.py")
        return

    # Use most recent video
    latest_video = max(videos, key=lambda p: p.stat().st_mtime)

    print(f"Found video: {latest_video.name}")
    print()

    # Analyze it
    analyzer = VideoWorkflowAnalyzer(verbose=True)

    result = analyzer.analyze_workflow_video(
        video_path=latest_video,
        workflow_name="Test Workflow",
        workflow_description="Testing video analysis"
    )

    # Save analysis
    output_path = latest_video.with_suffix('.json')
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n💾 Analysis saved to: {output_path}")


if __name__ == "__main__":
    test_video_analyzer()
