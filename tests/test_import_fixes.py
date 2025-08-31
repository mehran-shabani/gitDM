"""Test to verify all imports are fixed properly."""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all fixed imports work correctly."""
    errors = []
    
    # Test intelligence app import
    try:
        from intelligence import admin as app_admin
        print("✓ intelligence.admin import successful")
    except ImportError as e:
        errors.append(f"✗ intelligence.admin import failed: {e}")
    
    # Test gateway.urls import
    try:
        from gateway import urls
        print("✓ gateway.urls import successful")
    except ImportError as e:
        errors.append(f"✗ gateway.urls import failed: {e}")
    
    # Test model imports
    try:
        from gitdm.models import PatientProfile
        print("✓ gitdm.models.PatientProfile import successful")
    except ImportError as e:
        errors.append(f"✗ gitdm.models.PatientProfile import failed: {e}")
    
    try:
        from encounters.models import Encounter
        print("✓ encounters.models.Encounter import successful")
    except ImportError as e:
        errors.append(f"✗ encounters.models.Encounter import failed: {e}")
    
    try:
        from intelligence.models import AISummary
        print("✓ intelligence.models.AISummary import successful")
    except ImportError as e:
        errors.append(f"✗ intelligence.models.AISummary import failed: {e}")
    
    try:
        from versioning.models import RecordVersion
        print("✓ versioning.models.RecordVersion import successful")
    except ImportError as e:
        errors.append(f"✗ versioning.models.RecordVersion import failed: {e}")
    
    if errors:
        print("\nErrors found:")
        for error in errors:
            print(error)
        return False
    else:
        print("\nAll imports successful!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)