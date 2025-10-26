"""
Groq LLM Client for Fast Computer Use
Ultra-fast inference for task understanding and element location
"""

import os
from typing import Optional, Dict, Any
import json

from dotenv import load_dotenv
load_dotenv()

class GroqClient:
    """
    Fast LLM client using Groq's inference platform
    
    Benefits:
    - Ultra-fast inference (< 500ms for most queries)
    - OpenAI-compatible API
    - Excellent reasoning capabilities
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key (reads from GROQ_API_KEY env if None)
            model: Model to use (default: llama-3.3-70b-versatile)
        """
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = model
        self.client = None
        
        if not self.api_key:
            print("⚠️  GROQ_API_KEY not set!")
            print("   Set with: export GROQ_API_KEY='your_key_here'")
            print("   Get key at: https://console.groq.com/keys")
        else:
            self._init_client()
    
    def _init_client(self):
        """Initialize Groq client"""
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            print(f"✅ Groq client initialized")
            print(f"   Model: {self.model}")
        except ImportError:
            print("❌ Groq library not installed!")
            print("   Install with: pip install groq")
            self.client = None
        except Exception as e:
            print(f"❌ Failed to initialize Groq client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Groq client is available"""
        return self.client is not None
    
    def query(self, 
              prompt: str, 
              system: Optional[str] = None,
              temperature: float = 0.1,
              max_tokens: int = 500) -> Optional[str]:
        """
        Query Groq LLM
        
        Args:
            prompt: User prompt
            system: System message (optional)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
        
        Returns:
            Response text or None if failed
        """
        if not self.client:
            print("❌ Groq client not available")
            return None
        
        try:
            messages = []
            
            if system:
                messages.append({"role": "system", "content": system})
            
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"❌ Groq query failed: {e}")
            return None
    
    def find_element_mark(self, 
                         element_map_text: str, 
                         target_description: str) -> Optional[int]:
        """
        Ask Groq to identify which mark ID matches a description
        
        Args:
            element_map_text: Text representation of marked elements
            target_description: What the user wants to click
        
        Returns:
            Mark ID (integer) or None
        """
        system = """You are a computer use assistant. Your job is to identify which numbered UI element matches a user's description.

Respond with ONLY the number, nothing else. If no match exists, respond with "NONE"."""
        
        prompt = f"""Elements on screen:
{element_map_text}

User wants to interact with: "{target_description}"

Which element number matches best? Respond with ONLY the number."""
        
        response = self.query(prompt, system=system, temperature=0.0, max_tokens=10)
        
        if not response:
            return None
        
        try:
            # Extract number from response
            response = response.strip().upper()
            if response == "NONE":
                return None
            
            # Try to parse as integer
            mark_id = int(response)
            return mark_id
        except:
            return None
    
    def parse_user_command(self, 
                          user_input: str, 
                          screenshot_context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Parse user command into structured action
        
        Args:
            user_input: Natural language command
            screenshot_context: Optional context about current screen
        
        Returns:
            Dict with action_type, target_element, parameters, etc.
        """
        system = """You are a computer use assistant. Parse user commands into structured actions.

Output JSON in this format:
{
  "action_type": "click|type|drag|scroll|press",
  "target_element": "description of what to find",
  "parameters": {},
  "reasoning": "brief explanation"
}"""
        
        context_str = f"\n\nScreen context:\n{screenshot_context}" if screenshot_context else ""
        
        prompt = f"""User command: "{user_input}"{context_str}

Parse this into a structured action (JSON only):"""
        
        response = self.query(prompt, system=system, temperature=0.1, max_tokens=300)
        
        if not response:
            return None
        
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return None
        except:
            return None
    
    def verify_action_result(self, 
                            action_description: str, 
                            before_context: str,
                            after_context: str) -> Dict[str, Any]:
        """
        Verify if an action succeeded by comparing before/after states
        
        Returns:
            {
                'success': bool,
                'confidence': float,
                'reasoning': str
            }
        """
        system = """You are verifying if a computer action succeeded.

Output JSON:
{
  "success": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}"""
        
        prompt = f"""Action performed: {action_description}

Before:
{before_context}

After:
{after_context}

Did the action succeed? (JSON only):"""
        
        response = self.query(prompt, system=system, temperature=0.0, max_tokens=200)
        
        if not response:
            return {'success': False, 'confidence': 0.0, 'reasoning': 'No response from LLM'}
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {'success': False, 'confidence': 0.0, 'reasoning': 'Failed to parse response'}
        except:
            return {'success': False, 'confidence': 0.0, 'reasoning': 'Invalid JSON response'}


def test_groq_client():
    """Test Groq client"""
    print("=" * 70)
    print("Groq Client Test")
    print("=" * 70)
    print()
    
    # Initialize
    client = GroqClient()
    
    if not client.is_available():
        print("❌ Groq client not available. Set GROQ_API_KEY environment variable.")
        return
    
    # Test basic query
    print("🧪 Test 1: Basic query")
    print("-" * 70)
    response = client.query("What is 2+2? Respond with just the number.")
    print(f"Response: {response}")
    print()
    
    # Test element matching
    print("🧪 Test 2: Element matching")
    print("-" * 70)
    
    element_map_text = """#1: 'Submit' at (500, 300) (conf: 0.95)
#2: 'Cancel' at (600, 300) (conf: 0.93)
#3: 'Save as Draft' at (450, 350) (conf: 0.91)
#4: 'Settings' at (50, 50) (conf: 0.98)"""
    
    print(f"Elements:\n{element_map_text}\n")
    
    test_queries = [
        "Submit button",
        "Cancel",
        "Save as Draft",
        "Settings icon"
    ]
    
    for query in test_queries:
        print(f"Query: '{query}'")
        mark_id = client.find_element_mark(element_map_text, query)
        print(f"  → Mark #{mark_id}")
    
    print()
    
    # Test command parsing
    print("🧪 Test 3: Command parsing")
    print("-" * 70)
    
    commands = [
        "Click the submit button",
        "Type 'hello world' into the search box",
        "Scroll down",
    ]
    
    for cmd in commands:
        print(f"\nCommand: '{cmd}'")
        parsed = client.parse_user_command(cmd)
        if parsed:
            print(f"  Action: {parsed.get('action_type')}")
            print(f"  Target: {parsed.get('target_element')}")
            print(f"  Reasoning: {parsed.get('reasoning')}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_groq_client()

