import os
import re
import logging
from io import BytesIO

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ReportLab Imports (Vector Based)
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Gemini
import google.generativeai as genai


# =========================
# CONFIGURATION
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

logging.basicConfig(level=logging.INFO)


# =========================
# PDF STYLES (VECTOR SAFE)
# =========================

heading_style = ParagraphStyle(
    name="HeadingStyle",
    fontName="Helvetica-Bold",
    fontSize=16,
    spaceAfter=8,
)

body_style = ParagraphStyle(
    name="BodyStyle",
    fontName="Helvetica",
    fontSize=12,
    leading=16,  # optimized spacing
    spaceAfter=6,
)


# =========================
# UTIL FUNCTIONS
# =========================

def is_heading(line):
    """
    Detect heading dynamically:
    - Fully CAPS
    - Short line (< 60 chars)
    """
    if len(line.strip()) < 60:
        if line.strip().isupper():
            return True
    return False


def complete_text_with_gemini(text):
    """
    Complete project text intelligently.
    """
    model = genai.GenerativeModel("gemini-pro")

    prompt = f"""
    You are an expert academic project writer.
    Complete the following project content professionally.
    Do not add unnecessary fluff.
    Keep headings structured.

    Text:
    {text}
    """

    response = model.generate_content(prompt)
    return response.text


def detect_table_data(text):
    """
    Detect if user provided structured table data.
    Example:
    Name, Age, Class
    Ram, 14, 8
    """
    lines = text.strip().split("\n")
    table_data = []

    for line in lines:
        if "," in line:
            row = [cell.strip() for cell in line.split(",")]
            table_data.append(row)

    if len(table_data) >= 2:
        return table_data

    return None


def generate_pdf(content):
    """
    Create vector-based PDF using ReportLab Platypus.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    elements = []

    table_data = detect_table_data(content)

    # =========================
    # TABLE MODE
    # =========================
    if table_data:
        table = Table(table_data, hAlign='LEFT')

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))

        elements.append(table)

    # =========================
    # NORMAL TEXT MODE
    # =========================
    else:
        lines = content.split("\n")

        for line in lines:
            if not line.strip():
                elements.append(Spacer(1, 8))
                continue

            if is_heading(line):
                elements.append(Paragraph(line.strip(), heading_style))
            else:
                elements.append(Paragraph(line.strip(), body_style))

    doc.build(elements)
    buffer.seek(0)

    return buffer


# =========================
# TELEGRAM HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me your project text.\n\n"
        "I will:\n"
        "• Complete it (if needed)\n"
        "• Format headings automatically\n"
        "• Generate Crystal Clear PDF\n"
        "• Create Tables if detected"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    await update.message.reply_text("Processing your project...")

    # Step 1: Complete content
    completed_text = complete_text_with_gemini(user_text)

    # Step 2: Generate PDF
    pdf_buffer = generate_pdf(completed_text)

    await update.message.reply_document(
        document=pdf_buffer,
        filename="Professional_Project.pdf",
    )


# =========================
# MAIN FUNCTION
# =========================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
