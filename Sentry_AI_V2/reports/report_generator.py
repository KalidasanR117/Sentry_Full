import os
from fpdf import FPDF
from datetime import datetime
from PIL import Image

# -------------------- PDF Report Generator with Patterns & Legend --------------------
class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, "Mini SentryAI+ Report", 0, 1, "C")
        self.set_line_width(0.5)
        self.line(10, 15, 200, 15)
        self.ln(5)
        self._draw_background_stripes()

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def _draw_background_stripes(self):
        self.set_draw_color(220, 220, 220)
        step = 10
        w = int(self.w)
        h = int(self.h)
        for x in range(-h, w, step):
            self.line(x, 0, x + h, h)


# -------------------- Main PDF Generation Function --------------------
def generate_pdf_report(event_buffer, summary_text, output_path):
    """
    Generates a PDF report for Mini SentryAI+ events.

    Args:
        event_buffer (list): List of dicts with keys:
                             'frame', 'yolo', 'i3d', 'final', 'screenshot'
        summary_text (str): LLM-generated summary of events
        output_path (str): Path to save the PDF
    """
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)

    # -------------------- Cover Page --------------------
    pdf.add_page()
    pdf.set_font("Arial", "B", 24)
    pdf.set_text_color(0, 70, 140)
    pdf.cell(0, 40, "Mini SentryAI+ Report", 0, 1, "C")
    pdf.set_font("Arial", "", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, "C")
    pdf.ln(10)

    # -------------------- Legend Box --------------------
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Severity Legend:", ln=True)
    severity_colors = {"danger": (255,0,0), "suspicious": (255,165,0), "normal": (0,128,0)}
    for sev, color in severity_colors.items():
        pdf.set_fill_color(*color)
        pdf.cell(40, 8, sev.capitalize(), ln=True, fill=True)
    pdf.ln(5)

    # -------------------- Summary Page --------------------
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "LLM Summary", 0, 1)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, summary_text)
    pdf.ln(5)

    # -------------------- Event Pages --------------------
    for event in event_buffer:
        pdf.add_page()

        # Event box with light color based on severity
        color_map_light = {"danger": (255,200,200), "suspicious": (255,245,200), "normal": (200,255,200)}
        pdf.set_fill_color(*color_map_light.get(event["final"], (240,240,240)))
        pdf.rect(10, pdf.get_y(), 190, 50, "FD")
        pdf.ln(2)

        # Event header
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Event Frame: {event['frame']}", ln=True)
        pdf.ln(2)

        # Event info
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"YOLO Detection: {event['yolo']}", ln=True)
        pdf.cell(0, 8, f"I3D Prediction: {event['i3d']}", ln=True)
        severity_color = {"danger": (255,0,0), "suspicious": (255,165,0), "normal": (0,128,0)}
        pdf.set_text_color(*severity_color.get(event["final"], (0,0,0)))
        pdf.cell(0, 8, f"Final Severity: {event['final']}", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        # -------------------- Screenshot --------------------
        if os.path.exists(event["screenshot"]):
            img_path = event["screenshot"]
            img = Image.open(img_path)
            img_w, img_h = img.size

            # Max page width and remaining height
            max_w = 180
            remaining_h = pdf.h - pdf.get_y() - pdf.b_margin

            scale = min(max_w / img_w, remaining_h / img_h)
            new_w = img_w * scale
            new_h = img_h * scale

            pdf.image(img_path, w=new_w, h=new_h)
        else:
            pdf.cell(0, 8, "Screenshot not found.", ln=True)

    # -------------------- Save PDF --------------------
    pdf.output(output_path)
