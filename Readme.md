# 🚨 Sentry AI: Advanced Surveillance System

[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-v18+-green)](https://nodejs.org/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

Sentry AI is a **full-stack intelligent surveillance application** that uses deep learning models to analyze video streams in real-time, detect threats, and generate automated alerts and reports. It features a **modern web dashboard** for monitoring live feeds, reviewing past events, and managing reports.

---

## ✨ Key Features

<details>
<summary>📹 Multi-Source Video Input</summary>

- **Local Webcam:** Use your computer's built-in camera.
- **Network Stream:** Connect to any IP camera or phone camera using RTSP/HTTP protocols.
- **File Upload:** Process pre-recorded video files for batch analysis.

</details>

<details>
<summary>🤖 AI-Powered Analysis</summary>

- **Object Detection:** YOLOv8 model detects people, guns, knives, fires, masks, helmets.
- **Action Recognition:** I3D model classifies actions for context.
- **Severity Assessment:** Events classified automatically as **Normal**, **Suspicious**, or **Danger**.

</details>

<details>
<summary>📣 Automated Alerts & Reporting</summary>

- **Real-Time Telegram Alerts:** Sends annotated screenshots to Telegram when danger is detected.
- **LLM-Powered Summaries:** Generates human-readable summaries using a Large Language Model.
- **PDF Report Generation:** Creates detailed reports with key frame screenshots.

</details>

<details>
<summary>🖥️ Interactive Web Dashboard</summary>

- **Live Feed Monitoring:** View live annotated video in the browser.
- **Recent Alerts:** Real-time log of alerts.
- **Report Archive:** View, download, and delete past reports.

</details>

---

## 🛠️ Technology Stack

| Area      | Technology                                                                 |
|-----------|---------------------------------------------------------------------------|
| Frontend  | React (Vite), TypeScript, Tailwind CSS, Shadcn/ui, Axios                  |
| Backend   | Python, Flask, OpenCV, PyTorch, Ultralytics YOLOv8, I3D Model, threading  |
| DevOps    | concurrently (run frontend + backend with one command)                     |
| Database  | Flat-file JSON for persistent logging                                      |

---

## 📁 Project Structure



```bash
/
├── Sentry_AI_V2/       # Backend: Python, Flask, and AI models
│   ├── app.py
│   ├── models/
│   ├── detector/
│   └── ...
└── sentry-eye-live/    # Frontend: React, Vite, and UI components
    ├── src/
    ├── package.json
    └── ...

```
---

## 🚀 Getting Started

### Prerequisites
- Python (3.8+) and pip
- Node.js (v18+) and npm
- A YOLOv8 model file named `best.pt`

---

### 1. Backend Setup (Sentry_AI_V2)

First, set up the Python backend and its dependencies:

```bash
# Navigate to the backend folder
cd Sentry_AI_V2

# Create a Python virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install the required Python packages
pip install -r requirements.txt

# Place your YOLO model file in the 'models' directory:
# Sentry_AI_V2/models/best.pt
```

### 2. Frontend Setup (sentry-eye-live)
```bash
# Navigate to the frontend folder
cd sentry-eye-live

# Install the required Node.js packages
npm install
```
### 3. Running the Full Application
```bash
# From the frontend folder (sentry-eye-live)
npm run dev:all
```

## 📖 Usage
<details> <summary>💻 Local Webcam</summary> Click **Start Local Webcam** to begin analysis. </details> <details> <summary>🌐 Network Stream</summary> Enter RTSP or HTTP URL (e.g., `http://192.168.1.104:8080/video`) and click **Connect Network Stream**. </details> <details> <summary>📁 Upload Video</summary> Click **Upload Video**, select a file, then click **Analyze Video**. </details> <details> <summary>📝 Generate Reports</summary> While a camera is running, click **Generate Report** to create and send a PDF summary. </details> <details> <summary>📂 Past Reports</summary> Click **Past Reports** in the header to view, download, or delete previously generated reports. </details> ```
