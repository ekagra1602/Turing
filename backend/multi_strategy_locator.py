"""
Multi-Strategy Element Locator
Combines OCR, Set-of-Marks, Groq LLM, and fallback strategies for robust element location
"""

import numpy as np
from PIL import Image
from typing import Tuple, Optional, Dict, List
from enum import Enum

from vlm_ocr_engine import VLMOCREngine
from set_of_marks import SetOfMarks
from groq_client import GroqClient
from coordinate_normalizer import CoordinateNormalizer


class LocatorStrategy(Enum):
    """Element location strategies in order of preference"""
    OCR_EXACT = "ocr_exact"           # Exact text match from OCR
    OCR_FUZZY = "ocr_fuzzy"           # Fuzzy text match from OCR
    SET_OF_MARKS = "set_of_marks"     # Set-of-marks + Groq LLM
    POSITION_FALLBACK = "position"    # Use normalized coordinates from recording
    NOT_FOUND = "not_found"           # All strategies failed


class MultiStrategyLocator:
    """
    Locate UI elements using multiple strategies with fallback chain.
    
    Strategy Chain (in order):
    1. OCR Exact Match (fastest, most reliable)
    2. OCR Fuzzy Match (handles typos, variations)
    3. Set-of-Marks + Groq LLM (visual grounding)
    4. Position Fallback (use recorded coordinates)
    5. User Prompt (ask for help)
    """
    
    def __init__(self, 
                 use_gpu: bool = False,
                 enable_groq: bool = True,
                 verbose: bool = True):
        """
        Initialize Multi-Strategy Locator
        
        Args:
            use_gpu: Use GPU for OCR if available
            enable_groq: Enable Groq LLM for visual grounding
            verbose: Print debug information
        """
        self.verbose = verbose
        
        # Initialize components
        if self.verbose:
            print("🚀 Initializing Multi-Strategy Locator...")
        
        self.ocr = VLMOCREngine(verbose=False)
        self.som = SetOfMarks(font_size=16)
        self.normalizer = CoordinateNormalizer()
        
        if enable_groq:
            self.groq = GroqClient()
            if not self.groq.is_available():
                if self.verbose:
                    print("⚠️  Groq LLM not available - set-of-marks strategy disabled")
                self.groq = None
        else:
            self.groq = None
        
        # Strategy thresholds
        self.ocr_exact_threshold = 0.95
        self.ocr_fuzzy_threshold = 0.60  # Lower for VLM OCR (less precise than local OCR)
        self.groq_confidence = 0.85  # Confidence when using Groq
        self.position_confidence = 0.50  # Confidence when using position fallback
        
        if self.verbose:
            print("✅ Multi-Strategy Locator ready")
            print(f"   Strategies: OCR → Fuzzy → {'Groq → ' if self.groq else ''}Position")
    
    def locate_element(self, 
                      screenshot: Image.Image,
                      target_description: str,
                      fallback_normalized_coords: Optional[Tuple[int, int]] = None,
                      min_ocr_confidence: float = 0.6) -> Tuple[Optional[int], Optional[int], float, LocatorStrategy]:
        """
        Locate element using multiple strategies
        
        Args:
            screenshot: Current screenshot (PIL Image)
            target_description: What to find (e.g., "Submit button", "Search box")
            fallback_normalized_coords: Normalized (0-1000) coords as last resort
            min_ocr_confidence: Minimum OCR confidence to consider
        
        Returns:
            (x, y, confidence, strategy_used)
            Returns (None, None, 0.0, NOT_FOUND) if all strategies fail
        """
        if self.verbose:
            print(f"\n🔍 Locating: '{target_description}'")
        
        # Convert screenshot to numpy for OCR
        screenshot_np = np.array(screenshot)
        
        # Run OCR once (reuse for multiple strategies)
        ocr_detections = self.ocr.detect_text_with_boxes(screenshot_np)
        
        # Filter by confidence
        ocr_detections = [d for d in ocr_detections if d['confidence'] >= min_ocr_confidence]
        
        if self.verbose:
            print(f"   OCR: {len(ocr_detections)} elements detected")
        
        # Strategy 1: OCR Exact Match
        result = self._strategy_ocr_exact(ocr_detections, target_description)
        if result:
            return result
        
        # Strategy 2: OCR Fuzzy Match
        result = self._strategy_ocr_fuzzy(ocr_detections, target_description)
        if result:
            return result
        
        # Strategy 3: Set-of-Marks + Groq LLM
        if self.groq:
            result = self._strategy_set_of_marks(screenshot, ocr_detections, target_description)
            if result:
                return result
        
        # Strategy 4: Position Fallback
        if fallback_normalized_coords:
            result = self._strategy_position_fallback(fallback_normalized_coords)
            if result:
                return result
        
        # All strategies failed
        if self.verbose:
            print("   ❌ Element not found with any strategy")
        
        return (None, None, 0.0, LocatorStrategy.NOT_FOUND)
    
    def _strategy_ocr_exact(self, 
                           ocr_detections: List[Dict], 
                           target: str) -> Optional[Tuple]:
        """Strategy 1: Exact text match"""
        target_lower = target.lower().strip()
        
        for det in ocr_detections:
            if det['text'].lower().strip() == target_lower:
                if det['confidence'] >= self.ocr_exact_threshold:
                    x, y = det['center']
                    conf = det['confidence']
                    
                    if self.verbose:
                        print(f"   ✓ OCR Exact: '{det['text']}' at ({x}, {y}) [conf: {conf:.2f}]")
                    
                    return (x, y, conf, LocatorStrategy.OCR_EXACT)
        
        if self.verbose:
            print("   ⊗ OCR Exact: no match")
        
        return None
    
    def _strategy_ocr_fuzzy(self, 
                           ocr_detections: List[Dict], 
                           target: str) -> Optional[Tuple]:
        """Strategy 2: Fuzzy text match with improved normalization"""
        from fuzzywuzzy import fuzz
        
        best_match = None
        best_score = 0
        
        # Normalize target: lowercase, strip, remove extra whitespace
        target_norm = ' '.join(target.lower().strip().split())
        
        for det in ocr_detections:
            # Normalize detection text the same way
            det_text_norm = ' '.join(det['text'].lower().strip().split())
            
            # Try multiple matching strategies (use the best)
            score_ratio = fuzz.ratio(det_text_norm, target_norm) / 100.0
            score_partial = fuzz.partial_ratio(det_text_norm, target_norm) / 100.0
            score_token = fuzz.token_sort_ratio(det_text_norm, target_norm) / 100.0
            
            # Use the best score
            score = max(score_ratio, score_partial, score_token)
            
            if score > best_score:
                best_score = score
                best_match = det
        
        if best_match and best_score >= self.ocr_fuzzy_threshold:
            x, y = best_match['center']
            
            if self.verbose:
                print(f"   ✓ OCR Fuzzy: '{best_match['text']}' at ({x}, {y}) [similarity: {best_score:.2f}]")
            
            return (x, y, best_score, LocatorStrategy.OCR_FUZZY)
        
        if self.verbose:
            if best_match:
                print(f"   ⊗ OCR Fuzzy: best match '{best_match['text']}' score {best_score:.2f} < threshold {self.ocr_fuzzy_threshold}")
            else:
                print(f"   ⊗ OCR Fuzzy: no matches found")
        
        return None
    
    def _strategy_set_of_marks(self, 
                               screenshot: Image.Image,
                               ocr_detections: List[Dict], 
                               target: str) -> Optional[Tuple]:
        """Strategy 3: Set-of-Marks + Groq LLM"""
        try:
            # Create annotated screenshot
            annotated_img, element_map = self.som.create_annotated_screenshot(
                screenshot,
                ocr_detections,
                show_boxes=False,
                show_marks=True,
                min_confidence=0.6
            )
            
            if not element_map:
                if self.verbose:
                    print("   ⊗ Set-of-Marks: no elements to mark")
                return None
            
            # Create compact reference
            element_ref = self.som.create_compact_reference(element_map, max_elements=30)
            
            # Query Groq LLM
            mark_id = self.groq.find_element_mark(element_ref, target)
            
            if mark_id and mark_id in element_map:
                element = element_map[mark_id]
                x, y = element['center']
                
                if self.verbose:
                    print(f"   ✓ Set-of-Marks: Mark #{mark_id} ('{element['text']}') at ({x}, {y})")
                
                return (x, y, self.groq_confidence, LocatorStrategy.SET_OF_MARKS)
            
            if self.verbose:
                print(f"   ⊗ Set-of-Marks: Groq returned mark #{mark_id} (not found in map)")
            
        except Exception as e:
            if self.verbose:
                print(f"   ⊗ Set-of-Marks: Error: {e}")
        
        return None
    
    def _strategy_position_fallback(self, 
                                    norm_coords: Tuple[int, int]) -> Optional[Tuple]:
        """Strategy 4: Use normalized coordinates from recording"""
        x, y = self.normalizer.denormalize(norm_coords[0], norm_coords[1])
        
        if self.verbose:
            print(f"   ⚠️  Position Fallback: ({x}, {y}) from normalized {norm_coords}")
        
        return (x, y, self.position_confidence, LocatorStrategy.POSITION_FALLBACK)
    
    def find_multiple_elements(self,
                              screenshot: Image.Image,
                              targets: List[str]) -> Dict[str, Tuple]:
        """
        Find multiple elements at once (batch mode)
        
        Args:
            screenshot: Current screenshot
            targets: List of element descriptions
        
        Returns:
            {target: (x, y, confidence, strategy), ...}
        """
        results = {}
        
        # Run OCR once for all targets
        screenshot_np = np.array(screenshot)
        ocr_detections = self.ocr.detect_text_with_boxes(screenshot_np)
        
        for target in targets:
            result = self.locate_element(screenshot, target)
            results[target] = result
        
        return results


