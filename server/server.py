from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from ultralytics import YOLO
import torch
import numpy as np
from PIL import Image
import time

# Define base directory and model paths
BASE_DIR = '/Users/Anthonyz/bunny_finder_clean'
MODEL_PATH = os.path.join(BASE_DIR, 'ml/models/yolov5/runs/train/exp19/weights/best.pt')

app = Flask(__name__)
CORS(app)

try:
    # Load YOLOv5 model using ultralytics
    model = YOLO(MODEL_PATH)
    print(f"Successfully loaded model from: {MODEL_PATH}")
except Exception as e:
    print(f"Error loading model: {e}")
    raise

# Create uploads folder if it doesn't exist
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'server/uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/detect-batch', methods=['POST'])
def detect_rabbits_batch():
    if 'images' not in request.files:
        print("No images in request")
        return jsonify({'error': 'No images provided'}), 400
    
    files = request.files.getlist('images')
    print(f"Received batch of {len(files)} images")
    results = []
    
    try:
        batch_images = []
        filepaths = []
        
        # Save and prepare images
        for file in files:
            if file.filename:
                filepath = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(filepath)
                filepaths.append(filepath)
                batch_images.append(filepath)
                print(f"Saved image: {file.filename}")
        
        if not batch_images:
            print("No valid images in batch")
            return jsonify({'error': 'No valid images in batch'}), 400
        
        # Run batch inference
        print("Running model inference...")
        batch_results = model(batch_images)
        
        # Process results
        for idx, result in enumerate(batch_results):
            filename = os.path.basename(filepaths[idx])
            detections = []
            
            if len(result.boxes) > 0:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    print(f"Image {filename}: Confidence = {conf}")
                    if conf > 0.3:  # Lowered threshold for testing
                        detections.append({
                            'confidence': conf,
                            'class': result.names[int(box.cls[0])]
                        })
            
            has_bunny = len(detections) > 0
            print(f"Image {filename}: {'Bunny detected' if has_bunny else 'No bunny'}")
            
            results.append({
                'filename': filename,
                'detections': detections,
                'has_bunny': has_bunny
            })
        
        print(f"Batch processing complete. Found {sum(1 for r in results if r['has_bunny'])} bunnies")
        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        print(f"Error processing batch: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

    finally:
        # Clean up
        for filepath in filepaths:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass

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
        if len(results[0].boxes) > 0:
            for box in results[0].boxes:
                conf = float(box.conf[0])
                print(f"Detection confidence: {conf}")
                if conf > 0.3:  # Lowered threshold for testing
                    detections.append({
                        'confidence': conf,
                        'class': results[0].names[int(box.cls[0])]
                    })

        has_bunny = len(detections) > 0
        print(f"Single image result: {'Bunny detected' if has_bunny else 'No bunny'}")

        return jsonify({
            'success': True,
            'has_bunny': has_bunny,
            'detections': detections
        })

    except Exception as e:
        print(f"Error processing single image: {e}")
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
    print(" - POST /detect : Detect rabbits in uploaded image")
    print(" - GET /health : Check server status")
    
    app.run(debug=True, port=5001) 