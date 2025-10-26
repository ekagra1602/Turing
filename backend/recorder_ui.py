#!/usr/bin/env python3
"""
Professional Recording UI
Floating overlay for AgentFlow workflow recording
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from pathlib import Path

from video_recorder import VideoRecorder
from video_analyzer import VideoWorkflowAnalyzer
from visual_memory import VisualWorkflowMemory

from dotenv import load_dotenv
load_dotenv()


class RecorderUI:
    """
    Professional floating overlay for workflow recording

    Clean, minimal UI that stays out of the way while recording.
    """

    def __init__(self):
        self.recorder = VideoRecorder(fps=10)
        self.analyzer = VideoWorkflowAnalyzer(verbose=True)
        self.memory = VisualWorkflowMemory()

        self.workflow_name = None
        self.workflow_description = None
        self.workflow_tags = []
        self.current_video_path = None

        # Create main window
        self.root = tk.Tk()
        self.root.title("AgentFlow Recorder")

        # Make it compact
        self.root.geometry("280x360")
        self.root.resizable(False, False)

        # Always on top
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)

        # Position in top-right corner
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_width - 300}+20")

        # Dark theme
        self.root.configure(bg='#1e1e1e')

        self._create_ui()
        self._update_status()

    def _create_ui(self):
        """Create the UI elements"""
        # Title
        title = tk.Label(
            self.root,
            text="AgentFlow Pro",
            font=('SF Pro Display', 16, 'bold'),
            bg='#1e1e1e',
            fg='#ffffff'
        )
        title.pack(pady=12)

        # Status frame
        status_frame = tk.Frame(self.root, bg='#1e1e1e')
        status_frame.pack(pady=8, padx=16, fill='x')

        self.status_indicator = tk.Label(
            status_frame,
            text="●",
            font=('SF Pro Display', 20),
            bg='#1e1e1e',
            fg='#4CAF50'
        )
        self.status_indicator.pack(side='left')

        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            font=('SF Pro Display', 12),
            bg='#1e1e1e',
            fg='#ffffff'
        )
        self.status_label.pack(side='left', padx=8)

        # Time display
        self.time_label = tk.Label(
            self.root,
            text="00:00",
            font=('SF Mono', 24, 'bold'),
            bg='#1e1e1e',
            fg='#888888'
        )
        self.time_label.pack(pady=8)

        # Separator
        sep = tk.Frame(self.root, height=1, bg='#333333')
        sep.pack(fill='x', pady=8, padx=16)

        # Button frame
        btn_frame = tk.Frame(self.root, bg='#1e1e1e')
        btn_frame.pack(pady=8, padx=16, fill='both', expand=True)

        # Record button
        self.record_btn = tk.Button(
            btn_frame,
            text="⏺  Record",
            command=self._start_recording,
            bg='#ff4444',
            fg='white',
            font=('SF Pro Display', 12, 'bold'),
            relief='flat',
            cursor='hand2',
            width=22,
            height=2,
            activebackground='#cc0000'
        )
        self.record_btn.pack(pady=4)

        # Stop button (disabled initially)
        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹  Stop",
            command=self._stop_recording,
            bg='#333333',
            fg='#666666',
            font=('SF Pro Display', 12),
            relief='flat',
            cursor='hand2',
            width=22,
            height=2,
            state='disabled'
        )
        self.stop_btn.pack(pady=4)

        # Analyze button (disabled initially)
        self.analyze_btn = tk.Button(
            btn_frame,
            text="🧠  Analyze",
            command=self._analyze_recording,
            bg='#333333',
            fg='#666666',
            font=('SF Pro Display', 12),
            relief='flat',
            cursor='hand2',
            width=22,
            height=2,
            state='disabled'
        )
        self.analyze_btn.pack(pady=4)

        # List workflows button
        self.list_btn = tk.Button(
            btn_frame,
            text="📚  View Workflows",
            command=self._list_workflows,
            bg='#2196F3',
            fg='white',
            font=('SF Pro Display', 11),
            relief='flat',
            cursor='hand2',
            width=22,
            height=1,
            activebackground='#1976D2'
        )
        self.list_btn.pack(pady=4)

        # Minimize button
        minimize_btn = tk.Button(
            btn_frame,
            text="—",
            command=self.root.iconify,
            bg='#333333',
            fg='#888888',
            font=('SF Pro Display', 10),
            relief='flat',
            cursor='hand2',
            width=22
        )
        minimize_btn.pack(pady=4)

    def _start_recording(self):
        """Start recording workflow"""
        # Get workflow details from user
        dialog = WorkflowDialog(self.root)
        self.root.wait_window(dialog.top)

        if not dialog.result:
            return

        self.workflow_name = dialog.result['name']
        self.workflow_description = dialog.result['description']
        self.workflow_tags = dialog.result['tags']

        # Start recording
        self.current_video_path = self.recorder.start_recording(self.workflow_name)

        if self.current_video_path:
            # Update UI
            self.status_label.config(text="Recording", fg='#ff4444')
            self.status_indicator.config(fg='#ff4444')
            self.record_btn.config(state='disabled', bg='#333333', fg='#666666')
            self.stop_btn.config(state='normal', bg='#FFC107', fg='#000000', activebackground='#FFA000')
            self.list_btn.config(state='disabled')

    def _stop_recording(self):
        """Stop recording"""
        self.current_video_path = self.recorder.stop_recording()

        if self.current_video_path:
            # Update UI
            self.status_label.config(text="Stopped", fg='#FFC107')
            self.status_indicator.config(fg='#FFC107')
            self.stop_btn.config(state='disabled', bg='#333333', fg='#666666')
            self.analyze_btn.config(state='normal', bg='#9C27B0', fg='white', activebackground='#7B1FA2')
            self.record_btn.config(state='normal', bg='#ff4444', fg='white', activebackground='#cc0000')
            self.list_btn.config(state='normal')

            messagebox.showinfo(
                "Recording Complete",
                f"Recording saved!\n\nNext: Click 'Analyze' to process with Gemini"
            )

    def _analyze_recording(self):
        """Analyze recorded video with Gemini"""
        if not self.current_video_path:
            messagebox.showerror("Error", "No recording to analyze!")
            return

        # Update UI
        self.status_label.config(text="Analyzing...", fg='#9C27B0')
        self.status_indicator.config(fg='#9C27B0')
        self.analyze_btn.config(state='disabled')

        # Run analysis in background thread
        def analyze_thread():
            try:
                # Analyze video
                analysis = self.analyzer.analyze_workflow_video(
                    video_path=self.current_video_path,
                    workflow_name=self.workflow_name,
                    workflow_description=self.workflow_description
                )

                # Create workflow in memory
                workflow_id = self.memory.create_workflow(
                    name=self.workflow_name,
                    description=analysis.get('overall_intention', self.workflow_description),
                    tags=self.workflow_tags
                )

                # Store semantic actions
                semantic_actions = analysis.get('semantic_actions', [])
                parameters = analysis.get('identified_parameters', [])

                # Convert semantic actions to steps
                for action in semantic_actions:
                    action_data = {
                        'semantic_type': action.get('semantic_type'),
                        'target': action.get('target'),
                        'value': action.get('value'),
                        'timestamp': action.get('timestamp_seconds'),
                        'confidence': action.get('confidence')
                    }

                    visual_context = {
                        'description': action.get('description'),
                        'is_parameterizable': action.get('is_parameterizable', False),
                        'parameter_name': action.get('parameter_name')
                    }

                    self.memory.add_step(
                        workflow_id=workflow_id,
                        action_type=action.get('semantic_type'),
                        action_data=action_data,
                        visual_context=visual_context
                    )

                # Copy video file to workflow directory
                import shutil
                workflow_dir = self.memory.storage_dir / workflow_id
                video_dest = workflow_dir / f"recording.mp4"
                shutil.copy(self.current_video_path, video_dest)

                # Finalize workflow
                self.memory.finalize_workflow(
                    workflow_id=workflow_id,
                    parameters=parameters,
                    semantic_actions=semantic_actions
                )

                # Update UI on main thread
                self.root.after(0, lambda: self._analysis_complete(True))

            except Exception as e:
                error_msg = str(e)
                print(f"❌ Analysis error: {error_msg}")
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda msg=error_msg: self._analysis_complete(False, msg))

        thread = threading.Thread(target=analyze_thread, daemon=True)
        thread.start()

    def _analysis_complete(self, success: bool, error: str = None):
        """Called when analysis completes"""
        if success:
            self.status_label.config(text="Ready", fg='#4CAF50')
            self.status_indicator.config(fg='#4CAF50')
            self.analyze_btn.config(state='disabled', bg='#333333', fg='#666666')

            messagebox.showinfo(
                "Analysis Complete",
                f"Workflow learned successfully!\n\n'{self.workflow_name}' is ready to use."
            )

            # Reset
            self.current_video_path = None
            self.workflow_name = None

        else:
            self.status_label.config(text="Error", fg='#ff4444')
            messagebox.showerror("Analysis Failed", f"Error: {error}")

    def _list_workflows(self):
        """Show list of learned workflows"""
        workflows = self.memory.list_workflows(status='ready')

        if not workflows:
            messagebox.showinfo(
                "No Workflows",
                "No workflows learned yet.\n\nRecord your first workflow to get started!"
            )
            return

        # Create list dialog
        ListDialog(self.root, workflows)

    def _update_status(self):
        """Update status display (timer, etc.)"""
        info = self.recorder.get_recording_info()

        if info['is_recording']:
            # Update timer
            duration = int(info['duration'])
            minutes = duration // 60
            seconds = duration % 60
            self.time_label.config(
                text=f"{minutes:02d}:{seconds:02d}",
                fg='#ff4444'
            )
        else:
            self.time_label.config(text="00:00", fg='#888888')

        # Schedule next update
        self.root.after(100, self._update_status)

    def run(self):
        """Start the UI"""
        print("=" * 70)
        print("🚀 AgentFlow Recorder Starting")
        print("=" * 70)
        print()
        print("Controls:")
        print("  1. Click 'Record' to start recording a workflow")
        print("  2. Perform your workflow on screen")
        print("  3. Click 'Stop' when done")
        print("  4. Click 'Analyze' to process with Gemini")
        print()
        print("The Gemini AI will watch your video and learn your workflow!")
        print("=" * 70)
        print()

        self.root.mainloop()


class WorkflowDialog:
    """Dialog to get workflow details"""

    def __init__(self, parent):
        self.result = None

        self.top = tk.Toplevel(parent)
        self.top.title("New Workflow")
        self.top.geometry("400x280")
        self.top.configure(bg='#1e1e1e')
        self.top.resizable(False, False)

        # Center on screen
        self.top.transient(parent)
        self.top.grab_set()

        # Name
        tk.Label(
            self.top,
            text="Workflow Name:",
            bg='#1e1e1e',
            fg='white',
            font=('SF Pro Display', 11)
        ).pack(pady=(20, 5), padx=20, anchor='w')

        self.name_entry = tk.Entry(
            self.top,
            font=('SF Pro Display', 12),
            bg='#2e2e2e',
            fg='white',
            insertbackground='white',
            relief='flat'
        )
        self.name_entry.pack(pady=(0, 15), padx=20, fill='x')
        self.name_entry.focus()

        # Description
        tk.Label(
            self.top,
            text="Description (optional):",
            bg='#1e1e1e',
            fg='white',
            font=('SF Pro Display', 11)
        ).pack(pady=(0, 5), padx=20, anchor='w')

        self.desc_entry = tk.Entry(
            self.top,
            font=('SF Pro Display', 11),
            bg='#2e2e2e',
            fg='white',
            insertbackground='white',
            relief='flat'
        )
        self.desc_entry.pack(pady=(0, 15), padx=20, fill='x')

        # Tags
        tk.Label(
            self.top,
            text="Tags (comma-separated):",
            bg='#1e1e1e',
            fg='white',
            font=('SF Pro Display', 11)
        ).pack(pady=(0, 5), padx=20, anchor='w')

        self.tags_entry = tk.Entry(
            self.top,
            font=('SF Pro Display', 11),
            bg='#2e2e2e',
            fg='white',
            insertbackground='white',
            relief='flat'
        )
        self.tags_entry.pack(pady=(0, 20), padx=20, fill='x')

        # Buttons
        btn_frame = tk.Frame(self.top, bg='#1e1e1e')
        btn_frame.pack(pady=10, padx=20, fill='x')

        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.top.destroy,
            bg='#333333',
            fg='white',
            font=('SF Pro Display', 11),
            relief='flat',
            cursor='hand2',
            width=12
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame,
            text="Start Recording",
            command=self._ok,
            bg='#ff4444',
            fg='white',
            font=('SF Pro Display', 11, 'bold'),
            relief='flat',
            cursor='hand2',
            width=16
        ).pack(side='right', padx=5)

    def _ok(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a workflow name")
            return

        tags = [t.strip() for t in self.tags_entry.get().split(',') if t.strip()]

        self.result = {
            'name': name,
            'description': self.desc_entry.get().strip(),
            'tags': tags
        }
        self.top.destroy()


class ListDialog:
    """Dialog to show workflows"""

    def __init__(self, parent, workflows):
        self.top = tk.Toplevel(parent)
        self.top.title("Learned Workflows")
        self.top.geometry("500x400")
        self.top.configure(bg='#1e1e1e')

        tk.Label(
            self.top,
            text=f"📚 Learned Workflows ({len(workflows)})",
            bg='#1e1e1e',
            fg='white',
            font=('SF Pro Display', 14, 'bold')
        ).pack(pady=15)

        # List frame
        list_frame = tk.Frame(self.top, bg='#1e1e1e')
        list_frame.pack(padx=20, pady=10, fill='both', expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        # Text widget
        text = tk.Text(
            list_frame,
            bg='#2e2e2e',
            fg='white',
            font=('SF Mono', 10),
            relief='flat',
            yscrollcommand=scrollbar.set
        )
        text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=text.yview)

        # Add workflows
        for i, wf in enumerate(workflows, 1):
            text.insert('end', f"{i}. {wf['name']}\n", 'title')
            if wf.get('description'):
                text.insert('end', f"   {wf['description']}\n")
            text.insert('end', f"   Steps: {wf['steps_count']} | Used: {wf.get('use_count', 0)} times\n")
            if wf.get('tags'):
                text.insert('end', f"   Tags: {', '.join(wf['tags'])}\n")
            text.insert('end', "\n")

        text.config(state='disabled')

        # Close button
        tk.Button(
            self.top,
            text="Close",
            command=self.top.destroy,
            bg='#333333',
            fg='white',
            font=('SF Pro Display', 11),
            relief='flat',
            cursor='hand2',
            width=12
        ).pack(pady=10)


def main():
    """Main entry point"""
    app = RecorderUI()
    app.run()


if __name__ == "__main__":
    main()
