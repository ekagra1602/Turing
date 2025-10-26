#!/usr/bin/env python3
"""
AgentFlow GUI - Simplified (No Recording)
Beautiful interface for workflow execution
Recording disabled to avoid macOS pynput/tkinter conflicts
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
from io import StringIO


class AgentFlowGUI:
    """Simple GUI for AgentFlow - Execution Only"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AgentFlow - Intelligent Workflow Automation")
        self.root.geometry("900x700")
        self.root.configure(bg='#1e1e2e')
        
        # System will be loaded after UI
        self.system = None
        self.setup_ui()
        
        # Load system after UI is ready
        self.root.after(100, self.initialize_system)
    
    def setup_ui(self):
        """Setup the UI components"""
        # Header
        header = tk.Frame(self.root, bg='#11111b', height=80)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)
        
        title = tk.Label(
            header, 
            text="⚡ AgentFlow",
            font=('SF Pro Display', 32, 'bold'),
            bg='#11111b',
            fg='#cdd6f4'
        )
        title.pack(side=tk.LEFT, padx=20, pady=15)
        
        subtitle = tk.Label(
            header,
            text="Intelligent Workflow Automation",
            font=('SF Pro Display', 12),
            bg='#11111b',
            fg='#6c7086'
        )
        subtitle.pack(side=tk.LEFT, padx=0, pady=22)
        
        # Status indicator
        self.status_label = tk.Label(
            header,
            text="● Initializing...",
            font=('SF Pro Text', 11),
            bg='#11111b',
            fg='#f9e2af'
        )
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=22)
        
        # Main content area
        content = tk.Frame(self.root, bg='#1e1e2e')
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Input section
        input_frame = tk.Frame(content, bg='#1e1e2e')
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            input_frame,
            text="What would you like to automate?",
            font=('SF Pro Text', 13, 'bold'),
            bg='#1e1e2e',
            fg='#cdd6f4'
        ).pack(anchor=tk.W, pady=(0, 8))
        
        # Input field with modern styling
        input_container = tk.Frame(input_frame, bg='#313244', highlightthickness=1, highlightbackground='#45475a')
        input_container.pack(fill=tk.X)
        
        self.input_field = tk.Entry(
            input_container,
            font=('SF Pro Text', 14),
            bg='#313244',
            fg='#cdd6f4',
            insertbackground='#cdd6f4',
            relief=tk.FLAT,
            borderwidth=0
        )
        self.input_field.pack(fill=tk.X, padx=15, pady=12)
        self.input_field.bind('<Return>', lambda e: self.execute_request())
        self.input_field.bind('<FocusIn>', lambda e: input_container.configure(highlightbackground='#89b4fa'))
        self.input_field.bind('<FocusOut>', lambda e: input_container.configure(highlightbackground='#45475a'))
        
        # Buttons row
        buttons_frame = tk.Frame(content, bg='#1e1e2e')
        buttons_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Execute button
        self.exec_btn = tk.Button(
            buttons_frame,
            text="▶ Execute",
            command=self.execute_request,
            font=('SF Pro Text', 12, 'bold'),
            bg='#89b4fa',
            fg='#11111b',
            activebackground='#74c7ec',
            activeforeground='#11111b',
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor='hand2'
        )
        self.exec_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # List workflows button
        list_btn = tk.Button(
            buttons_frame,
            text="📚 Workflows",
            command=self.list_workflows,
            font=('SF Pro Text', 12),
            bg='#45475a',
            fg='#cdd6f4',
            activebackground='#585b70',
            activeforeground='#cdd6f4',
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor='hand2'
        )
        list_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear log button
        clear_btn = tk.Button(
            buttons_frame,
            text="🗑️ Clear",
            command=self.clear_log,
            font=('SF Pro Text', 12),
            bg='#45475a',
            fg='#cdd6f4',
            activebackground='#585b70',
            activeforeground='#cdd6f4',
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor='hand2'
        )
        clear_btn.pack(side=tk.LEFT)
        
        # Output area
        tk.Label(
            content,
            text="Activity Log",
            font=('SF Pro Text', 13, 'bold'),
            bg='#1e1e2e',
            fg='#cdd6f4'
        ).pack(anchor=tk.W, pady=(10, 8))
        
        # Scrolled text with custom styling
        output_container = tk.Frame(content, bg='#181825', highlightthickness=1, highlightbackground='#45475a')
        output_container.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(
            output_container,
            font=('SF Mono', 11),
            bg='#181825',
            fg='#cdd6f4',
            insertbackground='#cdd6f4',
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=15,
            pady=15
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.output_text.tag_config('success', foreground='#a6e3a1')
        self.output_text.tag_config('warning', foreground='#f9e2af')
        self.output_text.tag_config('error', foreground='#f38ba8')
        self.output_text.tag_config('info', foreground='#89b4fa')
        self.output_text.tag_config('dim', foreground='#6c7086')
        
        # Initial message
        self.log("Welcome to AgentFlow! 🚀\n", 'success')
        self.log("Initializing system...\n\n", 'dim')
    
    def initialize_system(self):
        """Initialize the workflow system in background"""
        def init():
            try:
                # Suppress initialization output
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                
                from intelligent_workflow_system import IntelligentWorkflowSystem
                self.system = IntelligentWorkflowSystem(verbose=False, use_snowflake=True)
                
                sys.stdout = old_stdout
                self.root.after(0, self.on_system_ready)
            except Exception as e:
                self.root.after(0, lambda: self.log(f"❌ Error: {e}\n", 'error'))
                import traceback
                traceback.print_exc()
        
        threading.Thread(target=init, daemon=True).start()
    
    def on_system_ready(self):
        """Called when system is ready"""
        self.log("✅ System ready!\n", 'success')
        self.log("✅ Snowflake connected\n", 'success')
        self.log("✅ Gemini AI loaded\n\n", 'success')
        self.log("💡 Type your request and press Enter\n", 'dim')
        self.log("   Example: 'open github and search for React tutorials'\n\n", 'dim')
        self.status_label.configure(text="● Ready", fg='#a6e3a1')
        self.input_field.configure(state=tk.NORMAL)
        self.input_field.focus()
    
    def log(self, message, tag='normal'):
        """Add message to output log"""
        self.output_text.insert(tk.END, message, tag)
        self.output_text.see(tk.END)
        self.output_text.update()
    
    def clear_log(self):
        """Clear the activity log"""
        self.output_text.delete(1.0, tk.END)
        self.log("Log cleared.\n\n", 'dim')
    
    def execute_request(self):
        """Execute user request"""
        request = self.input_field.get().strip()
        if not request:
            return
        
        if not self.system:
            self.log("⚠️ System not ready yet...\n", 'warning')
            return
        
        self.log(f"\n{'='*60}\n", 'dim')
        self.log(f"💬 Request: {request}\n", 'info')
        self.log(f"{'='*60}\n\n", 'dim')
        
        # Clear input
        self.input_field.delete(0, tk.END)
        
        # Disable buttons during execution
        self.exec_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="● Executing...", fg='#f9e2af')
        
        def execute_in_thread():
            try:
                # Redirect output to GUI
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                
                # Execute
                success = self.system.execute_from_prompt(request, auto_execute=True, confirm_steps=False)
                
                # Get output
                output = sys.stdout.getvalue()
                sys.stdout = old_stdout
                
                # Display in GUI
                self.root.after(0, lambda: self.display_execution_result(output, success))
                
            except Exception as e:
                self.root.after(0, lambda: self.log(f"❌ Error: {e}\n", 'error'))
                self.root.after(0, self.restore_buttons)
        
        threading.Thread(target=execute_in_thread, daemon=True).start()
    
    def display_execution_result(self, output, success):
        """Display execution result"""
        # Parse and colorize output
        for line in output.split('\n'):
            if '✓' in line or '✅' in line:
                self.log(line + '\n', 'success')
            elif '❌' in line or 'Error' in line or 'failed' in line.lower():
                self.log(line + '\n', 'error')
            elif '⚠️' in line or 'Warning' in line:
                self.log(line + '\n', 'warning')
            elif '🔍' in line or '🤖' in line or '🚀' in line or '📍' in line:
                self.log(line + '\n', 'info')
            elif line.startswith('   '):
                self.log(line + '\n', 'dim')
            elif line.strip().startswith('='):
                self.log(line + '\n', 'dim')
            elif line.strip():
                self.log(line + '\n')
        
        self.log('\n')
        self.restore_buttons()
    
    def restore_buttons(self):
        """Restore button states"""
        self.exec_btn.configure(state=tk.NORMAL)
        self.status_label.configure(text="● Ready", fg='#a6e3a1')
    
    def list_workflows(self):
        """List all workflows"""
        if not self.system:
            self.log("⚠️ System not ready yet...\n", 'warning')
            return
        
        self.log(f"\n{'='*60}\n", 'dim')
        self.log("📚 Workflows in Snowflake\n", 'info')
        self.log(f"{'='*60}\n\n", 'dim')
        
        try:
            workflows = self.system.memory.list_workflows(status='ready')
            
            if not workflows:
                self.log("No workflows yet.\n", 'dim')
                self.log("💡 Use CLI to record: python3 workflow_cli.py\n\n", 'dim')
            else:
                for i, wf in enumerate(workflows, 1):
                    self.log(f"{i}. {wf['name']}\n", 'success')
                    if wf.get('description'):
                        self.log(f"   {wf['description']}\n", 'dim')
                    self.log(f"   Used: {wf.get('use_count', 0)} times\n\n", 'dim')
        except Exception as e:
            self.log(f"❌ Error: {e}\n", 'error')
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


def main():
    """Main entry point"""
    app = AgentFlowGUI()
    app.run()


if __name__ == "__main__":
    main()

