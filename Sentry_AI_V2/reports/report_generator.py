import os
from fpdf import FPDF, XPos, YPos
from datetime import datetime
from PIL import Image

# ===================================================================
# Final Professional PDF Report Generator for Sentry AI
#
# This definitive version features a complete visual overhaul and is
# fully self-contained. It now uses a robust method to find the
# cover image, requiring NO changes to app.py.
# ===================================================================

class PDFReport(FPDF):
    """ A class to create a final, polished, and branded PDF report. """

    # --- Color Palette (Matching your cover design) ---
    COLOR_GOLD = (212, 175, 55)
    COLOR_CHARCOAL = (34, 34, 34)
    COLOR_COVER_BG = (24, 24, 24)
    COLOR_WHITE = (255, 255, 255)
    COLOR_LIGHT_GREY_TEXT = (200, 200, 200)
    COLOR_GREY_BORDER = (80, 80, 80)

    def header(self):
        if self.page_no() == 1: return # No header on the cover page
        self.set_font("Helvetica", "", 9)
        self.set_text_color(150)
        self.cell(0, 10, "Sentry AI Surveillance Report", 0, 0, "L")
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "R")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Sentry AI Automated Report | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 0, "C")

    def add_page(self, orientation="", format="", same=False):
        """ Override add_page to automatically add a dark background. """
        super().add_page(orientation=orientation, format=format, same=same)
        if self.page_no() > 1:
            self.set_fill_color(*self.COLOR_CHARCOAL)
            self.rect(0, 0, self.w, self.h, 'F')

    def add_cover_page(self, cover_image_path):
        """ Creates a cover page that preserves the image's aspect ratio on a dark background. """
        super().add_page()
        self.set_fill_color(*self.COLOR_COVER_BG)
        self.rect(0, 0, self.w, self.h, 'F')
        
        if cover_image_path and os.path.exists(cover_image_path):
            try:
                img = Image.open(cover_image_path)
                img_w, img_h = img.size
                page_w, page_h = self.w, self.h
                scale = min(page_w / img_w, page_h / img_h)
                new_w, new_h = img_w * scale, img_h * scale
                x = (page_w - new_w) / 2
                y = (page_h - new_h) / 2
                self.image(cover_image_path, x=x, y=y, w=new_w, h=new_h)
            except Exception as e:
                print(f"!!! ERROR: Could not process cover image: {e}")
        else:
            self.set_y(self.h / 2 - 10)
            self.set_font("Helvetica", "B", 24)
            self.set_text_color(*self.COLOR_WHITE)
            self.cell(0, 10, "Sentry AI Report", 0, 1, "C")
            self.set_font("Helvetica", "", 12)
            self.cell(0, 10, "(Cover image not found)", 0, 1, "C")


    def add_summary_page(self, summary_text, event_buffer):
        self.add_page()
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*self.COLOR_WHITE)
        self.cell(0, 15, "Executive Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*self.COLOR_GOLD)
        self.set_line_width(0.8)
        self.line(self.get_x(), self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(10)
        
        self.set_font("Helvetica", "", 12)
        self.set_text_color(*self.COLOR_LIGHT_GREY_TEXT)
        self.multi_cell(0, 8, summary_text)
        self.ln(15)

        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*self.COLOR_WHITE)
        self.cell(0, 10, "Key Findings", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.set_font("Helvetica", "", 11)
        danger_events = len([e for e in event_buffer if e['final'] == 'danger'])
        suspicious_events = len([e for e in event_buffer if e['final'] == 'suspicious'])
        
        self.cell(0, 8, f"- Total Significant Events Detected: {len(event_buffer)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 8, f"- Danger-Level Incidents: {danger_events}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 8, f"- Suspicious-Level Observations: {suspicious_events}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def add_event_details(self, event):
        self.add_page()
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*self.COLOR_WHITE)
        self.cell(0, 10, f"Event Details - Frame {event.get('frame', 'N/A')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)
        
        page_width = self.w - self.l_margin - self.r_margin
        col1_width = 50
        col2_width = page_width - col1_width
        self.set_draw_color(*self.COLOR_GREY_BORDER)
        
        self.set_font("Helvetica", "B", 11)
        self.cell(col1_width, 8, "Detection Type", border=1)
        self.set_font("Helvetica", "", 11)
        self.multi_cell(col2_width, 8, "Details", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.set_font("Helvetica", "B", 11)
        self.cell(col1_width, 8, "Objects Detected:", border=1)
        self.set_font("Helvetica", "", 11)
        self.multi_cell(col2_width, 8, event.get('yolo', "None"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font("Helvetica", "B", 11)
        self.cell(col1_width, 8, "Violence Detected:", border=1)
        self.set_font("Helvetica", "", 11)
        self.multi_cell(col2_width, 8, event.get('violence', "None"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.set_font("Helvetica", "B", 11)
        self.cell(col1_width, 8, "Final Severity:", border=1)
        
        severity = event.get('final', 'normal')
        if severity == 'danger': self.set_text_color(220, 50, 50)
        elif severity == 'suspicious': self.set_text_color(*self.COLOR_GOLD)
        else: self.set_text_color(150, 255, 150) # Light Green
        
        self.set_font("Helvetica", "B", 11)
        self.multi_cell(col2_width, 8, severity.capitalize(), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*self.COLOR_LIGHT_GREY_TEXT)
        self.ln(10)

        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Annotated Screenshot:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        screenshot_path = event.get("screenshot")
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                self.image(screenshot_path, x=self.get_x(), y=self.get_y(), w=self.w - self.l_margin - self.r_margin)
            except Exception as e:
                self.set_font("Helvetica", "I", 10)
                self.cell(0, 8, f"Could not load screenshot: {e}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.set_font("Helvetica", "I", 10)
            self.cell(0, 8, "Screenshot not found or path is invalid.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# -------------------- Main PDF Generation Function --------------------
def generate_pdf_report(event_buffer, summary_text, output_path):
    """ Generates a professional PDF report for Sentry AI events. """
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # ✅ FIXED: Use a robust method to find the cover image.
    # Always resolve relative to app.py (the entry point in project root)
    # Always resolve relative to the project root (where app.py lives)
    # Force project root to where app.py is
    project_root = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))  
    cover_image_path = os.path.join(project_root, "cover.png")
    print("Looking for cover image at:", cover_image_path)
    
    pdf.add_cover_page(cover_image_path)
    pdf.add_summary_page(summary_text, event_buffer)
    
    if event_buffer:
        for event in event_buffer:
            pdf.add_event_details(event)
    
    try:
        pdf.output(output_path)
        print(f"PDF Report generated successfully at {output_path}")
    except Exception as e:
        print(f"!!! ERROR: Failed to generate PDF report: {e}")

