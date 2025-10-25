#!/usr/bin/env python3
"""
Enhanced Overlay - Full interaction recording with options
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from enhanced_recorder import EnhancedRecorder
from enhanced_player import EnhancedPlayer


class EnhancedOverlay:
    """Enhanced floating overlay for AgentFlow with full recording"""

    def __init__(self):
        self.recorder = EnhancedRecorder()
        self.player = EnhancedPlayer()
        self.recording_file = None

        # Create main window
        self.root = tk.Tk()
        self.root.title("AgentFlow Pro")

        # Make it slightly larger for more options
        self.root.geometry("220x420")
        self.root.resizable(False, False)

        # Always on top
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)

        # Position in top-right corner
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_width - 240}+20")

        self._create_ui()
        self._update_status()

    def _create_ui(self):
        """Create the UI elements"""
        # Title
        title = tk.Label(
            self.root,
            text="AgentFlow Pro",
            font=('Arial', 14, 'bold'),
            bg='#2b2b2b',
            fg='white'
        )
        title.pack(fill='x', pady=5)

        self.root.configure(bg='#2b2b2b')

        # Status frame
        status_frame = tk.Frame(self.root, bg='#2b2b2b')
        status_frame.pack(pady=5, padx=10, fill='x')

        self.status_label = tk.Label(
            status_frame,
            text="● Ready",
            font=('Arial', 10),
            bg='#2b2b2b',
            fg='#00ff00'
        )
        self.status_label.pack()

        self.count_label = tk.Label(
            status_frame,
            text="Actions: 0",
            font=('Arial', 9),
            bg='#2b2b2b',
            fg='#aaaaaa'
        )
        self.count_label.pack()

        # Recording options frame
        options_frame = tk.LabelFrame(
            self.root,
            text="Record",
            bg='#2b2b2b',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        options_frame.pack(pady=5, padx=10, fill='x')

        self.move_var = tk.BooleanVar(value=True)
        self.keyboard_var = tk.BooleanVar(value=True)

        move_check = tk.Checkbutton(
            options_frame,
            text="🖱️  Movements",
            variable=self.move_var,
            command=self._update_options,
            bg='#2b2b2b',
            fg='white',
            selectcolor='#1a1a1a',
            activebackground='#2b2b2b',
            activeforeground='white',
            font=('Arial', 8)
        )
        move_check.pack(anchor='w', padx=5)

        keyboard_check = tk.Checkbutton(
            options_frame,
            text="⌨️  Keyboard",
            variable=self.keyboard_var,
            command=self._update_options,
            bg='#2b2b2b',
            fg='white',
            selectcolor='#1a1a1a',
            activebackground='#2b2b2b',
            activeforeground='white',
            font=('Arial', 8)
        )
        keyboard_check.pack(anchor='w', padx=5)

        # Button frame
        btn_frame = tk.Frame(self.root, bg='#2b2b2b')
        btn_frame.pack(pady=5, padx=10, fill='both', expand=True)

        # Record button
        self.record_btn = tk.Button(
            btn_frame,
            text="⏺ Record",
            command=self._toggle_recording,
            bg='#28a745',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            width=18,
            height=2
        )
        self.record_btn.pack(pady=3)

        # Save button
        self.save_btn = tk.Button(
            btn_frame,
            text="💾 Save",
            command=self._save_recording,
            bg='#007bff',
            fg='white',
            font=('Arial', 10),
            relief='flat',
            cursor='hand2',
            width=18,
            state='disabled'
        )
        self.save_btn.pack(pady=3)

        # Load button
        self.load_btn = tk.Button(
            btn_frame,
            text="📁 Load",
            command=self._load_recording,
            bg='#ffc107',
            fg='black',
            font=('Arial', 10),
            relief='flat',
            cursor='hand2',
            width=18
        )
        self.load_btn.pack(pady=3)

        # Play button
        self.play_btn = tk.Button(
            btn_frame,
            text="▶ Play",
            command=self._play_recording,
            bg='#dc3545',
            fg='white',
            font=('Arial', 10),
            relief='flat',
            cursor='hand2',
            width=18,
            state='disabled'
        )
        self.play_btn.pack(pady=3)

        # Playback options
        playback_frame = tk.LabelFrame(
            self.root,
            text="Playback",
            bg='#2b2b2b',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        playback_frame.pack(pady=5, padx=10, fill='x')

        self.smooth_var = tk.BooleanVar(value=True)
        smooth_check = tk.Checkbutton(
            playback_frame,
            text="🐌 Smooth",
            variable=self.smooth_var,
            bg='#2b2b2b',
            fg='white',
            selectcolor='#1a1a1a',
            activebackground='#2b2b2b',
            activeforeground='white',
            font=('Arial', 8)
        )
        smooth_check.pack(anchor='w', padx=5)

        # Minimize button
        minimize_btn = tk.Button(
            btn_frame,
            text="—",
            command=self._minimize,
            bg='#6c757d',
            fg='white',
            font=('Arial', 8),
            relief='flat',
            cursor='hand2',
            width=18
        )
        minimize_btn.pack(pady=3)

    def _update_options(self):
        """Update recorder options"""
        self.recorder.record_movements = self.move_var.get()
        self.recorder.record_keyboard = self.keyboard_var.get()

    def _toggle_recording(self):
        """Toggle recording on/off"""
        info = self.recorder.get_recording_info()

        if not info['is_recording']:
            # Start recording
            self._update_options()
            success = self.recorder.start_recording()
            if success:
                self.record_btn.config(text="⏹ Stop", bg='#dc3545')
                self.status_label.config(text="● Recording...", fg='#ff0000')
                self.load_btn.config(state='disabled')
                self.play_btn.config(state='disabled')
                self.save_btn.config(state='disabled')
        else:
            # Stop recording
            success = self.recorder.stop_recording()
            if success:
                self.record_btn.config(text="⏺ Record", bg='#28a745')
                self.status_label.config(text="● Stopped", fg='#ffa500')
                self.load_btn.config(state='normal')
                self.save_btn.config(state='normal')

                if self.recorder.actions:
                    self.play_btn.config(state='normal')

    def _save_recording(self):
        """Save the current recording"""
        if not self.recorder.actions:
            messagebox.showwarning("No Recording", "Nothing to save!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save Recording"
        )

        if filename:
            success = self.recorder.save_recording(filename)
            if success:
                self.recording_file = filename
                messagebox.showinfo("Saved", "Recording saved!")
                self.play_btn.config(state='normal')

    def _load_recording(self):
        """Load a recording"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Load Recording"
        )

        if filename:
            success = self.recorder.load_recording(filename)
            if success:
                self.recording_file = filename
                messagebox.showinfo("Loaded", "Recording loaded!")
                self.status_label.config(text="● Loaded", fg='#00ff00')
                self.play_btn.config(state='normal')

    def _play_recording(self):
        """Play back the recording"""
        if not self.recorder.actions:
            messagebox.showwarning("No Recording", "Nothing to play!")
            return

        info = self.recorder.get_recording_info()

        msg_parts = [f"Play {info['action_count']} actions?"]
        if info['has_movements']:
            msg_parts.append("✓ Includes mouse movements")
        if info['has_keyboard']:
            msg_parts.append("✓ Includes keyboard input")
        msg_parts.append("\nMove mouse to corner to abort.")

        result = messagebox.askyesno("Play Recording", "\n".join(msg_parts))

        if result:
            self.status_label.config(text="● Playing...", fg='#00ffff')
            self.record_btn.config(state='disabled')
            self.load_btn.config(state='disabled')
            self.play_btn.config(state='disabled')
            self.save_btn.config(state='disabled')

            def playback_thread():
                try:
                    # Update player settings
                    self.player.smooth_movements = self.smooth_var.get()

                    self.player.play_recording(
                        self.recorder.initial_window_state,
                        self.recorder.actions
                    )
                    self.root.after(0, self._playback_done)
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                    self.root.after(0, self._playback_done)

            thread = threading.Thread(target=playback_thread, daemon=True)
            thread.start()

    def _playback_done(self):
        """Re-enable buttons after playback"""
        self.status_label.config(text="● Ready", fg='#00ff00')
        self.record_btn.config(state='normal')
        self.load_btn.config(state='normal')
        self.play_btn.config(state='normal')
        self.save_btn.config(state='normal')

    def _minimize(self):
        """Minimize to dock"""
        self.root.iconify()

    def _update_status(self):
        """Update status display"""
        info = self.recorder.get_recording_info()
        self.count_label.config(text=f"Actions: {info['action_count']}")

        # Schedule next update
        self.root.after(500, self._update_status)

    def run(self):
        """Start the overlay"""
        print("Starting AgentFlow Pro overlay...")
        print("Full interaction recording enabled!")
        print("  - Mouse movements")
        print("  - Clicks")
        print("  - Keyboard")
        print("  - Scrolling")
        print("  - Drags")
        print()
        self.root.mainloop()


if __name__ == "__main__":
    app = EnhancedOverlay()
    app.run()