def test_locator():
    """Test multi-strategy locator"""
    import pyautogui
    
    print("=" * 70)
    print("Multi-Strategy Locator Test")
    print("=" * 70)
    print()
    
    # Initialize
    locator = MultiStrategyLocator(verbose=True)
    
    # Take screenshot
    print("\nCapturing screenshot...")
    screenshot = pyautogui.screenshot()
    
    # Test various search queries
    print("\n" + "=" * 70)
    print("Testing element location:")
    print("=" * 70)
    
    test_queries = [
        "File",           # Common menu item
        "Edit",           # Common menu item
        "Close",          # Common button
        "Finder",         # macOS dock app
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 70)
        
        x, y, confidence, strategy = locator.locate_element(screenshot, query)
        
        if x is not None:
            print(f"✅ FOUND at ({x}, {y})")
            print(f"   Strategy: {strategy.value}")
            print(f"   Confidence: {confidence:.0%}")
        else:
            print(f"❌ NOT FOUND")
    
    # Test with fallback coordinates
    print("\n" + "=" * 70)
    print("Testing with fallback coordinates:")
    print("=" * 70)
    
    print(f"\n🔍 Query: 'NonexistentElement'")
    print("-" * 70)
    
    x, y, confidence, strategy = locator.locate_element(
        screenshot,
        "NonexistentElement",
        fallback_normalized_coords=(500, 500)  # Center of screen
    )
    
    if x is not None:
        print(f"✅ Used fallback at ({x}, {y})")
        print(f"   Strategy: {strategy.value}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_locator()

