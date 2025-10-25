"""
Recording Overlay GUI
Floating window with START/STOP controls that stays on top during recording
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
from pathlib import Path
from typing import Optional, Callable

from video_recorder import ScreenVideoRecorder


class RecordingOverlay:
    """
    Floating overlay window for recording control.
    
    Features:
    - Always on top
    - START/STOP buttons
    - Recording status indicator
    - Timer display
    - Action count display
    - Minimal, non-intrusive design
    """
    
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("AgentFlow Recorder")
        
        # Make window stay on top
        self.window.attributes('-topmost', True)
        
        # Make window semi-transparent
        self.window.attributes('-alpha', 0.95)
        
        # Small, fixed size
        self.window.geometry("300x200")
        self.window.resizable(False, False)
        
        # Position in top-right corner
        screen_width = self.window.winfo_screenwidth()
        x_position = screen_width - 320
        self.window.geometry(f"+{x_position}+20")
        
        # Recorder
        self.recorder = ScreenVideoRecorder()
        
        # State
        self.is_recording = False
        self.recording_id = None
        self.start_time = None
        self.workflow_name = None
        self.workflow_description = None
        
        # Callback for when recording completes
        self.on_recording_complete: Optional[Callable[[str], None]] = None
        
        # Build UI
        self._build_ui()
        
        # Timer update
        self.timer_after_id = None
    
    def _build_ui(self):
        """Build the overlay UI"""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="🎥 AgentFlow Recorder",
            font=("Arial", 14, "bold"),
            fg="#2C3E50"
        )
        title_label.pack(pady=(0, 10))
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text="⚪ Ready",
            font=("Arial", 11),
            fg="#7F8C8D"
        )
        self.status_label.pack()
        
        # Info frame (timer + event count)
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        self.timer_label = tk.Label(
            info_frame,
            text="00:00",
            font=("Arial", 18, "bold"),
            fg="#34495E"
        )
        self.timer_label.pack()
        
        self.event_count_label = tk.Label(
            info_frame,
            text="0 actions",
            font=("Arial", 9),
            fg="#95A5A6"
        )
        self.event_count_label.pack()
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # START button
        self.start_button = tk.Button(
            button_frame,
            text="⏺ START",
            command=self._on_start_click,
            bg="#27AE60",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        self.start_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        # STOP button (disabled initially)
        self.stop_button = tk.Button(
            button_frame,
            text="⏹ STOP",
            command=self._on_stop_click,
            bg="#E74C3C",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=8,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
    
    def _on_start_click(self):
        """Handle START button click"""
        # Show input dialog
        dialog = WorkflowInputDialog(self.window)
        self.window.wait_window(dialog.dialog)
        
        if dialog.result is None:
            return  # User cancelled
        
        workflow_name, workflow_description = dialog.result
        
        if not workflow_name:
            messagebox.showerror("Error", "Workflow name is required!")
            return
        
        self.workflow_name = workflow_name
        self.workflow_description = workflow_description
        
        # Start recording
        try:
            self.recording_id = self.recorder.start_recording(
                recording_name=workflow_name,
                description=workflow_description
            )
            
            self.is_recording = True
            self.start_time = time.time()
            
            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="🔴 Recording", fg="#E74C3C")
            
            # Start timer
            self._update_timer()
            
            print(f"\n✅ Recording started: {workflow_name}")
            print("   Perform your workflow naturally...")
            print("   Click STOP when done")
        
        except Exception as e:
            messagebox.showerror("Recording Error", f"Failed to start recording:\n{e}")
            print(f"❌ Recording error: {e}")
    
    def _on_stop_click(self):
        """Handle STOP button click"""
        if not self.is_recording:
            return
        
        # Confirm
        if not messagebox.askyesno("Stop Recording", "Stop recording and process workflow?"):
            return
        
        # Stop recording
        try:
            self.recording_id = self.recorder.stop_recording()
            self.is_recording = False
            
            # Stop timer
            if self.timer_after_id:
                self.window.after_cancel(self.timer_after_id)
                self.timer_after_id = None
            
            # Update UI
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="✅ Processing...", fg="#27AE60")
            
            print("\n✅ Recording complete!")
            print("   Processing...")
            
            # Call callback if set
            if self.on_recording_complete:
                self.window.after(100, lambda: self.on_recording_complete(self.recording_id))
        
        except Exception as e:
            messagebox.showerror("Stop Error", f"Failed to stop recording:\n{e}")
            print(f"❌ Stop error: {e}")
    
    def _update_timer(self):
        """Update timer display"""
        if not self.is_recording:
            return
        
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
        
        # Update event count
        event_count = len(self.recorder.events)
        self.event_count_label.config(text=f"{event_count} actions")
        
        # Schedule next update
        self.timer_after_id = self.window.after(100, self._update_timer)
    
    def reset_ui(self):
        """Reset UI to ready state"""
        self.is_recording = False
        self.recording_id = None
        self.start_time = None
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="⚪ Ready", fg="#7F8C8D")
        self.timer_label.config(text="00:00")
        self.event_count_label.config(text="0 actions")
    
    def run(self):
        """Start the overlay (blocking)"""
        self.window.mainloop()
    
    def close(self):
        """Close the overlay"""
        if self.is_recording:
            if messagebox.askyesno("Exit", "Recording in progress. Stop and exit?"):
                self.recorder.stop_recording()
                self.window.destroy()
        else:
            self.window.destroy()


class WorkflowInputDialog:
    """Dialog to get workflow name and description"""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("New Workflow")
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center on parent
        self.dialog.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")
        
        self.result = None
        
        # Build UI
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Create New Workflow",
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Name field
        name_label = tk.Label(main_frame, text="Workflow Name *", anchor=tk.W)
        name_label.pack(fill=tk.X)
        
        self.name_entry = ttk.Entry(main_frame, font=("Arial", 10))
        self.name_entry.pack(fill=tk.X, pady=(2, 10))
        self.name_entry.focus()
        
        # Description field
        desc_label = tk.Label(main_frame, text="Description (optional)", anchor=tk.W)
        desc_label.pack(fill=tk.X)
        
        self.desc_entry = ttk.Entry(main_frame, font=("Arial", 10))
        self.desc_entry.pack(fill=tk.X, pady=(2, 15))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        ok_btn = ttk.Button(
            button_frame,
            text="Start Recording",
            command=self._on_ok
        )
        ok_btn.pack(side=tk.RIGHT)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self._on_ok())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
    
    def _on_ok(self):
        """OK button clicked"""
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Workflow name is required!", parent=self.dialog)
            return
        
        self.result = (name, desc)
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Cancel button clicked"""
        self.result = None
        self.dialog.destroy()


def main():
    """Test the recording overlay"""
    print("=" * 70)
    print("Recording Overlay Test")
    print("=" * 70)
    print()
    print("A floating window will appear.")
    print("Click START to begin recording, STOP to finish.")
    print()
    
    overlay = RecordingOverlay()
    
    # Set callback
    def on_complete(recording_id):
        print(f"\n✅ Recording complete: {recording_id}")
        print("   Ready for post-processing!")
        overlay.reset_ui()
    
    overlay.on_recording_complete = on_complete
    
    # Run overlay (blocking)
    overlay.run()


if __name__ == "__main__":
    main()

