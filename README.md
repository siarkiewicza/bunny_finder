Bunny Finder
An Electron application that uses YOLOv5 to detect rabbits in photos.

![Bunny Finder Interface](screenshots/main-interface.png)

Features
Batch processing of image folders
Custom-trained YOLOv5 model for rabbit detection
Adjustable detection sensitivity
Progress tracking and results display

Tech Stack
Frontend: React + Electron
Backend: Flask + Python
ML: YOLOv5 with PyTorch

Setup
Prerequisites
Python 3.10+
Node.js 16+
npm or yarn

Installation
Install Python dependencies:
cd server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Install Node dependencies:
cd app/bunny-finder
npm install
Running the Application
Start the Flask backend:
cd server
source venv/bin/activate
python app.py
Start the Electron application:
cd app/bunny-finder
npm start

Usage
Drop a folder containing photos into the "photos folder" area
Select an output folder for detected bunny images
Adjust detection sensitivity if needed
Click START to begin processing
Project Structure
bunny_finder/
├── app/                    # Electron frontend
│   └── bunny-finder/
│       ├── src/
│       │   ├── renderer/  # React components
│       │   └── main/      # Electron main process
├── server/                # Flask backend
│   ├── app.py            # Main server file
│   └── requirements.txt   # Python dependencies
└── ml/                    # ML model files
    └── models/
        └── yolov5/        # YOLOv5 model
License
MIT License
