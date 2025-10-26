"""
Enhanced Context System for AgentFlow
Rich multi-modal memory with visual embeddings, semantic understanding, and intelligent analysis
"""

import time
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np
from PIL import Image
import imagehash

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️  sentence-transformers not available. Semantic matching will be limited.")


@dataclass
class VisualElement:
    """Rich representation of a UI element"""
    text: str
    confidence: float
    bbox: List[List[int]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    center: Tuple[int, int]
    element_type: Optional[str] = None  # 'button', 'link', 'input', etc.
    visual_signature: Optional[str] = None  # perceptual hash
    nearby_elements: Optional[List[str]] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ActionContext:
    """Complete context for a single action"""
    action_id: str
    step_number: int
    timestamp: float
    
    # Action details
    action_type: str  # click, scroll, type, key_press
    action_data: Dict[str, Any]
    
    # Visual context
    clicked_element: Optional[VisualElement]
    visible_elements: List[VisualElement]
    screen_hash: str  # perceptual hash of screen
    ui_state: Dict[str, Any]  # URL, window title, etc.
    
    # Screenshots
    screenshot_before_path: str
    screenshot_after_path: str
    
    # Semantic understanding
    intent_description: Optional[str] = None
    extracted_entities: Optional[Dict[str, str]] = None  # class_name: "Machine Learning"
    is_parameterizable: bool = False
    
    def to_dict(self):
        result = asdict(self)
        # Convert VisualElement objects to dicts
        if self.clicked_element:
            result['clicked_element'] = self.clicked_element.to_dict()
        result['visible_elements'] = [e.to_dict() for e in self.visible_elements]
        return result


class EnhancedContextExtractor:
    """
    Extracts rich context from actions with visual and semantic analysis.
    This is the "brain" that understands what the user is doing.
    """
    
    def __init__(self, visual_analyzer=None, use_embeddings: bool = True):
        from visual_analyzer import VisualAnalyzer
        
        self.visual_analyzer = visual_analyzer or VisualAnalyzer()
        
        # Semantic embeddings for intelligent matching
        self.use_embeddings = use_embeddings and EMBEDDINGS_AVAILABLE
        if self.use_embeddings:
            print("🧠 Loading semantic embedding model...")
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Semantic embeddings enabled")
            except Exception as e:
                print(f"⚠️  Failed to load embedding model: {e}")
                self.use_embeddings = False
                self.embedding_model = None
        else:
            self.embedding_model = None
        
        print("✅ Enhanced Context Extractor initialized")
    
    def extract_action_context(self,
                               step_number: int,
                               action_type: str,
                               action_data: Dict[str, Any],
                               screenshot_before: Image.Image,
                               screenshot_after: Image.Image,
                               workflow_id: str) -> ActionContext:
        """
        Extract complete context from an action.
        This is called during recording to build rich memory.
        """
        
        action_id = f"{workflow_id}_step_{step_number}"
        timestamp = time.time()
        
        # Extract visual elements from screenshot
        visible_elements = self._extract_visible_elements(screenshot_before)
        
        # If click action, identify what was clicked
        clicked_element = None
        if action_type == 'click':
            click_x = action_data.get('x')
            click_y = action_data.get('y')
            
            if click_x and click_y:
                clicked_element = self._identify_clicked_element(
                    screenshot_before,
                    click_x,
                    click_y,
                    visible_elements
                )
        
        # Get UI state (URL, window, etc.)
        ui_state = self._capture_ui_state()
        
        # Create screen signature
        screen_hash = str(imagehash.average_hash(screenshot_before))
        
        # Build context
        context = ActionContext(
            action_id=action_id,
            step_number=step_number,
            timestamp=timestamp,
            action_type=action_type,
            action_data=action_data,
            clicked_element=clicked_element,
            visible_elements=visible_elements,
            screen_hash=screen_hash,
            ui_state=ui_state,
            screenshot_before_path=f"step_{step_number:03d}_before.png",
            screenshot_after_path=f"step_{step_number:03d}_after.png"
        )
        
        # Analyze intent (what is the user trying to do?)
        context = self._analyze_intent(context)
        
        # Detect if this step has parameters
        context = self._detect_parameters(context, visible_elements)
        
        return context
    
    def _extract_visible_elements(self, screenshot: Image.Image) -> List[VisualElement]:
        """
        Extract all visible text elements from screenshot.
        This builds a structured representation of what's on screen.
        
        Note: This method is deprecated as VLMs handle element extraction directly.
        Keeping empty implementation for backwards compatibility.
        """
        # VLMs handle element extraction directly, no need for OCR
        elements = []
        
        # Return empty list - VLMs will handle this in the recording processor
        return elements
    
    def _identify_clicked_element(self,
                                  screenshot: Image.Image,
                                  click_x: int,
                                  click_y: int,
                                  visible_elements: List[VisualElement]) -> Optional[VisualElement]:
        """
        Identify which element was clicked based on coordinates.
        """
        # Find element closest to click point
        min_distance = float('inf')
        closest_element = None
        
        for element in visible_elements:
            center_x, center_y = element.center
            distance = ((center_x - click_x) ** 2 + (center_y - click_y) ** 2) ** 0.5
            
            if distance < min_distance and distance < 100:  # Within 100px
                min_distance = distance
                closest_element = element
        
        if closest_element:
            # Get nearby elements for context
            nearby = []
            for element in visible_elements:
                if element == closest_element:
                    continue
                
                # Check if element is near the clicked one
                dx = abs(element.center[0] - closest_element.center[0])
                dy = abs(element.center[1] - closest_element.center[1])
                
                if dx < 200 and dy < 100:
                    nearby.append(element.text)
            
            closest_element.nearby_elements = nearby[:5]  # Keep top 5
        
        return closest_element
    
    def _classify_element_type(self, text: str, bbox: List[List[int]]) -> str:
        """
        Classify UI element type based on text and appearance.
        """
        text_lower = text.lower()
        
        # Simple heuristics (could be enhanced with ML)
        if any(word in text_lower for word in ['button', 'submit', 'cancel', 'ok', 'save']):
            return 'button'
        
        if any(word in text_lower for word in ['link', 'http', 'www', '.com']):
            return 'link'
        
        # Check bbox aspect ratio
        width = bbox[1][0] - bbox[0][0]
        height = bbox[2][1] - bbox[1][1]
        
        if height > 0:
            aspect_ratio = width / height
            if aspect_ratio > 10:  # Very wide
                return 'input'
        
        if text.isupper() and len(text) < 15:
            return 'button'
        
        return 'text'
    
    def _capture_ui_state(self) -> Dict[str, Any]:
        """
        Capture current UI state (URL, window title, etc.)
        """
        import pyautogui
        
        state = {
            'screen_size': pyautogui.size(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Try to get URL from browser (macOS specific)
        try:
            from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID
            )
            
            # Get frontmost window
            for window in window_list:
                if window.get('kCGWindowLayer', 0) == 0:
                    state['window_name'] = window.get('kCGWindowOwnerName', '')
                    break
        
        except Exception as e:
            pass
        
        return state
    
    def _analyze_intent(self, context: ActionContext) -> ActionContext:
        """
        Analyze user intent for this action using LLM.
        What is the user trying to accomplish?
        """
        # Build description
        description_parts = []
        
        if context.action_type == 'click' and context.clicked_element:
            text = context.clicked_element.text
            elem_type = context.clicked_element.element_type or 'element'
            description_parts.append(f"Clicked {elem_type}: '{text}'")
        
        elif context.action_type == 'scroll':
            direction = context.action_data.get('direction', 'unknown')
            description_parts.append(f"Scrolled {direction}")
        
        elif context.action_type == 'key_press':
            key = context.action_data.get('key', 'unknown')
            description_parts.append(f"Pressed {key}")
        
        # Add context from nearby elements
        if context.clicked_element and context.clicked_element.nearby_elements:
            description_parts.append(f"Near: {', '.join(context.clicked_element.nearby_elements[:3])}")
        
        context.intent_description = '. '.join(description_parts)
        
        return context
    
    def _detect_parameters(self, 
                          context: ActionContext,
                          visible_elements: List[VisualElement]) -> ActionContext:
        """
        Detect if this action contains parameters that could vary.
        
        For example, clicking "Machine Learning" might be parameterized as {class_name}.
        """
        if context.action_type != 'click' or not context.clicked_element:
            return context
        
        clicked_text = context.clicked_element.text
        
        # Heuristics for parameter detection
        # (This can be enhanced with LLM analysis)
        
        # Check if text looks like a proper noun or specific value
        if clicked_text and len(clicked_text) > 3:
            # Not a generic button word
            generic_terms = [
                'submit', 'cancel', 'ok', 'close', 'save', 'delete',
                'next', 'previous', 'back', 'home', 'search', 'login'
            ]
            
            if clicked_text.lower() not in generic_terms:
                context.is_parameterizable = True
                
                # Try to classify parameter type
                param_name = self._infer_parameter_name(clicked_text, context.ui_state)
                
                context.extracted_entities = {
                    param_name: clicked_text
                }
        
        return context
    
    def _infer_parameter_name(self, value: str, ui_state: Dict) -> str:
        """
        Infer parameter name from value and context.
        
        Examples:
        - "Machine Learning" on canvas.asu.edu → "class_name"
        - "Settings" → "menu_item"
        - "John Doe" → "name"
        """
        # Simple keyword-based inference
        # In production, use LLM for better understanding
        
        value_lower = value.lower()
        
        # Check UI context
        window = ui_state.get('window_name', '').lower()
        
        if 'canvas' in window or 'course' in value_lower:
            return 'class_name'
        
        if any(word in value_lower for word in ['setting', 'config', 'preference']):
            return 'menu_item'
        
        if any(word in value_lower for word in ['file', 'document', 'folder']):
            return 'filename'
        
        # Default
        return 'target_text'
    
    def compute_semantic_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Compute semantic embedding for text.
        Used for intelligent workflow matching.
        """
        if not self.use_embeddings or not self.embedding_model:
            return None
        
        try:
            embedding = self.embedding_model.encode(text)
            return embedding
        except Exception as e:
            print(f"⚠️  Error computing embedding: {e}")
            return None
    
    def compute_context_embedding(self, context: ActionContext) -> Optional[np.ndarray]:
        """
        Compute semantic embedding for entire action context.
        """
        if not self.use_embeddings:
            return None
        
        # Build text representation of context
        text_parts = []
        
        if context.intent_description:
            text_parts.append(context.intent_description)
        
        if context.clicked_element:
            text_parts.append(f"Interacted with: {context.clicked_element.text}")
        
        if context.extracted_entities:
            for param, value in context.extracted_entities.items():
                text_parts.append(f"{param}: {value}")
        
        combined_text = ". ".join(text_parts)
        
        return self.compute_semantic_embedding(combined_text)


class SemanticWorkflowMatcher:
    """
    Intelligently matches user requests to learned workflows using semantic understanding.
    """
    
    def __init__(self, context_extractor: EnhancedContextExtractor):
        self.context_extractor = context_extractor
        self.use_embeddings = context_extractor.use_embeddings
        
        print("✅ Semantic Workflow Matcher initialized")
    
    def find_best_match(self,
                        user_request: str,
                        workflows: List[Dict],
                        threshold: float = 0.7) -> Tuple[Optional[Dict], float, Dict]:
        """
        Find best matching workflow for user request using semantic similarity.
        
        Returns:
            (workflow, confidence, extracted_parameters)
        """
        if not workflows:
            return None, 0.0, {}
        
        # Compute embedding for user request
        request_embedding = self.context_extractor.compute_semantic_embedding(user_request)
        
        best_match = None
        best_score = 0.0
        
        for workflow in workflows:
            # Score this workflow
            score = self._score_workflow(user_request, workflow, request_embedding)
            
            if score > best_score:
                best_score = score
                best_match = workflow
        
        if best_score < threshold:
            return None, 0.0, {}
        
        # Extract parameters from user request
        parameters = self._extract_parameters(user_request, best_match)
        
        return best_match, best_score, parameters
    
    def _score_workflow(self,
                       user_request: str,
                       workflow: Dict,
                       request_embedding: Optional[np.ndarray]) -> float:
        """
        Score how well this workflow matches the user's request.
        """
        score = 0.0
        
        # 1. Keyword matching (basic)
        request_lower = user_request.lower()
        name_lower = workflow['name'].lower()
        desc_lower = workflow.get('description', '').lower()
        
        # Exact name match
        if name_lower in request_lower or request_lower in name_lower:
            score += 0.4
        
        # Description match
        desc_words = set(desc_lower.split())
        request_words = set(request_lower.split())
        common_words = desc_words & request_words
        
        if common_words:
            score += 0.2 * (len(common_words) / max(len(request_words), 1))
        
        # 2. Tag matching
        tags = workflow.get('tags', [])
        for tag in tags:
            if tag.lower() in request_lower:
                score += 0.1
        
        # 3. Semantic similarity (if available)
        if self.use_embeddings and request_embedding is not None:
            # Get workflow embedding
            workflow_text = f"{workflow['name']}. {workflow.get('description', '')}"
            workflow_embedding = self.context_extractor.compute_semantic_embedding(workflow_text)
            
            if workflow_embedding is not None:
                # Cosine similarity
                similarity = np.dot(request_embedding, workflow_embedding) / (
                    np.linalg.norm(request_embedding) * np.linalg.norm(workflow_embedding)
                )
                score += 0.4 * max(0, similarity)  # Scale to 0-0.4
        
        return min(score, 1.0)
    
    def _extract_parameters(self, user_request: str, workflow: Dict) -> Dict[str, str]:
        """
        Extract parameter values from user request based on workflow parameters.
        
        Example:
            Request: "Open my DataVis class"
            Workflow params: [{"name": "class_name", "example": "Machine Learning"}]
            → {"class_name": "DataVis"}
        """
        parameters = {}
        
        workflow_params = workflow.get('parameters', [])
        if not workflow_params:
            return parameters
        
        request_lower = user_request.lower()
        
        # Simple extraction (can be enhanced with NLP)
        for param in workflow_params:
            param_name = param['name']
            example_value = param.get('example', '')
            
            # Try to find what replaced the example value
            # For now, use simple heuristics
            
            if 'class' in param_name and 'class' in request_lower:
                # Extract class name
                words = user_request.split()
                for i, word in enumerate(words):
                    if 'class' in word.lower():
                        # Look for next capitalized word
                        if i + 1 < len(words):
                            potential_value = words[i + 1].strip('.,!?')
                            if potential_value[0].isupper():
                                parameters[param_name] = potential_value
                                break
            
            # Generic fallback: look for capitalized words not in workflow name
            if param_name not in parameters:
                words = user_request.split()
                for word in words:
                    if word and word[0].isupper() and word not in workflow['name']:
                        if not any(word.lower() in common for common in ['my', 'the', 'canvas', 'open']):
                            parameters[param_name] = word
                            break
        
        return parameters


def test_enhanced_context():
    """Test the enhanced context system"""
    print("=" * 70)
    print("Testing Enhanced Context System")
    print("=" * 70)
    
    extractor = EnhancedContextExtractor()
    
    # Take a screenshot
    import pyautogui
    print("\nCapturing screenshot...")
    screenshot = pyautogui.screenshot()
    
    # Extract elements
    print("\nExtracting visible elements...")
    elements = extractor._extract_visible_elements(screenshot)
    
    print(f"Found {len(elements)} UI elements")
    
    if elements:
        print("\nSample elements:")
        for elem in elements[:5]:
            print(f"  - '{elem.text}' ({elem.element_type}) at {elem.center}")
    
    # Test semantic matching
    if extractor.use_embeddings:
        print("\nTesting semantic embeddings...")
        
        test_texts = [
            "Open my machine learning class",
            "Navigate to Canvas ML course",
            "Check my email"
        ]
        
        for text in test_texts:
            emb = extractor.compute_semantic_embedding(text)
            if emb is not None:
                print(f"  '{text}' → embedding shape: {emb.shape}")
    
    print("\n✅ Enhanced context system test complete!")


if __name__ == "__main__":
    test_enhanced_context()

