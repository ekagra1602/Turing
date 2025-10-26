"""
Test Workflow Templates

Verify that hardcoded workflow templates are properly loaded and can be executed
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from workflow_templates import (
    get_all_templates,
    get_template,
    list_available_templates,
    merge_templates_with_learned
)
from gemini_workflow_executor import GeminiWorkflowExecutor
from visual_memory import VisualWorkflowMemory


def test_template_loading():
    """Test that templates load correctly"""
    print("=" * 70)
    print("TEST 1: Template Loading")
    print("=" * 70)
    
    templates = get_all_templates()
    print(f"✓ Loaded {len(templates)} templates")
    
    available = list_available_templates()
    print(f"✓ Available templates:")
    for intention in available:
        print(f"  • {intention}")
    
    print("\n✅ Template loading test passed!\n")


def test_template_structure():
    """Test that template structure is correct"""
    print("=" * 70)
    print("TEST 2: Template Structure")
    print("=" * 70)
    
    # Test the "send email via gmail" template
    email_template = get_template("send email via gmail")
    
    if not email_template:
        print("❌ Email template not found!")
        return False
    
    print(f"✓ Email template has {len(email_template)} steps")
    
    # Verify each step has required fields
    required_fields = ['step_number', 'semantic_type', 'description']
    for i, step in enumerate(email_template, 1):
        for field in required_fields:
            if field not in step:
                print(f"❌ Step {i} missing required field: {field}")
                return False
    
    print("✓ All steps have required fields")
    
    # Show first few steps
    print("\nFirst 5 steps:")
    for step in email_template[:5]:
        print(f"  {step['step_number']}. [{step['semantic_type']}] {step['description']}")
    
    print("\n✅ Template structure test passed!\n")
    return True


def test_executor_integration():
    """Test that executor properly loads templates"""
    print("=" * 70)
    print("TEST 3: Executor Integration")
    print("=" * 70)
    
    try:
        # Initialize executor
        memory = VisualWorkflowMemory()
        executor = GeminiWorkflowExecutor(memory=memory, verbose=False)
        
        # Check if templates are loaded
        template_intentions = list_available_templates()
        
        for intention in template_intentions:
            if intention in executor.workflows_by_intention:
                print(f"✓ Template loaded: {intention}")
            else:
                print(f"❌ Template not loaded: {intention}")
                return False
        
        print(f"\n✓ Total workflows in executor: {len(executor.workflows_by_intention)}")
        
        print("\n✅ Executor integration test passed!\n")
        return True
        
    except ValueError as e:
        if "GOOGLE_API_KEY" in str(e):
            print("⚠️  Skipping executor test - GOOGLE_API_KEY not set")
            print("   (This is expected in test environment)")
            print("\n✓ Test skipped (not a failure)\n")
            return True
        else:
            raise


def test_template_retrieval():
    """Test getting workflows by intention"""
    print("=" * 70)
    print("TEST 4: Template Retrieval")
    print("=" * 70)
    
    try:
        memory = VisualWorkflowMemory()
        executor = GeminiWorkflowExecutor(memory=memory, verbose=False)
        
        # Test exact match
        actions = executor.get_workflow_by_intention("send email via gmail")
        if actions:
            print(f"✓ Exact match found: 'send email via gmail' ({len(actions)} steps)")
        else:
            print("❌ Exact match failed")
            return False
        
        # Test fuzzy match
        actions = executor.get_workflow_by_intention("send gmail email")
        if actions:
            print(f"✓ Fuzzy match found: 'send gmail email' ({len(actions)} steps)")
        else:
            print("⚠️  Fuzzy match failed (may be expected)")
        
        # Test new tab template
        actions = executor.get_workflow_by_intention("open new tab")
        if actions:
            print(f"✓ Found: 'open new tab' ({len(actions)} steps)")
        else:
            print("❌ 'open new tab' not found")
            return False
        
        print("\n✅ Template retrieval test passed!\n")
        return True
        
    except ValueError as e:
        if "GOOGLE_API_KEY" in str(e):
            print("⚠️  Skipping retrieval test - GOOGLE_API_KEY not set")
            print("   (This is expected in test environment)")
            print("\n✓ Test skipped (not a failure)\n")
            return True
        else:
            raise


def test_parameter_substitution():
    """Test that parameters can be substituted"""
    print("=" * 70)
    print("TEST 5: Parameter Substitution")
    print("=" * 70)
    
    # Get email template
    email_template = get_template("send email via gmail")
    
    # Find parameterizable steps
    param_steps = [s for s in email_template if s.get('is_parameterizable')]
    print(f"✓ Found {len(param_steps)} parameterizable steps:")
    
    for step in param_steps:
        param_name = step.get('parameter_name')
        placeholder = step.get('value')
        print(f"  • Step {step['step_number']}: {param_name} = '{placeholder}'")
    
    # Verify parameter format
    expected_params = ['recipient_email', 'email_subject', 'email_body']
    found_params = [s.get('parameter_name') for s in param_steps]
    
    for expected in expected_params:
        if expected in found_params:
            print(f"✓ Parameter '{expected}' found")
        else:
            print(f"❌ Parameter '{expected}' missing")
            return False
    
    print("\n✅ Parameter substitution test passed!\n")
    return True


def show_template_summary():
    """Show summary of all templates"""
    print("=" * 70)
    print("TEMPLATE SUMMARY")
    print("=" * 70)
    
    templates = get_all_templates()
    
    print(f"\nTotal Templates: {len(templates)}\n")
    
    for intention, actions in templates.items():
        param_count = sum(1 for a in actions if a.get('is_parameterizable'))
        print(f"📋 {intention}")
        print(f"   Steps: {len(actions)} | Parameters: {param_count}")
        
        # Show parameter names
        if param_count > 0:
            params = [a.get('parameter_name') for a in actions if a.get('is_parameterizable')]
            print(f"   Params: {', '.join(params)}")
        print()


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("WORKFLOW TEMPLATES TEST SUITE")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Run tests
    try:
        test_template_loading()
        all_passed &= test_template_structure()
        all_passed &= test_executor_integration()
        all_passed &= test_template_retrieval()
        all_passed &= test_parameter_substitution()
        
        show_template_summary()
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Final result
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)
    print()
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

