"""ReportLab PDF 导出服务：生成错题本 PDF 复习卷。"""
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

# 注册中文字体（STSong-Light 是 ReportLab 内置 CID 字体，无需字体文件）
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


def _styles():
    title = ParagraphStyle(
        "title", fontName="STSong-Light", fontSize=18, leading=26,
        alignment=1, textColor=colors.HexColor("#2B3A67"),
    )
    h2 = ParagraphStyle(
        "h2", fontName="STSong-Light", fontSize=13, leading=20,
        spaceBefore=14, textColor=colors.HexColor("#2B3A67"),
    )
    body = ParagraphStyle(
        "body", fontName="STSong-Light", fontSize=11, leading=18,
        spaceAfter=6, textColor=colors.HexColor("#3A3A35"),
    )
    return title, h2, body


def export_pdf(questions: list) -> bytes:
    """根据错题列表生成 PDF，返回二进制内容。"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=22 * mm, rightMargin=22 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )
    title, h2, body = _styles()
    story = [Paragraph("Recall AI 智能错题本", title), Spacer(1, 8)]
    story.append(Paragraph(f"导出日期：{date.today().isoformat()}", body))

    for q in questions:
        story.append(Paragraph(f"{q.subject} · {q.knowledge_point or '未归类'}", h2))
        story.append(Paragraph(f"【题目】{q.content}", body))
        if q.my_answer:
            story.append(Paragraph(f"【我的答案】{q.my_answer}", body))
        if q.correct_answer:
            story.append(Paragraph(f"【正确答案】{q.correct_answer}", body))
        if q.ai_analysis:
            story.append(Paragraph(f"【AI 解析】{q.ai_analysis}", body))
        story.append(Spacer(1, 8))

    doc.build(story)
    return buf.getvalue()
