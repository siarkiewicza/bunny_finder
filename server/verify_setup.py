import os
import sys
from pathlib import Path

def check_path(path, description):
    exists = os.path.exists(path)
    print(f"✓ {description}: {path}" if exists else f"✗ Missing {description}: {path}")
    return exists

def verify_project_structure():
    # Base directories
    BASE_DIR = '/Users/Anthonyz/bunny_finder_clean'
    
    required_files = [
        # Server files
        (f"{BASE_DIR}/server/app.py", "Flask server"),
        (f"{BASE_DIR}/server/requirements.txt", "Python requirements"),
        
        # Frontend files
        (f"{BASE_DIR}/app/bunny-finder/src/renderer/App.jsx", "React frontend"),
        (f"{BASE_DIR}/app/bunny-finder/vite.config.js", "Vite config"),
        
        # ML model files
        (f"{BASE_DIR}/ml/models/yolov5/models/__init__.py", "YOLOv5 models init"),
        (f"{BASE_DIR}/ml/models/yolov5/utils/__init__.py", "YOLOv5 utils init"),
        (f"{BASE_DIR}/ml/models/yolov5/hubconf.py", "YOLOv5 hub config"),
        (f"{BASE_DIR}/ml/models/yolov5/runs/train/exp19/weights/best.pt", "Model weights"),
        
        # Required directories
        (f"{BASE_DIR}/server/uploads", "Upload directory"),
    ]
    
    all_exist = True
    print("\nChecking project structure...")
    for path, desc in required_files:
        if not check_path(path, desc):
            all_exist = False
    
    # Check if YOLOv5 directories have content
    yolo_dirs = [
        (f"{BASE_DIR}/ml/models/yolov5/models", "YOLOv5 model files"),
        (f"{BASE_DIR}/ml/models/yolov5/utils", "YOLOv5 utility files")
    ]
    
    print("\nChecking YOLOv5 directories...")
    for dir_path, desc in yolo_dirs:
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            print(f"✓ {desc} contains {len(files)} files")
        else:
            print(f"✗ Missing {desc}")
            all_exist = False
    
    print("\nVerifying virtual environment...")
    try:
        import torch
        import flask
        import ultralytics
        print("✓ Key Python packages are installed")
    except ImportError as e:
        print(f"✗ Missing Python package: {e}")
        all_exist = False
    
    print("\nSummary:")
    if all_exist:
        print("✅ All required files and directories are present")
    else:
        print("❌ Some required files or directories are missing")

if __name__ == "__main__":
    verify_project_structure() 