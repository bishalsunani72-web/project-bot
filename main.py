import os
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

# ReportLab
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

# ==========================
# CONFIG
# ==========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# ==========================
# STYLES
# ==========================

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
    leading=16,
    spaceAfter=6,
)

# ==========================
# HEADING DETECTION
# ==========================

def is_heading(line):
    line = line.strip()
    if line.isupper() and len(line) < 100:
        return True
    return False


# ==========================
# PAGE NUMBER
# ==========================

def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    canvas.setFont("Helvetica", 10)
    canvas.drawRightString(580, 20, str(page_num))


# ==========================
# PDF GENERATOR (WORD TO WORD)
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
# TABLE MODE (ONLY /table)
# ==========================

async def table_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send table data like this:\n\n"
        "Name, Age, Class\n"
        "Ram, 14, 8\n"
        "Shyam, 15, 9"
    )

async def handle_table_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lines = text.strip().split("\n")

    table_data = []
    for line in lines:
        row = [cell.strip() for cell in line.split(",")]
        table_data.append(row)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    table = Table(table_data, hAlign="LEFT")

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)

    await update.message.reply_document(
        document=buffer,
        filename="Table_Output.pdf",
    )


# ==========================
# TEXT HANDLER (NORMAL MODE)
# ==========================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    pdf_buffer = generate_pdf(user_text)

    await update.message.reply_document(
        document=pdf_buffer,
        filename="Professional_Project.pdf",
    )


# ==========================
# START
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send your text.\n\n"
        "• Word to word formatting\n"
        "• Headings in ALL CAPS\n"
        "• Use /table for tables"
    )


# ==========================
# MAIN
# ==========================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("table", table_command))

    # Table data handler (after /table)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
