import os
import sys

# Add backend directory to sys.path so we can import app modules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from app.services.image_analysis import analyze_image_file
from app.services.material_classifier import FABRIC_CLASSIFIER, QUALITY_CLASSIFIER
from app.services.waste_classifier import WASTE_CLASSIFIER

def test_pipeline():
    print("--- ML Pipeline Verification ---")
    
    # 1. Check if models are loaded
    print(f"Fabric Classifier ML Model Loaded: {FABRIC_CLASSIFIER is not None}")
    print(f"Quality Classifier ML Model Loaded: {QUALITY_CLASSIFIER is not None}")
    print(f"Waste Classifier ML Model Loaded: {WASTE_CLASSIFIER is not None}")
    
    if not (FABRIC_CLASSIFIER and QUALITY_CLASSIFIER and WASTE_CLASSIFIER):
        print("[WARNING] One or more ML models failed to load. Falling back to rule-based classification.")
    else:
        print("[SUCCESS] All ML models loaded successfully.")

    # 2. Find a test image
    uploads_dir = os.path.join(BASE_DIR, "static", "uploads")
    if not os.path.exists(uploads_dir) or not os.listdir(uploads_dir):
        print("[ERROR] No images found in static/uploads/ to test the pipeline.")
        return
        
    test_image_name = os.listdir(uploads_dir)[0]
    test_image_path = os.path.join(uploads_dir, test_image_name)
    print(f"Testing with image: {test_image_path}")

    # 3. Run analysis
    try:
        results = analyze_image_file(test_image_path, sensitivity=0.5)
        print("\n[SUCCESS] Pipeline completed successfully!")
        
        # 4. Print results
        print("\n--- EXTRACTED FEATURES ---")
        for k, v in results["features"].items():
            print(f"  {k}: {v}")
            
        print("\n--- MATERIAL CLASSIFICATION ---")
        for k, v in results["material"].items():
            print(f"  {k}: {v}")
            
        print("\n--- WASTE CLASSIFICATION ---")
        for k, v in results["waste_classification"].items():
            print(f"  {k}: {v}")
            
        print("\n--- RECOMMENDATIONS ---")
        for rec in results["recommendations"]:
            print(f"  - {rec}")
            
    except Exception as e:
        print(f"\n[ERROR] Pipeline run failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
