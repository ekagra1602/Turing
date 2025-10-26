"""
Semantic Workflow Matcher
Finds the most relevant workflow(s) based on natural language prompts

For demo with 3-5 workflows:
- Pulls all workflows from Snowflake
- Uses Gemini directly for semantic matching (no embeddings needed!)
- Fast and accurate
"""

import json
import os
from typing import List, Dict, Tuple, Optional
from pathlib import Path

try:
    from snowflake_workflow_memory import SnowflakeWorkflowMemory
    SNOWFLAKE_AVAILABLE = True
except:
    SNOWFLAKE_AVAILABLE = False
    from visual_memory import VisualWorkflowMemory


class SemanticWorkflowMatcher:
    """
    Match user prompts to stored workflows using Gemini
    
    Optimized for demos with small number of workflows (3-5):
    - Pulls ALL workflows into memory
    - Uses Gemini to directly rank them
    - No embeddings needed!
    - Fast and accurate
    """
    
    def __init__(self, memory = None, use_snowflake: bool = True):
        """
        Initialize semantic matcher
        
        Args:
            memory: Memory instance (Snowflake or local)
            use_snowflake: Use Snowflake cloud storage (default: True)
        """
        # Use Snowflake if available and requested
        if use_snowflake and SNOWFLAKE_AVAILABLE:
            self.memory = memory or SnowflakeWorkflowMemory()
            print("✅ Semantic Workflow Matcher initialized")
            print("   Using: Snowflake cloud storage + Gemini matching")
        else:
            if not SNOWFLAKE_AVAILABLE:
                print("⚠️  Snowflake not available, using local storage")
            from visual_memory import VisualWorkflowMemory
            self.memory = memory or VisualWorkflowMemory()
            print("✅ Semantic Workflow Matcher initialized")
            print("   Using: Local storage + Gemini matching")
        
        # Initialize Gemini client for matching
        from google import genai
        from google.genai.types import GenerateContentConfig
        
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("⚠️  GOOGLE_API_KEY not set - matching will fail!")
            self.gemini_client = None
        else:
            self.gemini_client = genai.Client(api_key=self.api_key)
            self.model = "gemini-2.0-flash-exp"
    
    def _create_searchable_text(self, workflow: Dict) -> str:
        """
        Create rich searchable text from workflow metadata
        
        Combines: name + description + tags + inferred intent
        """
        parts = []
        
        # Name (most important)
        parts.append(workflow.get('name', ''))
        
        # Description
        if workflow.get('description'):
            parts.append(workflow['description'])
        
        # Tags
        if workflow.get('tags'):
            parts.append(' '.join(workflow['tags']))
        
        return ' '.join(parts).strip()
    
    def find_similar_workflows(self, 
                               user_prompt: str, 
                               top_k: int = 3,
                               min_similarity: float = 0.3) -> List[Tuple[Dict, float]]:
        """
        Find workflows similar to user prompt using Gemini
        
        Args:
            user_prompt: Natural language description of what user wants
            top_k: Number of top matches to return
            min_similarity: Minimum similarity score (0-1)
        
        Returns:
            List of (workflow, similarity_score) tuples, sorted by score
        """
        return self._find_with_gemini(user_prompt, top_k, min_similarity)
    
    def _find_with_gemini(self, 
                          user_prompt: str, 
                          top_k: int,
                          min_similarity: float) -> List[Tuple[Dict, float]]:
        """
        Find similar workflows using Gemini (optimized for small datasets)
        
        Perfect for demos with 3-5 workflows:
        - Pulls all workflows from Snowflake
        - Gemini ranks them semantically
        - Fast and accurate
        """
        if not self.gemini_client:
            print("❌ Gemini client not initialized")
            return []
        
        from google.genai.types import GenerateContentConfig
        
        # Get ALL workflows (fine for 3-5 workflows)
        workflows = self.memory.list_workflows(status='ready')
        
        if not workflows:
            print("⚠️  No ready workflows found")
            return []
        
        # Create workflow list for Gemini with rich context
        workflow_list = []
        for i, wf in enumerate(workflows, 1):
            name = wf.get('workflow_name', wf.get('name', 'Unnamed'))
            desc = wf.get('workflow_description', wf.get('description', ''))
            tags = wf.get('tags', [])
            
            workflow_info = f"{i}. {name}"
            if desc:
                workflow_info += f": {desc}"
            if tags:
                workflow_info += f" (tags: {', '.join(tags)})"
            
            workflow_list.append(workflow_info)
        
        workflow_text = '\n'.join(workflow_list)
        
        # Ask Gemini to rank workflows
        prompt = f"""User request: "{user_prompt}"

Available workflows:
{workflow_text}

Analyze which workflow(s) are most relevant to the user's request.
Return ONLY a JSON array with rankings:
[
    {{"workflow_num": 1, "similarity": 0.95, "reasoning": "brief explanation"}},
    {{"workflow_num": 2, "similarity": 0.75, "reasoning": "brief explanation"}}
]

Rules:
- similarity is 0.0-1.0 (1.0 = perfect match)
- Only include workflows with similarity >= {min_similarity}
- Return top {top_k} most relevant
- Consider: task similarity, intent, domain
"""

        try:
            response = self.gemini_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=GenerateContentConfig(temperature=0.1, max_output_tokens=1024)
            )
            
            content = response.text
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            rankings = json.loads(content)
            
            # Convert to workflow objects
            results = []
            for rank in rankings:
                wf_num = rank.get('workflow_num')
                if wf_num and 1 <= wf_num <= len(workflows):
                    workflow = workflows[wf_num - 1]
                    similarity = rank.get('similarity', 0.5)
                    results.append((workflow, float(similarity)))
            
            return results
            
        except Exception as e:
            print(f"❌ Gemini matching failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def explain_match(self, user_prompt: str, workflow: Dict, similarity: float) -> str:
        """
        Explain why a workflow matches the user's prompt
        
        Args:
            user_prompt: User's request
            workflow: Matched workflow
            similarity: Similarity score
        
        Returns:
            Human-readable explanation
        """
        explanation = f"✓ Matched '{workflow['name']}' (similarity: {similarity:.0%})\n"
        explanation += f"  Description: {workflow.get('description', 'N/A')}\n"
        
        if similarity > 0.8:
            explanation += "  Confidence: High - Very similar workflow\n"
        elif similarity > 0.5:
            explanation += "  Confidence: Medium - Related workflow, may need adaptation\n"
        else:
            explanation += "  Confidence: Low - Loosely related\n"
        
        return explanation
    
def test_semantic_matcher():
    """Test semantic workflow matching"""
    print("=" * 70)
    print("Semantic Workflow Matcher Test")
    print("=" * 70)
    print()
    
    # Initialize
    matcher = SemanticWorkflowMatcher()
    
    # Test queries
    test_queries = [
        "Download a file from Canvas",
        "Open my machine learning class",
        "Submit an assignment",
        "Close a Jira ticket",
    ]
    
    print("\nTesting semantic matching:")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 70)
        
        matches = matcher.find_similar_workflows(query, top_k=3, min_similarity=0.3)
        
        if matches:
            for workflow, similarity in matches:
                print(matcher.explain_match(query, workflow, similarity))
        else:
            print("  No similar workflows found")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_semantic_matcher()

