"""Generate the Vietnamese SafeWeb KHKT engineering-project report."""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "reports" / "metrics.json"
EVALUATION_PATH = ROOT / "reports" / "phishvn_domain_eval.json"
OUTPUT_PATH = ROOT / "Bao_cao_SafeWeb_KHKT_THPT.docx"
SCREENSHOTS_PATH = ROOT / "reports" / "screenshots"

NAVY = "17324D"
TEAL = "167C80"
PALE_TEAL = "E6F2F1"
PALE_BLUE = "EAF0F5"
PALE_GOLD = "F5F0E3"
INK = "23313F"
MUTED = "5C6B78"
WHITE = "FFFFFF"
RED = "A33B35"


def set_cell_shading(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=90, bottom=80, end=90) -> None:
    properties = cell._tc.get_or_add_tcPr()
    margins = properties.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        properties.append(margins)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def prevent_row_split(row) -> None:
    properties = row._tr.get_or_add_trPr()
    properties.append(OxmlElement("w:cantSplit"))


def repeat_table_header(row) -> None:
    properties = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    properties.append(repeat)


def set_run_font(run, *, size=11, bold=False, color=INK, italic=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def add_page_field(paragraph, instruction: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    code = OxmlElement("w:instrText")
    code.set(qn("xml:space"), "preserve")
    code.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    value = OxmlElement("w:t")
    value.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend((begin, code, separate, value, end))


def set_page_number_format(section, fmt: str, start: int) -> None:
    properties = section._sectPr
    number_type = properties.find(qn("w:pgNumType"))
    if number_type is None:
        number_type = OxmlElement("w:pgNumType")
        properties.append(number_type)
    number_type.set(qn("w:fmt"), fmt)
    number_type.set(qn("w:start"), str(start))


def set_page_footer(section, color=NAVY):
    section.footer.is_linked_to_previous = False
    section.different_first_page_header_footer = False
    section.footer_distance = Cm(0.75)
    paragraph = section.footer.paragraphs[0]
    paragraph.clear()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run("SAFEWEB  |  BÁO CÁO KHKT  |  ")
    set_run_font(run, size=8, color=color)
    add_page_field(paragraph, "PAGE")


def add_paragraph(document, text: str, *, style=None, align=None, first_line=True, after=5):
    paragraph = document.add_paragraph(style=style)
    if align is not None:
        paragraph.alignment = align
    if first_line and style is None:
        paragraph.paragraph_format.first_line_indent = Cm(0.8)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.keep_together = True
    run = paragraph.add_run(text)
    set_run_font(run, size=9.5)
    return paragraph


def add_heading(document, text: str, level=1):
    paragraph = document.add_heading(text, level=level)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.space_before = Pt(6 if level == 1 else 4)
    paragraph.paragraph_format.space_after = Pt(2)
    return paragraph


def add_bullets(document, items, *, numbered=False):
    style = "List Number" if numbered else "List Bullet"
    for item in items:
        paragraph = document.add_paragraph(style=style)
        paragraph.paragraph_format.left_indent = Cm(0.7)
        paragraph.paragraph_format.first_line_indent = Cm(-0.35)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.keep_together = True
        set_run_font(paragraph.add_run(item), size=9.5)


def add_caption(document, text: str):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(5)
    paragraph.paragraph_format.keep_with_next = False
    set_run_font(paragraph.add_run(text), size=8.5, italic=True, color=MUTED)


def add_table(document, headers, rows, widths=None, font_size=8.6):
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.autofit = False
    header_row = table.rows[0]
    repeat_table_header(header_row)
    for index, label in enumerate(headers):
        cell = header_row.cells[index]
        cell.text = str(label)
        set_cell_shading(cell, NAVY)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for row_data in rows:
        cells = table.add_row().cells
        prevent_row_split(table.rows[-1])
        for index, value in enumerate(row_data):
            cells[index].text = str(value)
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if len(table.rows) % 2 == 0:
                set_cell_shading(cells[index], "F4F7F8")
    for row_index, row in enumerate(table.rows):
        for column_index, cell in enumerate(row.cells):
            set_cell_margins(cell, top=30, start=65, bottom=30, end=65)
            if widths and column_index < len(widths):
                cell.width = Cm(widths[column_index])
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.space_before = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in paragraph.runs:
                    set_run_font(
                        run,
                        size=font_size,
                        bold=row_index == 0,
                        color=WHITE if row_index == 0 else INK,
                    )
    spacer = document.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(0)
    spacer.paragraph_format.line_spacing = Pt(2)
    return table


def add_toc_field(document):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(8)
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = ' TOC \\o "1-1" \\h \\z \\u '
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Mục lục được cập nhật tự động từ các đề mục của báo cáo."
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend((begin, instruction, separate, placeholder, end))
    set_run_font(run, size=10, color=MUTED, italic=True)


def add_figure(document, path: Path, caption: str, width=15.8):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.keep_together = True
    paragraph.add_run().add_picture(str(path), width=Cm(width))
    add_caption(document, caption)


def make_pipeline_figure(path: Path):
    labels = [
        "Nhập URL\nchuỗi văn bản",
        "Chuẩn hóa\nHTTPS / .com",
        "Tra cứu cơ sở dữ liệu\nURL / host / chữ ký",
        "Trích xuất\n55 đặc trưng",
        "4 mô hình\nchạy song song",
        "Kiểm tra trực tuyến\ntùy chọn, có đồng ý",
        "Kết luận, giải thích\nvà giao diện",
    ]
    figure, axis = plt.subplots(figsize=(12.5, 2.5))
    axis.set_xlim(0, 12.5)
    axis.set_ylim(0, 2.5)
    axis.axis("off")
    box_width = 1.48
    gap = 0.29
    start = 0.12
    for index, label in enumerate(labels):
        x = start + index * (box_width + gap)
        color = "#E6F2F1" if index in (1, 2, 3, 4, 6) else "#EAF0F5"
        box = FancyBboxPatch(
            (x, 0.73), box_width, 1.0,
            boxstyle="round,pad=0.06,rounding_size=0.08",
            linewidth=1.15, edgecolor=f"#{TEAL}", facecolor=color,
        )
        axis.add_patch(box)
        axis.text(x + box_width / 2, 1.23, label, ha="center", va="center", fontsize=8.1, color=f"#{INK}")
        if index < len(labels) - 1:
            arrow = FancyArrowPatch(
                (x + box_width + 0.015, 1.23),
                (x + box_width + gap - 0.015, 1.23),
                arrowstyle="-|>", mutation_scale=10, linewidth=1.0, color=f"#{NAVY}",
            )
            axis.add_patch(arrow)
    axis.text(9.75, 0.25, "Chỉ kích hoạt sau khi người dùng bật kiểm tra trực tuyến", ha="center", fontsize=8, color=f"#{MUTED}")
    figure.savefig(path, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def make_metrics_figure(path: Path, evaluations):
    names = ["Random Forest", "Gradient Boosting", "Linear SVM", "Logistic Regression"]
    keys = ["random_forest", "gradient_boosting", "svm", "logistic_regression"]
    recall = [evaluations[key]["recall"] for key in keys]
    f1 = [evaluations[key]["f1_score"] for key in keys]
    positions = list(range(len(names)))
    figure, axis = plt.subplots(figsize=(8.8, 4.2))
    axis.bar([x - 0.18 for x in positions], recall, width=0.34, label="Recall phishing", color=f"#{TEAL}")
    axis.bar([x + 0.18 for x in positions], f1, width=0.34, label="F1 phishing", color="#C08B3E")
    axis.set_xticks(positions, names, rotation=12, ha="right")
    axis.set_ylim(0, 1.05)
    axis.set_ylabel("Tỷ lệ")
    axis.set_title("Hiệu năng trên tập kiểm thử theo tên miền được giữ riêng")
    axis.grid(axis="y", alpha=0.22)
    axis.legend(frameon=False, ncols=2, loc="upper center")
    for x, value in zip(positions, recall, strict=True):
        axis.text(x - 0.18, value + 0.025, f"{value:.3f}", ha="center", fontsize=7.5)
    figure.tight_layout()
    figure.savefig(path, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def make_confusion_figure(path: Path, evaluations):
    titles = ["Random Forest", "Gradient Boosting", "Linear SVM", "Logistic Regression"]
    keys = ["random_forest", "gradient_boosting", "svm", "logistic_regression"]
    figure, axes = plt.subplots(2, 2, figsize=(8.2, 6.3))
    for axis, title, key in zip(axes.flat, titles, keys, strict=True):
        matrix = evaluations[key]["confusion_matrix"]
        axis.imshow(matrix, cmap="GnBu", vmin=0)
        axis.set_title(title, fontsize=10)
        axis.set_xticks([0, 1], ["Hợp lệ", "Phishing"])
        axis.set_yticks([0, 1], ["Hợp lệ", "Phishing"])
        axis.set_xlabel("Dự đoán")
        axis.set_ylabel("Thực tế")
        for row in range(2):
            for column in range(2):
                axis.text(column, row, f"{matrix[row][column]:,}", ha="center", va="center", color=f"#{INK}", fontsize=10)
    figure.suptitle("Ma trận nhầm lẫn; hàng là nhãn thực tế, cột là nhãn dự đoán", fontsize=11)
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    figure.savefig(path, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def make_test_evidence_figure(path: Path):
    figure, axis = plt.subplots(figsize=(10.5, 4.1))
    axis.set_xlim(0, 10.5)
    axis.set_ylim(0, 4.1)
    axis.axis("off")
    axis.text(0.3, 3.76, "XÁC MINH CỤC BỘ · SAFEWEB", fontsize=12, weight="bold", color=f"#{NAVY}")
    cards = [
        (0.3, 2.05, "PYTHON / DATA", "59 passed", "pytest · pipeline, model, app", TEAL),
        (5.35, 2.05, "BROWSER", "15 passed", "URL logic · model · consent", "#C08B3E"),
        (0.3, 0.45, "PYTHON ↔ JAVASCRIPT", "10 valid · 6 invalid", "max feature Δ 1.33e-15 · max probability Δ 7.77e-16", "#547A9A"),
        (5.35, 0.45, "STATIC BUILD", "passed", "npm run build · Pages artifact", "#58806C"),
    ]
    for x, y, label, value, detail, color in cards:
        display_color = color if color.startswith("#") else f"#{color}"
        box = FancyBboxPatch(
            (x, y), 4.8, 1.25,
            boxstyle="round,pad=0.08,rounding_size=0.08",
            linewidth=1.0,
            edgecolor=display_color,
            facecolor="#F5F8F8",
        )
        axis.add_patch(box)
        axis.text(x + 0.2, y + 0.96, label, fontsize=8, weight="bold", color=display_color)
        axis.text(x + 0.2, y + 0.59, value, fontsize=13, weight="bold", color=f"#{NAVY}")
        axis.text(x + 0.2, y + 0.22, detail, fontsize=7, color=f"#{MUTED}")
    figure.savefig(path, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def add_contents(document):
    add_heading(document, "MỤC LỤC", 1)
    add_paragraph(
        document,
        "Mục lục Word liên kết trực tiếp với các cấp tiêu đề của báo cáo. Khi mở tài liệu, dùng lệnh cập nhật toàn bộ trường nếu trình xử lý văn bản chưa tự làm mới mục lục.",
        first_line=False,
        after=4,
    )
    add_toc_field(document)


def write_document(metrics, evaluation, output_path: Path):
    document = Document()
    section = document.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(1.8)
    section.right_margin = Cm(1.8)
    section.different_first_page_header_footer = True

    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(9.5)
    normal.font.color.rgb = RGBColor.from_string(INK)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.line_spacing = 1.0
    normal.paragraph_format.space_after = Pt(1)
    for name, size, color in (("Title", 18, NAVY), ("Heading 1", 12.5, NAVY), ("Heading 2", 10.5, TEAL), ("Heading 3", 9.5, NAVY)):
        style = styles[name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)

    document.core_properties.title = "SafeWeb: Ứng dụng trí tuệ nhân tạo kết hợp phân tích URL"
    document.core_properties.subject = "Báo cáo dự án kỹ thuật KHKT cấp THPT"
    document.core_properties.author = "Lê Văn Tuấn Anh; Nguyễn Hoàng Bảo"
    document.core_properties.keywords = "SafeWeb, phishing, URL, PhishVN, học máy, KHKT"

    # Cover page
    cover = document.add_paragraph()
    cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover.paragraph_format.space_before = Pt(16)
    set_run_font(cover.add_run("BÁO CÁO DỰ ÁN NGHIÊN CỨU KHOA HỌC KỸ THUẬT"), size=16, bold=True, color=NAVY)
    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(subtitle.add_run("CUỘC THI KHOA HỌC KỸ THUẬT CẤP TRUNG HỌC PHỔ THÔNG"), size=11, bold=True, color=TEAL)
    document.add_paragraph("")
    badge = document.add_paragraph()
    badge.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(badge.add_run("LĨNH VỰC: KHOA HỌC MÁY TÍNH / TRÍ TUỆ NHÂN TẠO"), size=10, bold=True, color=MUTED)
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(28)
    title.paragraph_format.space_after = Pt(18)
    set_run_font(title.add_run("SAFEWEB\nỨNG DỤNG TRÍ TUỆ NHÂN TẠO MACHINE LEARNING KẾT HỢP PHÂN TÍCH URL CẢNH BÁO SỚM RỦI RO LỪA ĐẢO VÀ LỘ LỌT DỮ LIỆU"), size=17, bold=True, color=NAVY)
    rule = document.add_paragraph()
    rule.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(rule.add_run("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"), size=12, color=TEAL)
    cover_gap = document.add_paragraph()
    cover_gap.paragraph_format.space_before = Pt(260)
    cover_gap.paragraph_format.space_after = Pt(0)
    cover_gap.paragraph_format.line_spacing = Pt(1)
    meta = document.add_table(rows=5, cols=2)
    meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta.autofit = False
    cover_rows = [
        ("Dạng dự án", "Dự án kỹ thuật (Engineering Project)"),
        ("Mô hình học máy", "Random Forest · Gradient Boosting · SVM tuyến tính · Logistic Regression"),
        ("Người thực hiện 1", "Lê Văn Tuấn Anh"),
        ("Người thực hiện 2", "Nguyễn Hoàng Bảo"),
        ("Người hướng dẫn", "Trần Văn Toàn"),
    ]
    for row, (label, value) in zip(meta.rows, cover_rows, strict=True):
        row.cells[0].text = label
        row.cells[1].text = value
        row.cells[0].width = Cm(4.5)
        row.cells[1].width = Cm(8.7)
        for index, cell in enumerate(row.cells):
            set_cell_margins(cell, top=130, bottom=130)
            set_cell_shading(cell, PALE_BLUE if index == 0 else "F7F9FA")
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    set_run_font(run, size=11, bold=index == 0, color=NAVY if index == 0 else INK)
    location = document.add_paragraph()
    location.alignment = WD_ALIGN_PARAGRAPH.CENTER
    location.paragraph_format.space_before = Pt(35)
    set_run_font(location.add_run("NĂM 2026"), size=11, bold=True, color=MUTED)

    toc_section = document.add_section(WD_SECTION_START.NEW_PAGE)
    toc_section.page_width = Cm(21.0)
    toc_section.page_height = Cm(29.7)
    toc_section.top_margin = Cm(1.8)
    toc_section.bottom_margin = Cm(1.8)
    toc_section.left_margin = Cm(1.8)
    toc_section.right_margin = Cm(1.8)
    set_page_number_format(toc_section, "lowerRoman", 1)
    set_page_footer(toc_section)
    add_contents(document)

    document.add_page_break()
    add_heading(document, "TÓM TẮT", 1)
    abstract = (
        "SafeWeb là nguyên mẫu phần mềm hướng đến cảnh báo sớm rủi ro lừa đảo và lộ lọt dữ liệu qua phân tích URL. Hệ thống ưu tiên xử lý cục bộ, kết hợp cơ sở dữ liệu tham chiếu, 55 đặc trưng và bốn mô hình học máy: Random Forest, Gradient Boosting, SVM tuyến tính và Logistic Regression. DNS, chuyển hướng, metadata và ảnh xem trước chỉ được yêu cầu khi người dùng đồng ý. Giao diện còn cung cấp kho dữ liệu tương tác và gợi ý category/provider/brand theo luật.\n\n"
        "Dữ liệu PhishVN v3.1.0 gồm 53.116 dòng nguồn, được chuẩn hóa còn 36.261 URL duy nhất; loại 16.855 bí danh và không ghi nhận nhóm URL xung đột nhãn. Huấn luyện sử dụng 29.637 mẫu PhishVN train/validation cùng 231.662 mẫu PhiUSIIL đã làm sạch, tổng cộng 261.299 mẫu. Tập test gồm 6.624 URL từ phân vùng PhishVN chính thức, tách biệt domain khỏi train. Bốn mô hình được so sánh bằng chỉ số lớp phishing và ma trận nhầm lẫn.\n\n"
        "Gradient Boosting đạt F1 phishing 0,8697, recall 0,9561; SVM đạt ROC-AUC 0,9308 nhưng recall ở ngưỡng hiện tại chỉ 0,0071. Lần kiểm thử ghi nhận 59 kiểm thử Python, 15 kiểm thử trình duyệt; parity trên 10 URL hợp lệ và 6 URL lỗi có sai khác cực đại 1,33×10⁻¹⁵ ở đặc trưng và 7,77×10⁻¹⁶ ở xác suất. Kết quả xác minh tính nhất quán trên các ca đã chọn, không chứng minh hiệu quả thực địa. SafeWeb là công cụ giáo dục tham khảo, không chứng nhận website an toàn hay độc hại."
    )
    for block in abstract.split("\n\n"):
        add_paragraph(document, block)
    add_paragraph(document, "Từ khóa: phishing; URL; PhishVN; học máy; suy luận phía trình duyệt; bảo vệ quyền riêng tư.", first_line=False, after=8)

    main_section = document.add_section(WD_SECTION_START.NEW_PAGE)
    main_section.page_width = Cm(21.0)
    main_section.page_height = Cm(29.7)
    main_section.top_margin = Cm(1.8)
    main_section.bottom_margin = Cm(1.8)
    main_section.left_margin = Cm(1.8)
    main_section.right_margin = Cm(1.8)
    set_page_number_format(main_section, "decimal", 1)
    set_page_footer(main_section)

    # Chapter 1
    add_heading(document, "CHƯƠNG 1. XÁC ĐỊNH NHU CẦU VÀ MỤC TIÊU KỸ THUẬT", 1)
    add_heading(document, "1.1. Bối cảnh và vấn đề thực tiễn", 2)
    add_paragraph(document, "URL gồm scheme, authority, path, query và fragment theo cú pháp URI (Berners-Lee et al., 2005). Phishing thường dùng hostname giả mạo thương hiệu, đường dẫn dài, ký tự mã hóa hoặc lời mời đăng nhập. HTTPS chỉ mô tả giao thức kết nối, không xác minh chủ thể website. Vì vậy SafeWeb trình bày tín hiệu quan sát được thay vì khẳng định chắc chắn URL an toàn hay độc hại.")
    add_paragraph(document, "URL có thể chứa mã theo dõi hoặc định danh riêng tư. SafeWeb ưu tiên chuẩn hóa, tra cứu và suy luận cục bộ; chỉ DNS, redirect, metadata và preview mới gửi yêu cầu ngoài sau khi người dùng đồng ý.")
    add_heading(document, "1.2. Nhu cầu kỹ thuật và câu hỏi nghiên cứu", 2)
    add_paragraph(document, "Nhu cầu kỹ thuật là phân tích URL, tra cứu tham chiếu, hiển thị lý do/mức cảnh báo và chỉ kiểm tra mạng sau consent. Câu hỏi nghiên cứu: với cùng schema và tham số, suy luận JavaScript có khớp Python trên bộ ca kiểm thử định trước không?")
    add_paragraph(document, "Giả thuyết: giữ cố định thứ tự 55 feature và phép tiền xử lý khi export sẽ làm xác suất trình duyệt gần trùng Python trong sai số dấu phẩy động. Script parity kiểm tra giả thuyết trên các ca chọn sẵn; kết quả không khái quát tới mọi URL.")
    add_heading(document, "1.3. Mục tiêu và tiêu chí thiết kế", 2)
    add_table(document, ["Mục tiêu", "Tiêu chí có thể kiểm chứng", "Bằng chứng hiện có"], [
        ("Phân tích nhiều tín hiệu", "Dùng cùng schema 55 đặc trưng cho bốn bộ phân loại.", "metrics.json ghi feature_count = 55."),
        ("Đánh giá tránh rò rỉ theo tên miền", "Tập kiểm thử theo phân vùng chính thức không giao tên miền đăng ký với train.", "phishvn_domain_eval.json: test_domains_disjoint_from_training = true."),
        ("Chạy cục bộ mặc định", "Tra cứu, trích đặc trưng, dự đoán không cần gửi URL tới dịch vụ mạng.", "Browser bundle chứa mô hình, suffix rules và chỉ mục; live checks mặc định tắt."),
        ("Duy trì tương đương Python–JavaScript", "Chênh lệch số học rất nhỏ trên bộ ca đã khóa.", "10 URL hợp lệ + 6 không hợp lệ; delta tối đa 1,33e-15 / 3,33e-16."),
        ("Thông báo có giới hạn", "Không gọi kết quả là chứng nhận an toàn; nêu SVM và giới hạn CORS.", "UI disclaimer, kết quả held-out và kiểm tra mã nguồn."),
    ], widths=[3.6, 6.3, 6.0], font_size=8.4)
    add_heading(document, "1.4. Phạm vi, giả định và giới hạn", 2)
    add_paragraph(document, "Phạm vi gồm chuỗi URL và nhãn trong các tập dữ liệu đã công bố. SafeWeb không tải/chạy HTML, không xác thực chứng thư TLS, tuổi tên miền, WHOIS, reputation hay hành vi trang; DNS chỉ kiểm tra khi bật live inspection. Nguyên mẫu chưa được đánh giá người dùng hoặc kiểm định bảo mật độc lập.")
    add_heading(document, "1.5. Giá trị và định hướng giáo dục", 2)
    add_paragraph(document, "SafeWeb hướng tới dạy an toàn số và tư duy dữ liệu: quan sát pipeline, so sánh bằng chứng, nhận diện giới hạn AI. Chưa có nghiên cứu học sinh hay đo hiệu quả sư phạm; đây là mục tiêu đề xuất, không phải kết quả thực nghiệm.")
    add_table(document, ["Năng lực hướng tới", "Hoạt động học tập có thể quan sát", "Giới hạn cần nêu"], [
        ("Hiểu URL", "Tách scheme, hostname, subdomain, path, query và xác định tín hiệu.", "Từ khóa, IP hay HTTPS không tự chứng minh an toàn/độc hại."),
        ("Phản biện AI", "So sánh tra cứu, xác suất model, precision/recall/F1 và lỗi FP/FN.", "Kết quả phụ thuộc dữ liệu/ngưỡng; SVM có recall rất thấp."),
        ("Quyền riêng tư", "Phân biệt local-only với live inspection trước khi chia sẻ URL.", "Không nhập token/URL riêng tư; HTTPS không xác thực danh tính."),
        ("Tái lập kỹ thuật", "Theo dõi pipeline và đối chiếu Python–JavaScript.", "Parity chỉ xác nhận các ca đã chọn."),
    ], widths=[3.3, 6.4, 6.2], font_size=8.2)
    add_paragraph(document, "Kịch bản lớp học dùng URL giả lập: phân tích hostname trước khi xem dự đoán, giải thích một FP/FN và đề xuất cách xác minh chính thức. Tắt live checks, không mở URL. Đánh giá sư phạm tương lai cần pre/post test, rubric, đồng thuận và bảo vệ dữ liệu; hiện chưa đo các kết quả này.")

    # Chapter 2
    add_heading(document, "CHƯƠNG 2. PHÂN TÍCH GIẢI PHÁP VÀ CƠ SỞ LÝ THUYẾT", 1)
    add_heading(document, "2.1. Phân biệt dự án khoa học và dự án kỹ thuật", 2)
    add_paragraph(document, "SafeWeb là dự án kỹ thuật với đầu ra nguyên mẫu phần mềm; đánh giá dựa trên hoạt động, tái lập và giới hạn vận hành, không nghiên cứu nhân quả hành vi người dùng.")
    add_heading(document, "2.2. Phân tích các phương án thiết kế", 2)
    add_table(document, ["Phương án", "Ưu điểm", "Đánh đổi / lý do lựa chọn"], [
        ("Heuristic URL", "Nhanh, giải thích được, không cần fit.", "Hạn chế tương tác phi tuyến; không dùng riêng làm verdict."),
        ("Chỉ tra cứu", "Match có record/provenance.", "Không bao phủ URL mới; giữ như tầng riêng."),
        ("Chỉ backend", "Dễ cập nhật/tập trung tài nguyên.", "Phải gửi URL lên server."),
        ("Trình duyệt + tra cứu + live opt-in", "Local inference và kiểm tra mạng theo consent.", "Bundle lớn; cần parity, có giới hạn CORS."),
    ], widths=[3.5, 5.1, 7.3], font_size=8.4)
    add_heading(document, "2.3. Cơ sở lý thuyết của bốn bộ phân loại", 2)
    add_paragraph(document, "Random Forest tổng hợp xác suất từ các cây quyết định lấy mẫu ngẫu nhiên, phù hợp quan hệ phi tuyến và có thể export cây sang JavaScript (Breiman, 2001). Cấu hình: 100 cây, depth 16, leaf 3, balanced-subsample.")
    add_paragraph(document, "Gradient Boosting cộng tuần tự cây nông theo gradient mất mát (Friedman, 2001). Cấu hình: 100 cây, depth 3, learning rate 0,1; đạt recall cao nhất nhưng có nhiều false positive.")
    add_paragraph(document, "Linear SVM tối đa hóa biên phân tách (Cortes & Vapnik, 1995), dùng `StandardScaler`, `LinearSVC` và sigmoid calibration 3-fold. ROC-AUC 0,9308 nhưng recall hiện chỉ 0,0071, nên ngưỡng chưa hữu ích.")
    add_paragraph(document, "Logistic Regression là baseline tuyến tính, ánh xạ tổ hợp đặc trưng qua sigmoid; cấu hình dùng `StandardScaler`, balanced class weights và tối đa 2.000 vòng lặp. Các estimator dựa trên scikit-learn (Pedregosa et al., 2011).")
    add_heading(document, "2.4. Lý do phối hợp mô hình và cách hiểu đồng thuận", 2)
    add_paragraph(document, "Hệ thống lấy trung bình số học bốn xác suất, dùng ngưỡng 0,5 cho nhãn và vẫn hiển thị điểm riêng; đây không phải bỏ phiếu đa số hay bảo đảm lỗi độc lập. Vì SVM có recall 0,0071 ở ngưỡng hiện tại, cần hiệu chỉnh trước khi dựa vào đồng thuận.")
    add_heading(document, "2.5. Điểm mới trong phạm vi nguyên mẫu", 2)
    add_bullets(document, [
        "Kết hợp tra cứu tham chiếu và bốn model trong trình duyệt.",
        "Tách database match khỏi xác suất ML để phân biệt record và dự đoán.",
        "Đóng gói cây, scaler, calibration và suffix rules cho suy luận offline.",
        "Live checks có consent gate trước khi chia sẻ URL.",
        "Đối chiếu feature/probability giữa Python và JavaScript.",
    ])
    add_paragraph(document, "Các điểm trên là đóng góp kỹ thuật của nguyên mẫu, không phải khẳng định thuật toán mới hoặc ưu thế vượt trội so với dịch vụ thương mại.")

    # Chapter 3
    add_heading(document, "CHƯƠNG 3. THIẾT KẾ, VẬT LIỆU VÀ PHƯƠNG PHÁP", 1)
    add_heading(document, "3.1. Thành phần và công cụ", 2)
    add_table(document, ["Thành phần", "Công nghệ / vai trò"], [
        ("Backend phát triển", "Python, Flask; route `/predict` nhận JSON và gọi pipeline Python."),
        ("Phân tích dữ liệu / ML", "pandas, NumPy, scikit-learn; joblib lưu mô hình; matplotlib dựng ma trận nhầm lẫn."),
        ("Giao diện", "HTML, CSS, JavaScript; có bản Flask dev và bản tĩnh GitHub Pages."),
        ("Nguồn dữ liệu", "PhishVN v3.1.0 và PhiUSIIL Phishing URL Dataset; quy ước nhãn SafeWeb 1 = phishing."),
        ("Kiểm thử", "pytest, Node.js built-in test runner, script đối chiếu parity và build GitHub Pages."),
    ], widths=[4.0, 11.9], font_size=8.8)
    add_heading(document, "3.2. Kiểm toán và chuẩn bị dữ liệu", 2)
    add_paragraph(document, "PhishVN v3.1.0 có 53.116 dòng; sau chuẩn hóa/gộp `www`-apex còn 36.261 URL (19.909 phishing, 16.352 benign), loại 16.855 alias, không có conflict. Split chính thức: train 25.185, validation 4.452, test 6.624; các split không giao domain (Thai Nguyen Vu, 2026).")
    add_paragraph(document, "PhiUSIIL có 235.795 dòng; loại 86 URL conflict, 3.586 bản canonical trùng và 461 URL thuộc 4.260 domain test, còn 231.662 mẫu (97.003 phishing, 134.659 benign) để fit. Nhãn được đảo về `1=phishing`. Tổng train: 29.637 PhishVN + 231.662 PhiUSIIL = 261.299; test 6.624 giữ riêng (PhiUSIIL Phishing URL Dataset, n.d.).")
    add_table(document, ["Tập / bước", "Hợp lệ", "Phishing", "Benign", "Ghi chú"], [
        ("PhishVN sau canonicalization", "36.261", "19.909", "16.352", "16.855 alias trùng loại bỏ; split domain-disjoint."),
        ("PhishVN train + validation", "29.637", "17.110", "12.527", "Hai phân vùng chính thức dùng fit."),
        ("PhiUSIIL sau audit", "231.662", "97.003", "134.659", "Loại conflict, canonical duplicate và domain test."),
        ("Tổng mẫu huấn luyện", "261.299", "114.113", "147.186", "Cân bằng tổng trọng số theo nguồn và lớp."),
        ("PhishVN test giữ riêng", "6.624", "2.799", "3.825", "Không dùng trong fit; domain tách biệt."),
    ], widths=[3.6, 2.0, 2.0, 2.0, 6.3], font_size=8.2)
    add_paragraph(document, "Đối chiếu 797.742 giá trị CompPhish trên 36.261 URL khớp bảng phát hành trong dung sai; timestamp chỉ là provenance, không dùng làm nhãn.")
    add_heading(document, "3.3. Lược đồ 55 đặc trưng", 2)
    add_paragraph(document, "Mô hình dùng vector có thứ tự cố định; feature cùng tên được giữ riêng theo định nghĩa nguồn. Hồ sơ host cung cấp một số giá trị TLD; nếu thiếu, dùng phép tính cục bộ và suffix list đóng gói.")
    feature_rows = [
        ("01–10", "URL tổng quát", "url_length; domain_length; path_length; query_length; num_dots; num_slashes; num_hyphens; num_underscores; num_digits; num_letters", "Độ dài chuỗi/thành phần và tần suất dấu, chữ, số."),
        ("11–20", "Cấu trúc URL", "num_special_chars; has_https; has_ip; num_subdomains; has_at; has_question_mark; has_equals; has_percent; has_double_slash; has_query", "Cờ cấu trúc, kiểu hostname và thành phần truy vấn."),
        ("21–22", "Độ phức tạp chuỗi", "url_entropy; domain_entropy", "Entropy Shannon theo ký tự trên URL và hostname."),
        ("23–30", "Từ khóa thực sự trong mô hình", "keyword_login; keyword_signin; keyword_verify; keyword_account; keyword_password; keyword_bank; keyword_payment; keyword_confirm", "Cờ có/không theo substring trên toàn URL viết thường."),
        ("31–40", "PhishVN / CompPhish", "phishvn_url_len; phishvn_dom_len; phishvn_is_ip; phishvn_tld_len; phishvn_subdom_cnt; phishvn_letter_cnt; phishvn_digit_cnt; phishvn_special_cnt; phishvn_eq_cnt; phishvn_qm_cnt", "Các biến đo theo quy ước schema PhishVN."),
        ("41–52", "PhishVN / CompPhish", "phishvn_amp_cnt; phishvn_dot_cnt; phishvn_dash_cnt; phishvn_under_cnt; phishvn_letter_ratio; phishvn_digit_ratio; phishvn_spec_ratio; phishvn_slash_cnt; phishvn_entropy; phishvn_path_len; phishvn_query_len; phishvn_suspicious_tld", "Số lượng, tỷ lệ, entropy và cờ TLD đáng ngờ."),
        ("53–55", "PhiUSIIL obfuscation", "phiusiil_has_obfuscation; phiusiil_obfuscated_char_count; phiusiil_obfuscation_ratio", "Phát hiện và lượng hóa chuỗi `%xx`; độ dài mã hóa quy ước ba ký tự mỗi escape."),
    ]
    add_table(document, ["Chỉ số", "Nhóm", "Tên đặc trưng", "Diễn giải"], feature_rows, widths=[1.4, 3.1, 7.6, 4.0], font_size=7.6)
    add_heading(document, "3.4. Nhóm từ khóa và cách diễn giải", 2)
    add_paragraph(document, "Các nhóm dưới đây mô tả ngữ nghĩa; model chỉ dùng tám keyword ở bảng, và sự xuất hiện của từ không chứng minh phishing.")
    add_table(document, ["Nhóm ngữ nghĩa", "Ví dụ theo yêu cầu", "Trạng thái trong phiên bản hiện tại"], [
        ("Tài chính / ngân hàng", "vietcombank, bidv, techcombank, acb, mbbank, wallet, pay, credit, card", "Cờ học máy chỉ có `bank`, `payment`; tên thương hiệu được nhận diện theo luật để gợi ý category/brand, không phải chín feature riêng."),
        ("Xác minh / xác thực", "login, signin, verify, update, secure, account, auth, confirm", "login, signin, verify, account, confirm là 5/8 từ khóa model; update, secure, auth chưa có cờ model."),
        ("Khẩn cấp / cưỡng ép", "urgent, suspended, locked, alert, limited, action-required", "Không nằm trong tám cờ từ khóa mô hình hiện tại; có thể cân nhắc ở phiên bản nghiên cứu kế tiếp."),
        ("Quà tặng / khuyến mãi", "gift, bonus, reward, free, iphone, win, voucher", "Không nằm trong tám cờ từ khóa mô hình hiện tại; không được mô tả như tiêu chí đã vận hành."),
        ("Từ khóa còn lại đang dùng", "password, bank, payment", "Được trích thành cờ `keyword_password`, `keyword_bank`, `keyword_payment`."),
    ], widths=[3.0, 5.4, 7.7], font_size=8.1)
    add_heading(document, "3.5. Quy trình huấn luyện có thể tái lập", 2)
    add_bullets(document, [
        "Dùng train/validation chính thức; giữ nguyên test PhishVN domain-disjoint.",
        "Chuẩn hóa PhiUSIIL, đảo nhãn về 1=phishing; loại conflict, duplicate và domain giao test.",
        "Tạo schema 55 feature chung, gồm CompPhish và ba feature obfuscation.",
        "Cân bằng trọng số theo nguồn/lớp; fit bốn model với seed 42.",
        "Đánh giá cùng 6.624 URL test bằng accuracy, precision, recall, F1, ROC-AUC và confusion matrix.",
    ], numbered=True)
    add_heading(document, "3.6. Kiến trúc suy luận trình duyệt", 2)
    add_paragraph(document, "Exporter đóng gói cây và tham số scaler/linear/SVM calibration cùng feature order, suffix rules và cơ sở dữ liệu. `browser-model.js` thực thi suy luận JavaScript, không gọi backend. Local-only không gửi URL; live inspection gửi URL tới DNS/preview providers sau consent, nên không nhập token hay URL riêng tư.")
    add_heading(document, "3.7. Tra cứu cơ sở dữ liệu tham chiếu và thứ tự kết luận", 2)
    add_paragraph(document, "Tra cứu theo URL chuẩn hóa → hostname → chữ ký feature độc quyền. Chỉ mục nguồn đã trích dẫn có 19.909 URL keys, 19.859 host keys và 4.461 signatures. Match được tách khỏi metric ML; không có match chỉ nghĩa là không có bản ghi, không chứng minh URL an toàn.")
    add_heading(document, "3.8. Chuẩn hóa URL và các chức năng chính", 2)
    add_table(document, ["Tính năng", "Cơ chế đã kiểm tra", "Giới hạn / cách diễn giải"], [
        ("Smart URL auto-healing", "Thêm `https://` khi thiếu scheme; từ đơn không có dấu chấm được thử bằng cách thêm `.com`; chuẩn hóa scheme/host, cổng mặc định và slash cuối.", "Đây là suy đoán đầu vào tiện lợi, không chứng minh hostname tồn tại; URL chuẩn hóa được hiển thị để người dùng kiểm tra."),
        ("Tra cứu cơ sở dữ liệu + đối chiếu đặc trưng", "URL chính xác → hostname đã biết → chữ ký đặc trưng độc quyền.", "Kết quả chỉ phản ánh bản ghi khớp; chữ ký đặc trưng có độ bao phủ và khả năng va chạm phụ thuộc thiết kế kho."),
        ("DNS qua DoH", "Truy vấn A, AAAA, MX, NS, CNAME qua `dns.google/resolve` theo khái niệm DNS (Mockapetris, 1987); phân biệt resolved, missing, unavailable.", "DNS có bản ghi không đồng nghĩa website hợp lệ; NXDOMAIN chỉ xác định không phân giải trong lần kiểm tra."),
        ("Redirect analysis", "Gỡ tối đa năm lớp tham số URL nhúng (url/u/next/redirect/target/continue/dest/destination), đánh giá URL đích và quan sát bước chuyển hướng HTTP (Fielding et al., 2022).", "Browser CORS có thể ngăn đọc `Location` của HTTP 301/302; chỉ báo cáo đích quan sát được, không tuyên bố luôn có chain đầy đủ."),
        ("Category/provider/brand", "Luật chuỗi nhận diện các danh mục, hosting suffix và thương hiệu có trong allowlist.", "Là gợi ý phân loại, không phải xác minh chủ sở hữu; brand mismatch không phải hiện tại một anomaly detector độc lập."),
        ("URL đối chiếu", "Lấy tối đa năm URL phishing cùng brand/category từ tập dữ liệu tham chiếu, hiển thị dưới dạng văn bản.", "Ví dụ là bản ghi lịch sử; không mở URL, không khẳng định cùng chiến dịch hay còn hoạt động."),
        ("Database Explorer", "Tìm kiếm, lọc nhãn/category/tier, phân trang, xem feature và gửi URL được chọn vào máy phân tích.", "Dữ liệu trình duyệt được đóng gói; nội dung URL chỉ nên đọc, không truy cập trực tiếp."),
        ("Easter egg SafeWeb", "Host `jerryishere.github.io` và path `/safeweb` được nhận diện, hiển thị thông điệp riêng và LOW.", "Đây là nhánh demo được mã hóa rõ ràng, không phải kết quả kiểm chứng độc lập cho domain."),
    ], widths=[3.0, 7.0, 6.2], font_size=7.8)
    add_heading(document, "3.9. Phân tích tín hiệu, mức rủi ro và giao diện", 2)
    add_paragraph(document, "Các lý do hiển thị được gắn với vị trí có thể chỉ ra: URL dài từ 100 ký tự; từ ba subdomain; hostname là IP; có ít nhất tám ký tự đặc biệt; entropy URL ít nhất 4,5 bit/ký tự; percent-encoding; tín hiệu obfuscation PhiUSIIL; và các keyword đã cấu hình. Phần giải thích giới hạn tối đa năm lý do trong danh sách chi tiết. Các ngưỡng này là tiêu chí trình bày hiện hành, không phải chuẩn phổ quát của phishing.")
    add_paragraph(document, "Điểm heuristic giao diện cộng: URL dài từ 120 ký tự +18; từ ba subdomain +16; hostname IP +18; có `@` +12; từ tám ký tự đặc biệt +10; có `%` +8; entropy từ 4,5 +10; mỗi keyword khớp +8. Điểm kết hợp được tính `clamp(0, 100, 0,6 × 100p + heuristicScore)`. Mức theme lại phân loại theo xác suất ensemble p: LOW nếu p < 0,25; CAUTION nếu 0,25 ≤ p < 0,50; HIGH nếu 0,50 ≤ p < 0,75; VERY HIGH nếu p ≥ 0,75. Kết quả khớp cơ sở dữ liệu và Easter egg có nhánh ghi đè theo record/host. Vì score và tier có công thức khác nhau, không nên suy ra tier chỉ từ điểm heuristic.")
    add_paragraph(document, "Giao diện đổi trạng thái trực quan theo mức LOW/CAUTION/HIGH/VERY HIGH, gồm badge, thanh mức tín hiệu, icon, phần kết luận và khuyến nghị. Màu là kênh trình bày; văn bản, nguồn match, xác suất từng model và disclaimer mới là bằng chứng để người đọc diễn giải. HTTPS được hiển thị như scheme có mặt, không phải trạng thái xác thực TLS.")
    add_heading(document, "3.10. Chẩn đoán bất thường: điều đã và chưa có", 2)
    add_table(document, ["Hiện tượng", "Trạng thái triển khai", "Diễn giải chính xác"], [
        ("URL dài / nhiều subdomain / IP / ký tự đặc biệt / entropy cao", "Được nêu thành lý do khi đạt ngưỡng.", "Có thể chỉ ra nhóm đặc trưng quan sát được; không chứng minh ý đồ xấu."),
        ("Hyphen count", "Có đặc trưng `num_hyphens` và `phishvn_dash_cnt` trong model.", "Không có ngưỡng hyphen riêng trong danh sách lý do; không tuyên bố UI đánh dấu chính xác vị trí dấu gạch nối."),
        ("Suspicious TLD", "Có cờ `phishvn_suspicious_tld` và danh sách suffix.", "Là đầu vào mô hình, nhưng chưa có thông báo lý do TLD riêng trong explain list hiện tại."),
        ("Brand keyword / brand mismatch", "Brand/category được gợi ý theo luật chuỗi; feature keyword chỉ gồm tám từ đã nêu.", "Không có so sánh domain đăng ký với brand allowlist để phát hiện mismatch độc lập."),
        ("Redirect obfuscation", "Tham số redirect nhúng được gỡ và URL đích được đánh giá khi live check bật.", "Không có bảo đảm đọc toàn bộ redirect HTTP do CORS và nguồn bên thứ ba."),
        ("Entropy cao", "Ngưỡng explain hiện tại là 4,5.", "Đo độ phân bố ký tự, không đo nội dung trang hay ý nghĩa chuỗi."),
    ], widths=[3.7, 5.7, 6.8], font_size=8.0)

    with tempfile.TemporaryDirectory(prefix="safeweb-report-") as temporary:
        temporary_path = Path(temporary)
        pipeline_path = temporary_path / "pipeline.png"
        test_evidence_path = temporary_path / "test-evidence.png"
        homepage_path = SCREENSHOTS_PATH / "homepage.png"
        make_pipeline_figure(pipeline_path)
        make_test_evidence_figure(test_evidence_path)

        add_heading(document, "3.11. Lưu đồ vận hành", 2)
        add_paragraph(document, "Quy trình dưới đây thể hiện đường đi chính của một lần phân tích. Bước live inspection nằm sau consent gate; luồng local-only dừng ở suy luận và render kết quả.")
        add_figure(document, pipeline_path, "Hình 3.1. Pipeline từ nhập URL đến hiển thị; kiểm tra mạng là nhánh tùy chọn sau khi đồng ý.")

        # Chapter 4
        add_heading(document, "CHƯƠNG 4. KẾT QUẢ THỬ NGHIỆM VÀ THẢO LUẬN", 1)
        add_heading(document, "4.1. Giao thức đánh giá và định nghĩa chỉ số", 2)
        add_paragraph(document, "Bốn model dùng cùng 261.299 mẫu, 55 feature và test giữ riêng 6.624 URL (3.825 benign, 2.799 phishing). Precision/recall/F1 tính cho lớp phishing; confusion order là TN/FP/FN/TP. ROC-AUC đo ranking qua nhiều ngưỡng, không thay thế metric tại threshold. Số liệu lấy từ artefact đánh giá SafeWeb (2026).")
        add_heading(document, "4.2. Kết quả định lượng bốn mô hình", 2)
        model_names = {
            "random_forest": "Random Forest",
            "gradient_boosting": "Gradient Boosting",
            "svm": "SVM tuyến tính hiệu chuẩn",
            "logistic_regression": "Logistic Regression",
        }
        result_rows = []
        for key, name in model_names.items():
            result = metrics["evaluations"][key]
            counts = result["confusion_counts"]
            result_rows.append((
                name,
                f"{result['accuracy']:.4f}",
                f"{result['precision']:.4f}",
                f"{result['recall']:.4f}",
                f"{result['f1_score']:.4f}",
                f"{result['roc_auc']:.4f}",
                f"{counts['tn']} / {counts['fp']} / {counts['fn']} / {counts['tp']}",
                f"{result['training_rows']:,} / {result['test_rows']:,}",
            ))
        add_table(document, ["Mô hình", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "TN / FP / FN / TP", "Train / Test"], result_rows, widths=[2.9, 1.3, 1.35, 1.2, 1.0, 1.2, 3.4, 2.5], font_size=7.7)
        add_paragraph(document, "Gradient Boosting đạt accuracy 0,8789, F1 0,8697, recall 0,9561 (2.676/2.799 TP) và 679 FP. Random Forest: recall 0,9232, F1 0,8615; Logistic Regression: F1 0,8371. SVM chỉ phát hiện 20 phishing, bỏ sót 2.779, dù ROC-AUC 0,9308; cần hiệu chỉnh threshold trên validation.")
        add_heading(document, "4.3. Phân tích sai số và độ tin cậy", 2)
        add_paragraph(document, "False negative bỏ sót phishing; false positive cảnh báo URL hợp lệ. Gradient Boosting có 123 FN/679 FP; Logistic Regression 341/616. SVM precision 1,0 chỉ trên 20 phát hiện, không đại diện cho recall.")
        add_paragraph(document, "Metric chỉ mô tả corpus/split này; không đo calibration, deployment drift, chống né tránh hay quan hệ nhân quả. Tách domain giảm leakage nhưng không loại hết trùng chiến dịch/nguồn.")
        add_heading(document, "4.4. Đối chiếu Python–JavaScript", 2)
        add_table(document, ["Hạng mục", "Kết quả ghi nhận", "Phạm vi kết luận"], [
            ("Ca hợp lệ", "10 URL", "Đối chiếu feature vector, xác suất và verdict."),
            ("Ca không hợp lệ", "6 URL", "Kiểm tra từ chối đầu vào sai định dạng."),
            ("Feature delta cực đại", "1,33 × 10⁻¹⁵", "Sai khác dấu phẩy động rất nhỏ trong tập ca định trước."),
            ("Probability delta cực đại", "7,77 × 10⁻¹⁶", "Không bằng 0 tuyệt đối; khác biệt ở độ chính xác máy."),
        ], widths=[4.0, 3.6, 8.9], font_size=8.6)
        add_paragraph(document, "Parity xác nhận hai runtime nhất quán trên ca đã chọn, không chứng minh hiệu quả bảo mật. Cần bổ sung IDN, IPv6, user-info, query lồng và URL adversarial.")
        add_heading(document, "4.5. Kiểm thử phần mềm và build", 2)
        add_table(document, ["Cổng kiểm tra", "Kết quả được ghi nhận", "Ý nghĩa"], [
            ("Python / data tests", "59 passed (`python -m pytest -q`)", "Lần chạy hiện hành; gồm pipeline dữ liệu, extractor, model, web app và thử nghiệm."),
            ("Browser unit tests", "15 passed (`npm run test:browser`)", "Lần chạy hiện hành; kiểm tra suy luận/URL helper phía JavaScript."),
            ("Model parity", "10 hợp lệ + 6 không hợp lệ; delta nêu tại mục 4.4", "Đối chiếu hai runtime trên ca xác định."),
            ("Build tĩnh", "`npm run build` passed; artifact `_site` có asset/URL tương đối", "Xác minh đường build GitHub Pages tại evidence hiện hành."),
        ], widths=[3.6, 5.0, 7.9], font_size=8.5)
        add_paragraph(document, "Các con số trên lấy từ tài liệu evidence của release hiện hành; chúng được tái chạy trong quy trình hoàn tất báo cáo nếu môi trường có đủ dữ liệu và công cụ. Một test pass xác nhận assertion tương ứng, không thay thế kiểm thử bảo mật độc lập.")
        add_figure(document, test_evidence_path, "Hình 4.3. Tổng hợp bằng chứng kiểm thử thực thi cục bộ; không phải ảnh chụp terminal.", width=15.0)
        add_heading(document, "4.6. Hướng dẫn thao tác và giao diện thực tế", 2)
        add_paragraph(document, "Các bước dưới đây mô tả luồng thao tác an toàn trên backend Flask tại `http://127.0.0.1:5000/`. Ảnh trang chủ được chụp từ ứng dụng đang chạy; URL ví dụ không chứa thông tin đăng nhập.", first_line=False)
        add_bullets(document, [
            "Nhập URL cần kiểm tra; xem dòng URL đã chuẩn hóa trước khi phân tích. Không dán URL riêng tư, token hoặc mật khẩu.",
            "Mặc định SafeWeb chỉ phân tích cục bộ. Chỉ bật kiểm tra trực tuyến nếu chấp nhận gửi URL tới các dịch vụ DNS/preview được nêu trong giao diện.",
            "Chọn Phân tích URL; đọc riêng kết quả tra cứu cơ sở dữ liệu, xác suất từng mô hình, mức rủi ro, tín hiệu và khuyến nghị. Mức rủi ro thấp không chứng nhận trang an toàn.",
            "Mở Cơ sở dữ liệu URL để tìm/lọc bản ghi; URL trong kho được hiển thị để tham khảo, không cần mở trang đích.",
        ], numbered=True)
        add_figure(document, homepage_path, "Hình 4.4. Giao diện trang chủ SafeWeb trên backend Flask.", width=15.0)
        add_heading(document, "4.7. Tính năng bổ sung và ranh giới tin cậy", 2)
        add_paragraph(document, "DNS resolve không đồng nghĩa domain đáng tin; metadata/ảnh preview là dữ liệu do dịch vụ bên thứ ba trả về; redirect chỉ đầy đủ trong giới hạn trình duyệt và CORS; phân loại brand/provider là luật nhận diện chuỗi chứ không kiểm tra quyền sở hữu. Mẫu phishing đối ứng chỉ mang tính giáo dục. Easter egg của URL dự án là nhánh demo. Các nguồn này phải được trình bày độc lập với xác suất ML để tránh tạo cảm giác một phép kiểm tra đơn lẻ đã “chứng nhận” website.")

    # Chapter 5
    add_heading(document, "CHƯƠNG 5. ĐÁNH GIÁ SẢN PHẨM, KẾT LUẬN VÀ KIẾN NGHỊ", 1)
    add_heading(document, "5.1. Mức độ đạt mục tiêu kỹ thuật", 2)
    add_paragraph(document, "Nguyên mẫu hoàn thành phân tích URL cục bộ, tra cứu tham chiếu, 55 feature, bốn model trên trình duyệt, explorer và live checks có consent. Parity/build xác nhận triển khai nhất quán trong phạm vi test. SVM có recall rất thấp; cần hiệu chỉnh trên validation trước khi tin cậy ensemble.")
    add_heading(document, "5.2. Kết luận", 2)
    add_paragraph(document, "SafeWeb khả thi như nguyên mẫu cảnh báo sớm URL, chạy cục bộ mặc định. Trên test giữ riêng, Gradient Boosting đạt F1 0,8697/recall 0,9561; SVM gần như bỏ sót phishing ở threshold hiện tại. Đây là công cụ giáo dục/sàng lọc, không phải bộ bảo vệ hay chứng nhận an toàn.")
    add_heading(document, "5.3. Hạn chế", 2)
    add_bullets(document, [
        "SVM cần hiệu chỉnh threshold trên validation; không chọn threshold bằng test.",
        "Không match database không đồng nghĩa an toàn; coverage/nhãn thay đổi theo nguồn và thời gian.",
        "Model chỉ phân tích URL, không đọc HTML, TLS, tuổi domain, reputation hay script; keyword có thể gây bias/false positive.",
        "Domain-disjoint không loại hết campaign leakage hoặc dataset drift; benchmark không đại diện mọi môi trường.",
        "Live checks phụ thuộc dịch vụ/CORS và chia sẻ URL sau consent; chưa có usability/accessibility study.",
    ])
    add_heading(document, "5.4. Hướng phát triển: tiện ích mở rộng quét liên kết trong viewport", 2)
    add_paragraph(document, "Hướng phát triển là extension quét anchor trong viewport, chuẩn hóa/khử trùng URL, suy luận cục bộ và cảnh báo không chặn. Bắt buộc opt-in, permission tối thiểu, không đọc form/credential, không gửi URL mặc định; đánh giá latency, FP và tương thích SPA trước phát hành.")
    add_heading(document, "5.5. Kế hoạch cải tiến theo giai đoạn", 2)
    add_table(document, ["Giai đoạn", "Công việc", "Tiêu chí nghiệm thu"], [
        ("V2.4", "Hiệu chỉnh SVM trên validation; so sánh ensemble.", "Khóa threshold trước test; báo recall, precision, calibration."),
        ("V2.5", "Giải thích feature; thêm ca IDN/adversarial.", "Lý do truy về feature; test Unicode."),
        ("V3", "Extension quét viewport opt-in.", "Không gửi URL mặc định; audit permission/usability/performance."),
    ], widths=[2.2, 7.2, 6.8], font_size=7.8)

    add_heading(document, "TÀI LIỆU THAM KHẢO", 1)
    references = [
        "Berners-Lee, T., Fielding, R., & Masinter, L. (2005). Uniform Resource Identifier (URI): Generic syntax (RFC 3986). Internet Engineering Task Force. https://doi.org/10.17487/RFC3986",
        "Breiman, L. (2001). Random forests. Machine Learning, 45, 5–32. https://doi.org/10.1023/A:1010933404324",
        "Cortes, C., & Vapnik, V. (1995). Support-vector networks. Machine Learning, 20, 273–297. https://doi.org/10.1007/BF00994018",
        "Fielding, R., Nottingham, M., & Reschke, J. (Eds.). (2022). HTTP semantics (RFC 9110). Internet Engineering Task Force. https://doi.org/10.17487/RFC9110",
        "Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. The Annals of Statistics, 29(5), 1189–1232. https://doi.org/10.1214/aos/1013203451",
        "Mockapetris, P. (1987). Domain names—Implementation and specification (RFC 1035). Internet Engineering Task Force. https://doi.org/10.17487/RFC1035",
        "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.",
        "PhiUSIIL Phishing URL Dataset. (n.d.). URL and label archive used for source-balanced model fitting. Dataset attribution and audit recorded in SafeWeb ML Experiment Report.",
        "SafeWeb. (2026). Tài liệu kỹ thuật, báo cáo thí nghiệm học máy, metrics.json, phishvn_domain_eval.json và mã nguồn [Tài liệu dự án và phần mềm].",
        "Thai Nguyen Vu. (2026). PhishVN: A time-stamped Vietnamese URL phishing dataset with impersonation-scenario labels and confidence tiers (Version 3.1.0) [Data set]. Mendeley Data. https://doi.org/10.17632/b97hxbxtpd.4",
    ]
    for item in references:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(0.8)
        paragraph.paragraph_format.first_line_indent = Cm(-0.8)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.keep_together = True
        set_run_font(paragraph.add_run(item), size=8.5)

    # Appendices
    document.add_page_break()
    add_heading(document, "PHỤ LỤC A. PHIÊN DỊCH THUẬT NGỮ CHUYÊN NGÀNH", 1)
    terms = [
        ("Phishing", "Lừa đảo trực tuyến", "Trang/URL giả mạo nhằm chiếm đoạt thông tin hoặc dẫn dụ hành động."),
        ("URL (Uniform Resource Locator)", "Bộ định vị tài nguyên thống nhất", "Chuỗi định vị tài nguyên web."),
        ("Machine Learning (ML)", "Học máy", "Phương pháp học quy luật từ dữ liệu."),
        ("Binary classification", "Phân loại nhị phân", "Phân lớp benign và phishing."),
        ("Feature / feature vector", "Đặc trưng / véc-tơ đặc trưng", "Các giá trị số mô tả một URL theo thứ tự schema."),
        ("Feature extraction", "Trích xuất đặc trưng", "Tính các biến từ chuỗi URL và hồ sơ dữ liệu."),
        ("Domain-disjoint split", "Tách biệt theo tên miền", "Tách để domain đăng ký không xuất hiện ở cả train và test."),
        ("Browser inference", "Suy luận trong trình duyệt", "Thực thi mô hình JavaScript trên máy người dùng."),
        ("Ensemble", "Tổ hợp mô hình", "Kết hợp nhiều bộ phân loại; ở SafeWeb là trung bình xác suất."),
        ("Random Forest", "Rừng ngẫu nhiên", "Tổ hợp cây quyết định lấy mẫu ngẫu nhiên."),
        ("Gradient Boosting", "Tăng cường gradient", "Học tuần tự các bộ học yếu theo gradient mất mát."),
        ("Support Vector Machine (SVM)", "Máy véc-tơ hỗ trợ", "Phân loại dựa trên biên phân tách; SafeWeb dùng LinearSVC."),
        ("Logistic Regression", "Hồi quy logistic", "Mô hình tuyến tính xác suất dùng sigmoid."),
        ("Calibration", "Hiệu chuẩn xác suất", "Ánh xạ score sang xác suất; không đảm bảo calibration hoàn hảo."),
        ("Threshold", "Ngưỡng quyết định", "Ranh giới biến xác suất thành nhãn hoặc tier."),
        ("Precision", "Độ chính xác dương", "TP / (TP + FP) cho lớp đang xét."),
        ("Recall", "Độ bao phủ / độ nhạy", "TP / (TP + FN) cho lớp đang xét."),
        ("F1-score", "Điểm F1", "Trung bình điều hòa của precision và recall."),
        ("ROC-AUC", "Diện tích dưới đường ROC", "Đánh giá xếp hạng trên nhiều ngưỡng."),
        ("Confusion matrix", "Ma trận nhầm lẫn", "Bảng đếm dự đoán đúng/sai theo lớp."),
        ("False positive / false negative", "Dương tính giả / âm tính giả", "Cảnh báo nhầm / bỏ sót URL phishing."),
        ("Canonicalization", "Chuẩn hóa dạng chuẩn", "Biến thể URL được quy về biểu diễn nhất quán."),
        ("Registrable domain", "Tên miền có thể đăng ký", "Phần domain cấp đăng ký theo public suffix rules."),
        ("Public Suffix List", "Danh sách hậu tố công cộng", "Quy tắc xác định ranh giới suffix và registrable domain."),
        ("Entropy", "Entropy / độ hỗn loạn ký tự", "Độ phân bố thông tin ký tự theo Shannon; không phải mức độc hại."),
        ("Percent-encoding", "Mã hóa phần trăm", "Biểu diễn byte bằng chuỗi `%xx` trong URL."),
        ("Feature signature", "Chữ ký đặc trưng", "Chuỗi đặc trưng chuẩn hóa dùng đối chiếu chỉ mục."),
        ("Data provenance", "Nguồn gốc dữ liệu", "Nguồn, nhãn, thời điểm và lịch sử biến đổi của bản ghi."),
        ("Held-out test set", "Tập kiểm thử giữ riêng", "Dữ liệu không dùng trong fit/tuning chính."),
        ("Data leakage", "Rò rỉ dữ liệu", "Thông tin test vô tình ảnh hưởng huấn luyện hoặc chọn mô hình."),
        ("DNS over HTTPS (DoH)", "DNS qua HTTPS", "Tra cứu DNS qua giao thức HTTPS."),
        ("Redirect chain", "Chuỗi chuyển hướng", "Dãy đích URL qua các bước HTTP hoặc tham số nhúng."),
        ("Cross-Origin Resource Sharing (CORS)", "Chia sẻ tài nguyên khác nguồn", "Chính sách trình duyệt có thể chặn đọc phản hồi cross-origin."),
        ("Metadata", "Siêu dữ liệu trang", "Tiêu đề/mô tả/thuộc tính được dịch vụ preview trả về."),
        ("Consent gate", "Cổng đồng ý", "Bước yêu cầu người dùng cho phép trước khi chia sẻ URL."),
        ("Parity check", "Kiểm tra tương đương", "Đối chiếu đầu ra của hai hiện thực trên cùng bộ ca."),
        ("Viewport scanner", "Bộ quét vùng nhìn", "Tiện ích phát hiện liên kết đang hiển thị trên khung nhìn."),
        ("Prototype", "Nguyên mẫu", "Phiên bản chứng minh tính khả thi, chưa phải sản phẩm chứng nhận."),
    ]
    add_table(document, ["English term", "Thuật ngữ tiếng Việt", "Ý nghĩa trong báo cáo"], terms, widths=[4.4, 4.5, 6.8], font_size=7.6)

    add_heading(document, "PHỤ LỤC B. QUY TRÌNH TÁI LẬP", 1)
    add_paragraph(document, "Tái lập theo thứ tự: `python scripts/prepare_phishvn_dataset.py` → `python scripts/train_phishvn_model.py` → `python scripts/export_browser_model.py` → `python scripts/compare_browser_model.py` → `python -m pytest -q` → `npm run test:browser` → `npm run build`. Cần có archive PhishVN/PhiUSIIL và các dependency tương ứng.", first_line=False)

    document.add_page_break()
    back = document.add_paragraph()
    back.alignment = WD_ALIGN_PARAGRAPH.CENTER
    back.paragraph_format.space_before = Pt(170)
    set_run_font(back.add_run("SAFEWEB"), size=25, bold=True, color=NAVY)
    back_subtitle = document.add_paragraph()
    back_subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(back_subtitle.add_run("ĐỌC TÍN HIỆU URL — GIỮ NGUYÊN BỐI CẢNH"), size=13, bold=True, color=TEAL)
    back_body = document.add_paragraph()
    back_body.alignment = WD_ALIGN_PARAGRAPH.CENTER
    back_body.paragraph_format.space_before = Pt(28)
    back_body.paragraph_format.left_indent = Cm(2)
    back_body.paragraph_format.right_indent = Cm(2)
    set_run_font(back_body.add_run("Công cụ nghiên cứu giáo dục hỗ trợ đánh giá URL. Kết quả là tín hiệu tham khảo, không thay thế việc xác minh qua kênh chính thức và không chứng nhận một trang web an toàn hay độc hại."), size=11, color=MUTED)
    credit_heading = document.add_paragraph()
    credit_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    credit_heading.paragraph_format.space_before = Pt(100)
    credit_heading.paragraph_format.space_after = Pt(8)
    set_run_font(credit_heading.add_run("NHÓM THỰC HIỆN VÀ NGƯỜI HƯỚNG DẪN"), size=10, bold=True, color=NAVY)
    credits = document.add_table(rows=3, cols=2)
    credits.alignment = WD_TABLE_ALIGNMENT.CENTER
    credits.autofit = False
    credit_rows = [
        ("Người thực hiện 1", "Lê Văn Tuấn Anh"),
        ("Người thực hiện 2", "Nguyễn Hoàng Bảo"),
        ("Người hướng dẫn", "Trần Văn Toàn"),
    ]
    for row, (role, name) in zip(credits.rows, credit_rows, strict=True):
        row.cells[0].text = role
        row.cells[1].text = name
        row.cells[0].width = Cm(4.2)
        row.cells[1].width = Cm(6.0)
        for column, cell in enumerate(row.cells):
            set_cell_margins(cell, top=95, bottom=95)
            set_cell_shading(cell, PALE_BLUE if column == 0 else "F7F9FA")
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    set_run_font(run, size=10, bold=column == 0, color=NAVY if column == 0 else INK)

    settings = document.settings._element
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    settings.append(update_fields)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)


def main():
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    evaluation = json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))
    if metrics["train_rows"] != 261299 or metrics["test_rows"] != 6624 or len(metrics["evaluations"]) != 4:
        raise ValueError("Current metrics do not match the documented SafeWeb evaluation.")
    if not evaluation.get("test_domains_disjoint_from_training"):
        raise ValueError("The held-out PhishVN test set is not marked domain-disjoint.")
    write_document(metrics, evaluation, OUTPUT_PATH)
    print(f"Generated {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size:,} bytes).")


if __name__ == "__main__":
    main()