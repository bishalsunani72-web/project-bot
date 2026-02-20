import os
import re
import logging
from io import BytesIO
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ReportLab (Vector Based)
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ==========================
# CONFIG
# ==========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# ==========================
# STYLES (VECTOR SHARP)
# ==========================

heading_style = ParagraphStyle(
    name="HeadingStyle",
    fontName="Helvetica-Bold",
    fontSize=16,
    spaceAfter=10,
)

body_style = ParagraphStyle(
    name="BodyStyle",
    fontName="Helvetica",
    fontSize=12,
    leading=16,
    spaceAfter=6,
)

# ==========================
# SMART HEADING DETECTION
# ==========================

def is_heading(line):
    line = line.strip()

    # Rule 1: ALL CAPS
    if line.isupper() and len(line) < 80:
        return True

    # Rule 2: Short line without period
    if len(line) < 50 and not line.endswith("."):
        return True

    return False


# ==========================
# TABLE DETECTION
# ==========================

def detect_table_block(text):
    lines = text.split("\n")
    table_data = []

    for line in lines:
        if "," in line:
            row = [cell.strip() for cell in line.split(",")]
            table_data.append(row)

    if len(table_data) >= 2:
        return table_data

    return None


# ==========================
# PAGE NUMBER FUNCTION
# ==========================

def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"{page_num}"
    canvas.setFont("Helvetica", 10)
    canvas.drawRightString(580, 20, text)


# ==========================
# PDF GENERATOR
# ==========================

def generate_pdf(content):
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

    # Auto Cover Page
    elements.append(Paragraph("PROJECT REPORT", heading_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y')}", body_style))
    elements.append(PageBreak())

    table_data = detect_table_block(content)

    # TABLE MODE
    if table_data:
        table = Table(table_data, hAlign="LEFT")

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))

        elements.append(table)

    # NORMAL TEXT MODE
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

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    buffer.seek(0)
    return buffer


# ==========================
# TELEGRAM HANDLERS
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📄 Send your project text.\n\n"
        "Features:\n"
        "• Crystal Clear Vector PDF\n"
        "• Auto Heading Detection\n"
        "• Auto Cover Page\n"
        "• Professional Tables\n"
        "• Page Numbers\n"
        "\nNo API needed. Fully Free."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    await update.message.reply_text("Generating Professional PDF...")

    pdf_buffer = generate_pdf(user_text)

    await update.message.reply_document(
        document=pdf_buffer,
        filename="Professional_Project.pdf",
    )


# ==========================
# MAIN
# ==========================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
