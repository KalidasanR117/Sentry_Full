import os
import telegram

from dotenv import load_dotenv

# Load .env variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialize bot
bot = telegram.Bot(token=BOT_TOKEN)

# -------------------- Send instant image alert --------------------
def send_alert(frame, severity):
    """
    Sends a single frame as a Telegram alert.
    
    Args:
        frame: OpenCV image (BGR)
        severity: string, e.g., 'danger' or 'suspicious'
    """
    try:
        import cv2
        from io import BytesIO

        # Convert frame to JPEG bytes
        _, buffer = cv2.imencode(".jpg", frame)
        image_bytes = BytesIO(buffer.tobytes())
        image_bytes.name = f"{severity}_alert.jpg"

        caption = f"Mini SentryAI+ Alert: {severity.upper()}"

        bot.send_photo(chat_id=CHAT_ID, photo=image_bytes, caption=caption)
        print(f"[INFO] Telegram {severity} alert sent.")
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram alert: {e}")

# -------------------- Send PDF with summary --------------------
def send_pdf_with_summary(pdf_path, summary_text=None):
    """
    Sends the final PDF report via Telegram.
    If the summary is too long, split into multiple messages.
    """
    try:
        # ------------------ Send summary in chunks ------------------
        if summary_text:
            max_len = 1000  # Telegram safe limit
            chunks = [summary_text[i:i+max_len] for i in range(0, len(summary_text), max_len)]
            for idx, chunk in enumerate(chunks, 1):
                bot.send_message(chat_id=CHAT_ID, text=f"Summary part {idx}/{len(chunks)}:\n{chunk}")

        # ------------------ Send PDF ------------------
        caption = "Mini SentryAI+ Final Report"
        with open(pdf_path, "rb") as pdf_file:
            bot.send_document(chat_id=CHAT_ID, document=pdf_file, caption=caption)

        print("[INFO] Telegram PDF report sent.")
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram PDF: {e}")
# bot.send_message(chat_id=CHAT_ID, text="Hello from Mini SentryAI+")
