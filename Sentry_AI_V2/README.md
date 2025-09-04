# Mini SentryAI+ 🚨

![Python](https://img.shields.io/badge/python-3.10+-blue)


Mini SentryAI+ is a modular AI-powered surveillance system that detects **dangerous** and **suspicious activities**, sends real-time Telegram alerts, and generates daily PDF reports with annotated screenshots and LLM-generated summaries.

---

## ⚡ Features

- **YOLO Object Detection:** Guns, knives, helmets, masks, etc.
- **YOLO Violence Detection:** Violence,Non-Violence.
- **Severity Classification:** Danger / Suspicious / Normal.
- **Event Logging:** JSON logs with timestamps.
- **Telegram Alerts:** Images + severity notifications.
- **PDF Reports:** Annotated screenshots + AI summaries.
- **Modular & Extendable:** Separate modules for detection, logging, alerting, LLM, and reports.

---

## 🚀 Quick Start

### Clone & Setup

```bash
git clone https://github.com/KalidasanR117/Sentry_AI_V2.git
cd Sentry_AI_V2
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

```

Configure API Keys

Create a .env file:

```bash
BOT_TOKEN=<your_telegram_bot_token>
CHAT_ID=<your_telegram_chat_id>
GEMINI_API_KEY=<your_gemini_api_key>
```

Run

Video Analysis:

```bash
python main.py
```

Real-Time Camera:

Set VIDEO_SOURCE = 0 in main.py.
```bash
sentry_ai/
│
├── models/               # YOLO weights
├── detector/             # YOLO, severity selector
├── input/                # Camera/video stream
├── alerts/               # Telegram bot integration
├── reports/              # PDF report generator
├── database/             # Event logger
├── llm/                  # LLM summary generator
├── main.py
└── .env                  # API keys
```


🛠 Configuration

 - **ALERT_COOLDOWN → Time between danger alerts** (seconds)

 - **SCREENSHOT_DIR → Folder for annotated screenshots** 

 - **LOG_DIR → JSON logs directory** 


📈 Future Improvements

- **Face recognition for identity tracking.**

- **Web UI for live monitoring.** 

- **Multi-camera support.** 

- **GPU acceleration for faster inference.** 
