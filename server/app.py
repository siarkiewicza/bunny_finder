from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import torch
import sys
import numpy as np
from PIL import Image
import time
from werkzeug.utils import secure_filename
from torchvision import transforms
import torchvision.transforms as transforms

# Define base project directory and paths
BASE_DIR = '/Users/Anthonyz/bunny_finder_clean'
MODEL_PATH = os.path.join(BASE_DIR, 'ml/models/yolov5/runs/train/exp19/weights/best.pt')
YOLO_PATH = os.path.join(BASE_DIR, 'ml/models/yolov5')

# Add YOLOv5 to path
sys.path.append(YOLO_PATH)

# Import YOLOv5 modules directly
from models.experimental import attempt_load
from utils.general import non_max_suppression
from utils.torch_utils import select_device

app = Flask(__name__)
CORS(app)

try:
    # Load YOLOv5 model directly
    device = select_device('')  # CPU
    model = attempt_load(MODEL_PATH, device=device)
    print(f"Successfully loaded model from: {MODEL_PATH}")
except Exception as e:
    print(f"Error loading model: {e}")
    raise

# Create uploads folder if it doesn't exist
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'server/uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/detect-batch', methods=['POST'])
def detect_batch():
    try:
        files = request.files.getlist('images')
        if not files:
            return jsonify({'error': 'No files uploaded', 'success': False}), 400

        print(f"Received batch of {len(files)} images")
        
        # Define image preprocessing
        preprocess = transforms.Compose([
            transforms.Resize((640, 640)),
            transforms.ToTensor(),
        ])
        
        # Process in batches of 8 (smaller batch size for better accuracy)
        BATCH_SIZE = 8
        results = []
        batch_tensors = []
        batch_filenames = []
        
        for idx, file in enumerate(files):
            filename = secure_filename(file.filename)
            print(f"Processing: {filename}")
            
            try:
                image = Image.open(file.stream)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                image_tensor = preprocess(image)
                batch_tensors.append(image_tensor)
                batch_filenames.append(filename)
                
                # Process batch when it's full or on last image
                if len(batch_tensors) == BATCH_SIZE or idx == len(files) - 1:
                    # Stack tensors and move to device
                    batch = torch.stack(batch_tensors).to(device)
                    
                    # Run inference on batch
                    with torch.no_grad():
                        predictions = model(batch)
                        predictions = predictions[0] if isinstance(predictions, tuple) else predictions
                    
                    # Process each result in the batch
                    for bidx, pred in enumerate(predictions):
                        # Adjust confidence threshold based on sensitivity
                        conf_thres = 0.3  # Lower threshold to catch more potential matches
                        pred = non_max_suppression(
                            pred.unsqueeze(0),
                            conf_thres=conf_thres,
                            iou_thres=0.45
                        )[0]
                        
                        detections = []
                        if len(pred):
                            for *xyxy, conf, cls in pred:
                                # Only include if confidence is high enough
                                if float(conf) > conf_thres:
                                    detections.append({
                                        'bbox': [float(x) for x in xyxy],
                                        'confidence': float(conf),
                                        'class': 'bunny'
                                    })
                                    print(f"Found bunny in {batch_filenames[bidx]} with confidence {float(conf)}")
                        
                        results.append({
                            'filename': batch_filenames[bidx],
                            'detections': detections,
                            'has_bunny': len(detections) > 0
                        })
                    
                    # Clear batch
                    batch_tensors = []
                    batch_filenames = []
                    
                    # Report progress
                    print(f"Processed {len(results)}/{len(files)} images")
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                results.append({
                    'filename': filename,
                    'error': str(e),
                    'has_bunny': False
                })

        print(f"Batch processing complete. Found bunnies in {sum(1 for r in results if r.get('has_bunny', False))} images")
        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results),
            'bunnies_found': sum(1 for r in results if r.get('has_bunny', False))
        })

    except Exception as e:
        print(f"Error processing batch: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/detect', methods=['POST'])
def detect_rabbit():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Save uploaded file temporarily
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        print(f"Processing single image: {file.filename}")

        # Run inference
        results = model(filepath)
        
        # Process results
        detections = []
        if len(results.pred[0]) > 0:
            for *xyxy, conf, cls in results.pred[0]:
                conf = float(conf)
                print(f"Detection confidence: {conf}")
                if conf > 0.3:  # Lowered threshold for testing
                    detections.append({
                        'confidence': conf,
                        'class': results.names[int(cls)]
                    })

        has_bunny = len(detections) > 0
        print(f"Single image result: {'Bunny detected' if has_bunny else 'No bunny'}")

        return jsonify({
            'success': True,
            'has_bunny': has_bunny,
            'detections': detections
        })

    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

    finally:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'model_path': MODEL_PATH
    })

if __name__ == '__main__':
    print(f"Starting server with model: {MODEL_PATH}")
    print("Available routes:")
    print(" - POST /detect-batch : Detect rabbits in batch of images")
    print(" - POST /detect : Detect rabbits in single image")
    print(" - GET /health : Check server status")
    
    app.run(debug=True, port=5001)