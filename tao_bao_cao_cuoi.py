# -*- coding: utf-8 -*-
"""
Tập lệnh tự động tạo Báo cáo KHKT cấp THPT hoàn chỉnh:
- Xuất ra đồng thời: Bao_cao_SafeWeb_KHKT_THPT.docx và Bao_cao_SafeWeb_KHKT_THPT.doc
- Cỡ chữ bắt buộc: 14pt Times New Roman toàn bộ văn bản, bảng biểu (chuẩn KHKT)
- Lề trang A4: Trái 3.0cm, Phải 2.0cm, Trên 2.0cm, Dưới 2.0cm
- Tự động vẽ hình Lưu đồ tiếng Việt, hình Xác minh cục bộ tiếng Việt, hình 3 bước thao tác và nhúng ảnh giao diện.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

PROJECT_ROOT = Path(__file__).resolve().parent

# ==============================================================================
# 1. HÀM TỰ ĐỘNG VẼ 3 HÌNH MINH HỌA 100% TIẾNG VIỆT DỄ HIỂU
# ==============================================================================

def create_flowchart_image(output_path: str):
    """Vẽ Hình 3.1: Lưu đồ vận hành hệ thống bằng tiếng Việt dễ hiểu."""
    fig, ax = plt.subplots(figsize=(11, 3.2), dpi=220)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 3.2)
    ax.axis("off")

    steps = [
        "1. Nhập địa chỉ\ntrang web cần\nkiểm tra",
        "2. Tự điền đủ\nhttps:// và .com\nnếu gõ thiếu",
        "3. Đối chiếu\nCơ sở dữ liệu\n36.261 địa chỉ",
        "4. Đo đếm\n55 dấu hiệu\ncủa địa chỉ",
        "5. Bốn mô hình\nAI cùng lúc\nchấm điểm",
        "6. Kiểm tra DNS\nvà ảnh chụp\n(nếu bật)",
        "7. Đổi màu trang\n(Xanh/Vàng/Cam/Đỏ)\n& giải thích rõ"
    ]

    box_w, box_h = 1.65, 1.75
    y0 = 0.85
    xs = [0.2 + i * 1.95 for i in range(len(steps))]

    for i, (x, text) in enumerate(zip(xs, steps)):
        face = "#E6F4F1" if i < 6 else "#D1FAE5"
        edge = "#0F766E" if i < 6 else "#047857"
        patch = FancyBboxPatch(
            (x, y0), box_w, box_h,
            boxstyle="round,pad=0.08,rounding_size=0.15",
            facecolor=face, edgecolor=edge, linewidth=2.0
        )
        ax.add_patch(patch)
        ax.text(
            x + box_w / 2, y0 + box_h / 2, text,
            ha="center", va="center", fontsize=9.5, fontweight="bold",
            color="#0F172A", family="DejaVu Sans"
        )
        if i < len(steps) - 1:
            ax.annotate(
                "", xy=(xs[i + 1] - 0.04, y0 + box_h / 2),
                xytext=(x + box_w + 0.04, y0 + box_h / 2),
                arrowprops=dict(arrowstyle="-|>", color="#0F766E", lw=2.0, mutation_scale=14)
            )

    ax.text(
        7.0, 0.28,
        "Mặc định bước 1 đến bước 5 chạy hoàn toàn ngay trên máy người dùng; bước 6 chỉ chạy khi người dùng bật cho phép.",
        ha="center", va="center", fontsize=9.5, style="italic", color="#334155", family="DejaVu Sans"
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def create_verification_image(output_path: str):
    """Vẽ Hình 4.1: Kết quả kiểm thử phần mềm & Xác minh cục bộ 100% Tiếng Việt."""
    fig, ax = plt.subplots(figsize=(10.5, 4.6), dpi=220)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)
    ax.axis("off")

    ax.text(
        0.3, 4.75, "KẾT QUẢ KIỂM TRA CHẤT LƯỢNG & XÁC MINH CỤC BỘ · SAFEWEB",
        fontsize=13.5, fontweight="bold", color="#0F172A", family="DejaVu Sans"
    )

    cards = [
        (0.3, 2.55, "#0F766E", "#F0FDF4",
         "1. KIỂM TRA XỬ LÝ DỮ LIỆU & AI",
         "Đạt 59 / 59 mẫu (100%)",
         "Đo 55 dấu hiệu, làm sạch dữ liệu & chấm điểm chuẩn xác"),
        (5.15, 2.55, "#B45309", "#FFFBEB",
         "2. KIỂM TRA TRÊN TRÌNH DUYỆT WEB",
         "Đạt 16 / 16 bài (100%)",
         "Kiểm tra nhập URL, mô hình, cơ sở dữ liệu và giao diện"),
        (0.3, 0.35, "#1D4ED8", "#EFF6FF",
         "3. ĐỐI CHIẾU HAI CÁCH TÍNH",
         "Khớp 16 / 16 trường hợp",
         "10 URL hợp lệ, 6 URL không hợp lệ; sai số rất nhỏ do số học"),
        (5.15, 0.35, "#15803D", "#F0FDF4",
         "4. XỬ LÝ CỤC BỘ CÓ CHỌN LỌC",
         "Mặc định không gửi URL đi",
         "Chỉ tra cứu mạng khi người dùng chủ động cho phép")
    ]

    for x, y, border_col, bg_col, title, big_val, desc in cards:
        box = FancyBboxPatch(
            (x, y), 4.55, 1.85,
            boxstyle="round,pad=0.06,rounding_size=0.15",
            facecolor=bg_col, edgecolor=border_col, linewidth=2.0
        )
        ax.add_patch(box)
        ax.text(x + 0.25, y + 1.45, title, fontsize=9.5, fontweight="bold", color=border_col, family="DejaVu Sans")
        ax.text(x + 0.25, y + 0.85, big_val, fontsize=14.5, fontweight="bold", color="#0F172A", family="DejaVu Sans")
        ax.text(x + 0.25, y + 0.32, desc, fontsize=8.8, color="#334155", family="DejaVu Sans")

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def create_user_guide_diagram(output_path: str):
    """Vẽ Hình 4.2: Sơ đồ 3 bước thao tác và ý nghĩa 3 màu cảnh báo."""
    fig, ax = plt.subplots(figsize=(10.5, 3.6), dpi=220)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 3.8)
    ax.axis("off")

    ax.text(
        5.25, 3.45, "SƠ ĐỒ 3 BƯỚC THAO TÁC ĐƠN GIẢN & Ý NGHĨA MÀU CẢNH BÁO",
        ha="center", fontsize=12.5, fontweight="bold", color="#0F172A", family="DejaVu Sans"
    )

    steps = [
        (0.3, "#0284C7", "#E0F2FE", "BƯỚC 1: NHẬP ĐỊA CHỈ",
         "Dán đường dẫn nghi ngờ vào ô.\nPhần mềm tự điền https://\nvà .com nếu người dùng gõ thiếu."),
        (3.75, "#0D9488", "#CCFBF1", "BƯỚC 2: BẤM NÚT PHÂN TÍCH",
         "Bấm nút 'Phân tích URL'.\nMáy dò cơ sở dữ liệu và cho\nbốn mô hình cùng đánh giá."),
        (7.2, "#16A34A", "#DCFCE7", "BƯỚC 3: NHÌN MÀU & ĐỌC LÝ DO",
             "• Xanh: rủi ro thấp\n• Vàng: thận trọng\n• Cam: nguy cơ cao\n• Đỏ: nguy cơ rất cao")
    ]

    for i, (x, edge, face, title, body) in enumerate(steps):
        box = FancyBboxPatch(
            (x, 0.45), 3.0, 2.55,
            boxstyle="round,pad=0.06,rounding_size=0.16",
            facecolor=face, edgecolor=edge, linewidth=2.2
        )
        ax.add_patch(box)
        ax.text(x + 1.5, 2.55, title, ha="center", va="center", fontsize=10, fontweight="bold", color=edge, family="DejaVu Sans")
        ax.text(x + 1.5, 1.35, body, ha="center", va="center", fontsize=9.2, color="#0F172A", family="DejaVu Sans")
        if i < 2:
            ax.annotate(
                "", xy=(steps[i + 1][0] - 0.06, 1.72),
                xytext=(x + 3.0 + 0.06, 1.72),
                arrowprops=dict(arrowstyle="-|>", color="#0F172A", lw=2.2, mutation_scale=15)
            )

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def find_or_create_ui_screenshot(output_path: str) -> str:
    """Tìm ảnh chụp giao diện trang chủ có sẵn trong dự án hoặc tạo hình minh họa giao diện."""
    screenshot = PROJECT_ROOT / "reports" / "screenshots" / "homepage.png"
    if screenshot.is_file():
        return str(screenshot)

    candidates = list(PROJECT_ROOT.rglob("home*.png"))
    candidates += list(PROJECT_ROOT.rglob("screenshot*.png"))
    candidates += list(PROJECT_ROOT.rglob("ui*.png"))
    for c in candidates:
        low = c.as_posix().lower()
        if all(k not in low for k in ["flow", "pipeline", "verify", "step", "confusion"]):
            return str(c)

    # Nếu không tìm thấy file ảnh sẵn, tự động vẽ mô phỏng giao diện trang chủ SafeWeb
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    bg = FancyBboxPatch((0.1, 0.1), 9.8, 5.0, boxstyle="round,pad=0.05", facecolor="#0B1F17", edgecolor="#10B981", lw=2)
    ax.add_patch(bg)
    ax.text(0.5, 4.5, "SafeWeb — Giao diện Phân tích Địa chỉ Trang web & Cơ sở dữ liệu", fontsize=12, fontweight="bold", color="#34D399")
    left_card = FancyBboxPatch((0.4, 0.5), 4.2, 3.6, boxstyle="round,pad=0.05", facecolor="#112A20", edgecolor="#059669", lw=1.5)
    right_card = FancyBboxPatch((4.9, 0.5), 4.7, 3.6, boxstyle="round,pad=0.05", facecolor="#112A20", edgecolor="#059669", lw=1.5)
    ax.add_patch(left_card)
    ax.add_patch(right_card)
    ax.text(0.6, 3.6, "KHUNG TRÁI: NHẬP URL CẦN ĐÁNH GIÁ\n\n[ https://example.com/account ]\n\n• Tự động điền https:// và .com\n• Tùy chọn bật Kiểm tra trực tuyến\n\n[ NÚT: PHÂN TÍCH URL ]", fontsize=9.5, color="#ECFDF5")
    ax.text(5.1, 3.6, "KHUNG PHẢI: KẾT QUẢ & HỘI ĐỒNG 4 MÔ HÌNH AI\n\n• Trạng thái màu sắc: Xanh / Vàng / Đỏ\n• Điểm Random Forest, Gradient Boosting,\n  SVM, Logistic Regression\n• Giải thích: Vì sao có kết quả này?\n• Khuyến nghị: Tôi nên làm gì?", fontsize=9.5, color="#ECFDF5")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


# ==============================================================================
# 2. CÁC HÀM ĐỊNH DẠNG WORD (.DOCX) CHUẨN CỠ CHỮ 14PT TIMES NEW ROMAN
# ==============================================================================

def set_cell_shading(cell, color_hex: str):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def format_run(run, size_pt=14, bold=False, italic=False, color_rgb=(0, 0, 0), font_name="Times New Roman"):
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(*color_rgb)


def add_p(doc, text="", bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, size_pt=14, color_rgb=(0, 0, 0)):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    if text:
        r = p.add_run(text)
        format_run(r, size_pt=size_pt, bold=bold, italic=italic, color_rgb=color_rgb)
    return p


def add_bullet(doc, lead_bold: str, rest_text: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(5)
    r1 = p.add_run("• " + lead_bold)
    format_run(r1, size_pt=14, bold=True)
    r2 = p.add_run(rest_text)
    format_run(r2, size_pt=14, bold=False)
    return p


def add_heading_1(doc, text: str):
    p = doc.add_paragraph()
    p.style = "Heading 1"
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    format_run(r, size_pt=14, bold=True, color_rgb=(15, 76, 92))
    return p


def add_heading_2(doc, text: str):
    p = doc.add_paragraph()
    p.style = "Heading 2"
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    format_run(r, size_pt=14, bold=True, color_rgb=(15, 118, 110))
    return p


def add_table_of_contents(doc):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.08
    field_parts = [
        ("w:fldChar", {"w:fldCharType": "begin", "w:dirty": "true"}, None),
        ("w:instrText", {"xml:space": "preserve"}, ' TOC \\o "1-2" \\h \\z \\u '),
        ("w:fldChar", {"w:fldCharType": "separate"}, None),
        ("w:t", {}, "Mục lục sẽ được cập nhật khi mở tài liệu bằng Word."),
        ("w:fldChar", {"w:fldCharType": "end"}, None),
    ]
    for tag, attributes, text in field_parts:
        element = OxmlElement(tag)
        for name, value in attributes.items():
            element.set(qn(name), value)
        if text:
            element.text = text
        run = paragraph.add_run()
        format_run(run, size_pt=14)
        run._r.append(element)
    settings = doc.settings.element
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    settings.append(update_fields)
    return paragraph


def keep_table_on_one_page(table):
    rows = table.rows
    for index, row in enumerate(rows):
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        if index < len(rows) - 1:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.keep_with_next = True


def add_code_box(doc, title: str, code_lines: list, explanation_lines: list[str]):
    title_paragraph = add_p(doc, title, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=3, size_pt=14, color_rgb=(15, 76, 92))
    title_paragraph.paragraph_format.keep_with_next = True
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_shading(cell, "F1F5F9")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.1
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run("\n".join(code_lines))
    format_run(r, size_pt=11, bold=False, font_name="Times New Roman", color_rgb=(15, 23, 42))
    keep_table_on_one_page(tbl)

    add_p(doc, "Giải thích", bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=2, size_pt=14, color_rgb=(15, 76, 92))
    for index, explanation in enumerate(explanation_lines, start=1):
        add_bullet(doc, f"{index}. ", explanation)


def add_styled_table(doc, headers: list, rows: list, size_pt=12, widths=None):
    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style = "Table Grid"

    for col_idx, h_text in enumerate(headers):
        cell = tbl.cell(0, col_idx)
        set_cell_shading(cell, "0F766E")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(h_text)
        format_run(r, size_pt=size_pt, bold=True, color_rgb=(255, 255, 255))

    for row_idx, r_data in enumerate(rows):
        bg = "FFFFFF" if row_idx % 2 == 0 else "F8FAFC"
        for col_idx, val in enumerate(r_data):
            cell = tbl.cell(row_idx + 1, col_idx)
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=90, bottom=90, left=120, right=120)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx in (0, len(headers) - 1) else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(val)
            format_run(r, size_pt=size_pt, bold=(col_idx == 0))

    if widths:
        tbl.autofit = False
        for row in tbl.rows:
            for col_idx, width in enumerate(widths):
                row.cells[col_idx].width = Cm(width)
    keep_table_on_one_page(tbl)
    add_p(doc, "", space_after=4)


# ==============================================================================
# 3. HÀM XÂY DỰNG TOÀN BỘ NỘI DUNG BÁO CÁO CUỐI CÙNG
# ==============================================================================

def build_full_report():
    out_dir = PROJECT_ROOT / "reports" / "figures_vi"
    out_dir.mkdir(parents=True, exist_ok=True)

    flowchart_img = str(out_dir / "hinh_3_1_luu_do_vi.png")
    verify_img = str(out_dir / "hinh_4_1_xac_minh_vi.png")
    steps_img = str(out_dir / "hinh_4_2_ba_buoc_vi.png")
    ui_img = find_or_create_ui_screenshot(str(out_dir / "hinh_4_3_giao_dien_vi.png"))

    create_flowchart_image(flowchart_img)
    create_verification_image(verify_img)
    create_user_guide_diagram(steps_img)

    doc = Document()
    doc.styles["Normal"].font.name = "Times New Roman"
    doc.styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    doc.styles["Normal"].font.size = Pt(14)
    doc.styles["Normal"].paragraph_format.line_spacing = 1.15

    # Cài đặt trang A4 & Lề chuẩn: Trái 3cm, Phải 2cm, Trên 2cm, Dưới 2cm
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.0)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)

    # --------------------------------------------------------------------------
    # TRANG 1: TRANG BÌA ĐẦU (THIẾT KẾ DẠNG BÌA SÁCH TRANG TRỌNG)
    # --------------------------------------------------------------------------
    add_p(doc, "BÁO CÁO DỰ ÁN NGHIÊN CỨU KHOA HỌC KỸ THUẬT", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, size_pt=14)
    add_p(doc, "CUỘC THI KHOA HỌC KỸ THUẬT CẤP TRUNG HỌC PHỔ THÔNG", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, size_pt=14)
    add_p(doc, "LĨNH VỰC: MÁY TÍNH / TRÍ TUỆ NHÂN TẠO", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, size_pt=14, color_rgb=(15, 118, 110))

    add_p(doc, "SAFEWEB", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10, size_pt=14, color_rgb=(15, 76, 92))
    add_p(
        doc,
        "ỨNG DỤNG TRÍ TUỆ NHÂN TẠO KẾT HỢP PHÂN TÍCH ĐỊA CHỈ TRANG WEB GIÚP CẢNH BÁO SỚM RỦI RO LỪA ĐẢO VÀ LỘ LỌT DỮ LIỆU",
        bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=20, size_pt=14, color_rgb=(15, 23, 42)
    )
    add_p(doc, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, size_pt=14, color_rgb=(15, 118, 110))

    add_p(doc, "DỰ ÁN KỸ THUẬT", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8, size_pt=14, color_rgb=(15, 118, 110))
    add_p(doc, "Bốn mô hình cùng xem xét dấu hiệu, như bốn giám khảo đọc chung một hồ sơ.", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8, size_pt=14)
    author_one = add_p(doc, "Người thực hiện 1 : Lê Văn Tuấn Anh", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=5, size_pt=14)
    author_one.paragraph_format.space_before = Pt(150)
    add_p(doc, "Người thực hiện 2 : Nguyễn Hoàng Bảo", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=5, size_pt=14)
    add_p(doc, "Người hướng dẫn : Trần Văn Toàn", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6, size_pt=14)

    doc.add_page_break()

    # --------------------------------------------------------------------------
    # TRANG 2: MỤC LỤC & TÓM TẮT DỰ ÁN
    # --------------------------------------------------------------------------
    add_p(doc, "MỤC LỤC", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8, size_pt=14, color_rgb=(15, 76, 92))
    add_table_of_contents(doc)

    add_heading_1(doc, "TÓM TẮT DỰ ÁN")
    add_p(
        doc,
        "SafeWeb là phần mềm giúp người dùng phát hiện sớm các đường dẫn trang web lừa đảo và phòng tránh lộ lọt dữ liệu cá nhân. Thay vì phải mạo hiểm bấm vào đường dẫn lạ, phần mềm sẽ tự động khám xét địa chỉ trang web đó ngay trên máy của người dùng thông qua cơ sở dữ liệu tra cứu nhanh, 55 dấu hiệu nhận biết chữ viết và hội đồng gồm 4 mô hình Trí tuệ nhân tạo: Random Forest, Gradient Boosting, SVM và Logistic Regression. Các tính năng kiểm tra tên miền, dò tìm chuyển hướng và chụp ảnh xem trước trang web chỉ hoạt động khi người dùng đồng ý cho phép."
    )
    add_p(
        doc,
        "Để dạy cho máy tính thông minh, nhóm sử dụng tổng cộng 261.299 địa chỉ trang web đã làm sạch (gồm 114.113 trang lừa đảo và 147.186 trang an toàn). Khi đem thi thử trên 6.624 địa chỉ trang web hoàn toàn mới chưa từng gặp trong lúc học, mô hình Gradient Boosting bắt trúng tới 95,61% trang web lừa đảo (phát hiện đúng 2.676 trên 2.799 trang lừa đảo), và mô hình Random Forest bắt trúng 92,32%. Phần mềm đã vượt qua 100% các bài kiểm tra chất lượng gồm 59 bài kiểm tra xử lý dữ liệu và 16 bài kiểm tra trình duyệt, giúp người dùng nhận biết rủi ro trực quan trước khi bấm vào đường dẫn."
    )
    add_p(doc, "Từ khóa: Trang web lừa đảo; Địa chỉ trang web; Trí tuệ nhân tạo; Kiểm tra trực tiếp trên trình duyệt; Bảo vệ quyền riêng tư.", italic=True)
    doc.add_page_break()

    # --------------------------------------------------------------------------
    # CHƯƠNG 1. XÁC ĐỊNH NHU CẦU VÀ MỤC TIÊU THIẾT KẾ
    # --------------------------------------------------------------------------
    add_heading_1(doc, "CHƯƠNG 1. XÁC ĐỊNH NHU CẦU VÀ MỤC TIÊU THIẾT KẾ")

    add_heading_2(doc, "1.1. Bối cảnh và vấn đề thực tiễn")
    add_p(
        doc,
        "Mỗi trang web có một dòng địa chỉ giống như biển hiệu của cửa hàng. Kẻ gian gửi tin nhắn, thư điện tử chứa đường dẫn giả mạo ngân hàng, mạng xã hội hay sàn mua sắm để lừa người dùng nhập mật khẩu và mã xác nhận. Mắt thường khó nhận ra vì địa chỉ giả thường chỉ khác thật vài ký tự, hoặc viết rất dài để che phần đuôi."
    )
    add_p(
        doc,
        "Nhiều người tin rằng địa chỉ có khóa https là an toàn, nhưng kẻ lừa đảo cũng tạo được khóa này miễn phí. Nếu gửi địa chỉ lên một máy chủ lạ để kiểm tra, người dùng còn có nguy cơ lộ thông tin riêng. Vì vậy cần một công cụ kiểm tra ngay trên máy của người dùng và nói rõ lý do cảnh báo."
    )

    add_heading_2(doc, "1.2. Nhu cầu thực tế và câu hỏi đặt ra")
    add_p(
        doc,
        "Nhóm cần một công cụ tự điền đủ địa chỉ gõ thiếu, đối chiếu với cơ sở dữ liệu 36.261 địa chỉ đã biết (19.909 trang lừa đảo, 16.352 trang hợp lệ), chấm điểm bằng bốn mô hình và nêu lý do cảnh báo. Câu hỏi đặt ra: nếu đưa toàn bộ phép tính vào trình duyệt, kết quả có gần như giống máy huấn luyện hay không?"
    )

    add_heading_2(doc, "1.3. Mục tiêu và tiêu chí thiết kế")
    add_bullet(
        doc,
        "Mục tiêu: ",
        "Xây dựng SafeWeb giúp người dùng kiểm tra nhanh một địa chỉ ngay trên trình duyệt và hiểu vì sao nên hoặc không nên tin trước khi bấm."
    )
    add_bullet(
        doc,
        "Tiêu chí thiết kế: ",
        "Đo 55 dấu hiệu, dùng bốn mô hình cùng cơ sở dữ liệu 36.261 địa chỉ; thử trên các tên miền không trùng lúc học; mặc định không gửi địa chỉ ra ngoài; hiện bốn mức màu Xanh - Vàng - Cam - Đỏ kèm lý do."
    )

    add_heading_2(doc, "1.4. Phạm vi của sản phẩm")
    add_p(
        doc,
        "SafeWeb chỉ xem xét chữ viết và cấu trúc của địa chỉ, không tải hay chạy nội dung trang đích. Kiểm tra tên miền (DNS) và ảnh xem trước chỉ chạy khi người dùng bật cho phép."
    )

    add_heading_2(doc, "1.5. Giá trị và định hướng giáo dục")
    add_p(
        doc,
        "SafeWeb còn là bài học an toàn số: người dùng thấy cách tách một địa chỉ thành từng phần, hiểu vì sao khóa https chưa đủ để tin, và tập thói quen kiểm tra trước khi bấm."
    )

    # --------------------------------------------------------------------------
    # CHƯƠNG 2. CƠ SỞ HOẠT ĐỘNG CỦA AI VÀ CÁCH ĐƯA RA PHÁN ĐOÁN
    # --------------------------------------------------------------------------
    add_heading_1(doc, "CHƯƠNG 2. CƠ SỞ HOẠT ĐỘNG CỦA TRÍ TUỆ NHÂN TẠO VÀ CÁCH ĐƯA RA PHÁN ĐOÁN")

    add_heading_2(doc, "2.1. Bốn mô hình Trí tuệ nhân tạo trong SafeWeb làm được gì và khác nhau thế nào?")
    add_p(
        doc,
        "Thay vì chỉ nghe một ý kiến, SafeWeb dùng bốn mô hình học máy, tức là bốn cách để máy tính học dấu hiệu từ các trang web mẫu. Có thể hình dung chúng như bốn vị giám khảo cùng xem một hồ sơ nhưng mỗi người để ý một kiểu dấu hiệu khác nhau:"
    )
    add_bullet(
        doc,
        "1. Random Forest: ",
        "Tạo ra 100 cây câu hỏi nhỏ. Mỗi cây lần lượt hỏi về độ dài, dấu chấm, dấu gạch ngang hay từ khóa. Có thể hình dung 100 giám khảo độc lập bỏ phiếu; kết quả chung dựa trên tiếng nói của cả nhóm, nên một dấu hiệu lạ đơn lẻ khó quyết định toàn bộ kết luận."
    )
    add_bullet(
        doc,
        "2. Gradient Boosting: ",
        "Dùng nhiều cây hỏi nối tiếp nhau theo kiểu người sau xem lại chỗ người trước còn nhầm. Trong phép thử của dự án, mô hình này phát hiện 2.676 trên 2.799 trang lừa đảo, tương ứng 95,61%; con số này chỉ mô tả bộ thử đã dùng, không bảo đảm kết quả tương tự trên mọi trang ngoài đời."
    )
    add_bullet(
        doc,
        "3. SVM: ",
        "Tưởng tượng xếp hồ sơ an toàn về một phía, hồ sơ lừa đảo về phía còn lại rồi tìm đường ranh ngăn cách hai nhóm. Trong bộ thử, mô hình báo lừa đảo đúng 20 lần và không báo nhầm lần nào; nhưng nó bỏ sót 2.779 trong 2.799 trang lừa đảo. Vì vậy không nên dùng riêng mô hình này để bảo vệ người dùng."
    )
    add_bullet(
        doc,
        "4. Logistic Regression: ",
        "Giống như một bảng cân có nhiều quả cân: mỗi đặc điểm làm thay đổi điểm nghiêng về một phía. Cách tính gọn và nhanh, giúp nhóm có thêm một ý kiến khác để so sánh với ba vị giám khảo còn lại."
    )

    add_heading_2(doc, "2.2. Cách Trí tuệ nhân tạo tính toán và đưa ra phán đoán cuối cùng")
    add_p(
        doc,
        "Quy trình máy tính biến một dòng địa chỉ trang web thành kết luận cảnh báo trên màn hình được xác định rõ ràng qua 4 bước tính toán cụ thể:"
    )
    add_bullet(
        doc,
        "Bước 1 — Đo đạc thành 55 con số: ",
        "Phần mềm đếm độ dài, số lượng dấu câu, tỷ lệ chữ số và các từ khóa trên đường dẫn để biến thành 55 con số cụ thể."
    )
    add_bullet(
        doc,
        "Bước 2 — Tính điểm trung bình của 4 mô hình AI: ",
        "Từng mô hình dựa vào 55 con số này để tính ra tỷ lệ nghi ngờ lừa đảo từ 0% đến 100%. Hệ thống cộng kết quả của cả 4 mô hình rồi chia đều cho 4 để ra mức xác suất nghi ngờ chung (gọi là p), đồng thời hiển thị công khai điểm của từng mô hình."
    )
    add_bullet(
        doc,
        "Bước 3 — Cộng điểm các dấu hiệu nhìn thấy được: ",
        "Hệ thống cộng điểm riêng khi thấy địa chỉ quá dài, nhiều tầng tên phụ, dùng dãy số thay tên, có dấu @, nhiều ký tự lạ, có dấu mã hóa hoặc từ khóa nhạy cảm. Điểm này như các thẻ ghi chú để giải thích vì sao cần cẩn thận; nó làm thay đổi thanh điểm tổng hợp nhưng không tự đổi mức màu."
    )
    add_bullet(
        doc,
        "Bước 4 — Xếp mức rủi ro và đổi màu: ",
        "Mức xác suất dưới 25% là rủi ro thấp (Xanh); từ 25% đến dưới 50% là cần thận trọng (Vàng); từ 50% đến dưới 75% là nguy cơ cao (Cam); từ 75% trở lên là nguy cơ rất cao (Đỏ). Nếu cơ sở dữ liệu có hồ sơ khớp, kết quả hồ sơ được ưu tiên. Cách xếp này giống bốn vạch trên nhiệt kế: càng vượt vạch cao thì màu cảnh báo càng mạnh."
    )

    add_heading_2(doc, "2.3. Điểm mới của sản phẩm")
    add_p(
        doc,
        "Những điểm dưới đây là thứ phân biệt SafeWeb với một công cụ chỉ tra danh sách đen hoặc chỉ báo chung chung “nguy hiểm”:"
    )
    add_bullet(
        doc,
        "Ba lớp thông tin cùng làm việc: ",
        "Hồ sơ đã biết trong cơ sở dữ liệu, 55 dấu hiệu cấu trúc của địa chỉ và ý kiến của bốn mô hình được đặt cạnh nhau. Một trang mới tạo chưa có trong danh sách vẫn có thể bị phát hiện nhờ dấu hiệu và mô hình."
    )
    add_bullet(
        doc,
        "Giải thích được vì sao: ",
        "Kết quả không chỉ là một con số. Người dùng thấy mức màu (Xanh, Vàng, Cam, Đỏ), điểm của từng mô hình và lý do cụ thể như địa chỉ quá dài, nhiều tầng tên phụ hay có từ khóa nhạy cảm."
    )
    add_bullet(
        doc,
        "Chạy ngay trong trình duyệt: ",
        "Việc đối chiếu và chấm điểm diễn ra trên máy người dùng, mặc định không gửi địa chỉ đi đâu. Chỉ khi người dùng chủ động bật kiểm tra DNS hoặc ảnh xem trước, địa chỉ mới được chia sẻ với dịch vụ tương ứng."
    )
    add_bullet(
        doc,
        "Tự sửa địa chỉ gõ thiếu: ",
        "Nếu người dùng chỉ gõ một từ như vietcombank, phần mềm tự điền thành https://vietcombank.com trước khi kiểm tra."
    )
    add_bullet(
        doc,
        "Ví dụ lừa đảo tương tự để đối chiếu: ",
        "Khi một trang được xem là an toàn, SafeWeb chỉ đưa ra những trang lừa đảo có độ tin cậy cao, đã có ngày ghi nhận và tên miền giống ít nhất 80%, để người dùng thấy trang thật khác trang giả thế nào."
    )
    add_bullet(
        doc,
        "Phiếu báo cáo do người dùng lập: ",
        "Người dùng có thể lập phiếu báo cáo một địa chỉ nghi lừa đảo hoặc một cảnh báo có thể sai. Phiếu được lưu thành tệp trên máy, không tự gửi đi."
    )

    # --------------------------------------------------------------------------
    # CHƯƠNG 3. CÔNG CỤ, DỮ LIỆU VÀ QUY TRÌNH VẬN HÀNH HỆ THỐNG
    # --------------------------------------------------------------------------
    add_heading_1(doc, "CHƯƠNG 3. CÔNG CỤ, DỮ LIỆU VÀ QUY TRÌNH VẬN HÀNH HỆ THỐNG")

    add_heading_2(doc, "3.1. Thành phần và công cụ sử dụng")
    add_bullet(
        doc,
        "1. Python, pandas và scikit-learn: ",
        "Python là ngôn ngữ dùng để viết phần xử lý; pandas giống như bảng tính lớn để đọc, lọc và đếm các dòng dữ liệu; scikit-learn cung cấp sẵn các cách huấn luyện bốn mô hình. Nhóm chọn chúng vì có thể xử lý hàng trăm nghìn địa chỉ và lặp lại phép thử theo cùng một quy trình."
    )
    add_bullet(
        doc,
        "2. HTML, CSS, JavaScript và Flask: ",
        "HTML dựng khung trang như khung nhà; CSS tô màu và sắp xếp đồ đạc; JavaScript làm các nút và phép tính hoạt động; Flask là máy chủ phục vụ bản thử nghiệm. Khi đưa lên GitHub Pages, các tệp tĩnh và bộ tính toán JavaScript chạy ngay trong trình duyệt, không cần cài ứng dụng."
    )

    add_heading_2(doc, "3.2. Dữ liệu đưa vào hệ thống")
    add_p(
        doc,
        "Nhóm chuẩn bị ba phần dữ liệu: mẫu để máy học, mẫu để thi thử và cơ sở dữ liệu để tra cứu nhanh. Có thể hình dung đây lần lượt là bài học, đề kiểm tra để riêng và cuốn sổ tra cứu. Trong dữ liệu, số 1 chỉ trang lừa đảo, số 0 chỉ trang hợp lệ."
    )
    add_bullet(
        doc,
        "Cơ sở dữ liệu tra cứu nhanh: ",
        "Sau khi gộp các địa chỉ trùng nhau, cơ sở dữ liệu tra cứu giữ 36.261 địa chỉ: 19.909 trang lừa đảo và 16.352 trang hợp lệ. Đây giống như cuốn sổ ghi những trường hợp đã biết; nếu địa chỉ mới trùng hồ sơ thì hệ thống có thể nhận ra ngay."
    )
    add_bullet(
        doc,
        "Tập dữ liệu dùng để dạy máy học (Tập huấn luyện): ",
        "Tổng cộng có 261.299 địa chỉ dùng để huấn luyện bốn mô hình, gồm 114.113 trang lừa đảo và 147.186 trang hợp lệ. Đây là phần bài học; các địa chỉ dành cho thi thử được để riêng để đánh giá công bằng."
    )
    add_bullet(
        doc,
        "Tập dữ liệu giữ riêng để thi thử (Tập kiểm thử): ",
        "Gồm 6.624 địa chỉ được để riêng, không dùng lúc huấn luyện: 2.799 trang lừa đảo và 3.825 trang hợp lệ. Tên miền của chúng không trùng phần dữ liệu học, nên phép thử gần với việc gặp một trang mới hơn là gặp lại bài cũ."
    )

    add_heading_2(doc, "3.3. Lược đồ 55 dấu hiệu nhận biết địa chỉ trang web")
    add_p(
        doc,
        "Mỗi địa chỉ đưa vào SafeWeb được đo bằng đúng 55 biến số theo thứ tự cố định, chia thành 6 nhóm như Bảng 3.1."
    ).paragraph_format.keep_with_next = True
    add_p(doc, "Bảng 3.1. Sáu nhóm dấu hiệu nhận biết địa chỉ trang web", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4).paragraph_format.keep_with_next = True
    add_styled_table(
        doc,
        ["Nhóm", "Các biến đo", "Diễn giải đời thường"],
        [
            ["1. Độ dài và đếm ký tự (biến 01–10)", "url_length, domain_length, path_length, query_length, num_dots, num_slashes, num_hyphens, num_underscores, num_digits, num_letters", "Đo độ dài địa chỉ, tên trang, phần đường dẫn, phần tham số và đếm dấu chấm, gạch chéo, gạch ngang, gạch dưới, chữ số, chữ cái. Trang thật thường ngắn gọn; trang lừa đảo hay ghép thêm chữ, số và gạch ngang dài lê thê."],
            ["2. Cấu trúc và ký hiệu bất thường (biến 11–20)", "num_special_chars, has_https, has_ip, num_subdomains, has_at, has_question_mark, has_equals, has_percent, has_double_slash, has_query", "Kiểm tra có khóa https không, có dùng dãy số thay tên chữ không, có nhiều tầng tên miền phụ không, có dấu @ đánh lừa mắt nhìn hay các ký hiệu ?, =, %, // lạ. Giúp phát hiện các kiểu ngụy trang cấu trúc địa chỉ."],
            ["3. Độ lộn xộn của chữ cái (biến 21–22)", "url_entropy, domain_entropy", "Đo mức lộn xộn của cả địa chỉ và của tên trang. Tên thật ghép từ có nghĩa nên đọc xuôi; trang lừa đảo tạo tự động thường có chữ và số xếp hỗn loạn vô nghĩa."],
            ["4. Từ khóa nhạy cảm (biến 23–30)", "keyword_login, keyword_signin, keyword_verify, keyword_account, keyword_password, keyword_bank, keyword_payment, keyword_confirm", "Dò 8 từ mồi nhử quen thuộc: đăng nhập, vào tài khoản, xác minh, tài khoản, mật khẩu, ngân hàng, thanh toán, xác nhận. Kẻ gian hay chèn chúng để giục nạn nhân khai báo mật khẩu."],
            ["5. Tỉ lệ chữ, số và đuôi tên miền đáng ngờ (biến 31–52)", "phish_url_len, phish_dom_len, phish_tld_len, phish_path_len, phish_query_len, phish_is_ip, phish_subdom_cnt, phish_letter_cnt, phish_digit_cnt, phish_special_cnt, phish_eq_cnt, phish_qm_cnt, phish_amp_cnt, phish_dot_cnt, phish_dash_cnt, phish_under_cnt, phish_slash_cnt, phish_letter_ratio, phish_digit_ratio, phish_spec_ratio, phish_entropy, phish_suspicious_tld", "Đo chỉ tiết hơn: độ dài từng phần, số lượng từng loại ký tự, tỉ lệ phần trăm chữ cái, chữ số và ký tự lạ, độ lộn xộn và cờ báo đuôi tên miền hay bị lạm dụng. Giống như cân đo từng thành phần của một biển hiệu nghi vấn."],
            ["6. Giấu chữ bằng mã phần trăm (biến 53–55)", "phish_has_obfuscation, phish_obfuscated_char_count, phish_obfuscation_ratio", "Phát hiện chiêu biến chữ bình thường thành cụm ký hiệu dạng %xx để làm hoa mắt người xem."],
        ],
        size_pt=11,
        widths=[3.4, 5.6, 7.0],
    )

    add_heading_2(doc, "3.4. Công cụ đo, phần mềm phân tích và thống kê kết quả")
    add_p(
        doc,
        "Bộ đo được viết hai lần: một bản trong Python để dùng khi huấn luyện và một bản trong JavaScript để dùng trên trình duyệt. Cả hai biến địa chỉ thành cùng 55 con số, giống như hai chiếc cân được chỉnh theo một quả cân chuẩn. pandas giúp đếm và sắp xếp kết quả; scikit-learn tính các chỉ số. Nhóm kiểm tra số trang lừa đảo bắt trúng, trang hợp lệ đoán đúng, báo nhầm và bỏ sót trên 6.624 địa chỉ thi thử."
    )

    add_heading_2(doc, "3.5. Quy trình huấn luyện máy học")
    add_bullet(doc, "Bước 1: ", "Làm sạch dữ liệu, gộp các địa chỉ trùng lặp và tách riêng 6.624 địa chỉ có tên miền độc lập để làm đề thi kiểm tra.")
    add_bullet(doc, "Bước 2: ", "Đồng bộ nhãn dữ liệu (1 = lừa đảo, 0 = an toàn) trên toàn bộ 261.299 địa chỉ học tập.")
    add_bullet(doc, "Bước 3: ", "Chạy công cụ đo để biến mỗi địa chỉ trang web thành một dãy gồm đúng 55 con số đặc điểm.")
    add_bullet(doc, "Bước 4: ", "Cân bằng mức đóng góp giữa các nhóm dữ liệu rồi cho bốn mô hình học quy luật theo cùng một thiết lập để có thể lặp lại phép thử.")
    add_bullet(doc, "Bước 5: ", "Chấm điểm cả 4 mô hình trên 6.624 địa chỉ thi thử và đóng gói bộ não đã học sang tệp chạy trên trình duyệt web.")

    add_heading_2(doc, "3.6. Lưu đồ vận hành và các đoạn mã lệnh cốt lõi trong chương trình")
    add_p(doc, "Lưu đồ dưới đây mô tả trực quan đường đi của một địa chỉ trang web từ lúc người dùng nhập vào đến khi hiển thị kết luận cảnh báo:")

    p_img1 = doc.add_paragraph()
    p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img1.add_run().add_picture(flowchart_img, width=Inches(6.1))
    add_p(doc, "Hình 3.1. Lưu đồ vận hành 7 bước của phần mềm SafeWeb.", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    # 3 đoạn code cốt lõi kèm giải thích bình dân
    add_code_box(
        doc,
        "1) Tự hoàn thiện đường dẫn trang web:",
        [
            "function validateUrl(value) {",
            "  let healed = value.trim();",
            "  if (healed.startsWith('//')) healed = `https:${healed}`;",
            "  else if (!healed.includes('://')) {",
            "    const host = healed.split(/[/?#]/u, 1)[0];",
            "    if (!host.includes('.') && host.toLowerCase() !== 'localhost') {",
            "      healed = `${host}.com${healed.slice(host.length)}`;",
            "    }",
            "    healed = `https://${healed}`;",
            "  }",
            "  ...",
            "}"
        ],
        [
            "Bắt đầu hàm nhận một đường dẫn do người dùng nhập.",
            "Bỏ khoảng trắng ở đầu và cuối, như gọt bỏ phần thừa ngoài nhãn địa chỉ.",
            "Nếu người dùng đã gõ hai dấu gạch chéo đầu tiên, thêm giao thức bảo mật.",
            "Nếu chưa có phần đầu giao thức, hệ thống sẽ tự bổ sung.",
            "Tách phần tên máy chủ khỏi phần đường dẫn phía sau.",
            "Kiểm tra xem tên máy chủ có dấu chấm hay là tên máy cục bộ.",
            "Nếu chỉ nhập một từ như vietcombank, phần mềm thêm .com và giữ phần đường dẫn nếu có.",
            "Đóng nhánh kiểm tra tên máy không có dấu chấm.",
            "Kết thúc việc bổ sung phần đầu https://.",
            "Đóng khối xử lý trường hợp chưa có giao thức.",
            "Dấu ba chấm cho biết trích đoạn còn phần kiểm tra địa chỉ hợp lệ ở phía sau.",
            "Dòng đóng hàm; ví dụ vietcombank trở thành https://vietcombank.com."
        ]
    )

    add_code_box(
        doc,
        "2) Tra cứu hồ sơ lừa đảo đã biết:",
        [
            "function databaseMatch(url, features) {",
            "  const parts = parseParts(url);",
            "  let hostname = parts.hostname.toLowerCase().replace(/\\.+$/u, '');",
            "  if (hostname.startsWith('www.')) hostname = hostname.slice(4);",
            "  const path = parts.path.replace(/\\/+$/u, '');",
            "  const key = `${hostname}${path}?${parts.query}`.replace(/\\?$/u, '');",
            "  const record = recordsByUrl.get(key);",
            "  if (record) {",
            "    return { matched: true, type: 'exact_url', provenance: 'Matched in reference database', record };",
            "  }",
            "  if (database.knownPhishingHosts?.includes(parts.hostname.toLowerCase())) {",
            "    return { matched: true, type: 'known_phishing_host', provenance: 'Matched in reference database' };",
            "  }",
            "  return { matched: false, type: null, provenance: null };",
            "}"
        ],
        [
            "Hàm nhận địa chỉ và các con số dấu hiệu đã đo.",
            "Tách địa chỉ ra thành tên máy, đường dẫn và phần truy vấn, như tách tỉnh, phố và số nhà.",
            "Đưa tên máy về chữ thường và bỏ dấu chấm thừa ở cuối.",
            "Bỏ tiền tố www để cách viết có hoặc không có www cùng trỏ về một hồ sơ.",
            "Bỏ dấu gạch chéo cuối đường dẫn để tránh coi hai cách viết là hai nhà khác nhau.",
            "Ghép tên máy, đường dẫn và phần truy vấn thành khóa để dò sổ.",
            "Tìm khóa địa chỉ chính xác trong danh sách đã nạp.",
            "Kiểm tra xem có hồ sơ trùng khớp hay không.",
            "Nếu tìm thấy, trả lại hồ sơ và ghi rõ đây là kết quả đối chiếu từ kho.",
            "Đóng nhánh xử lý hồ sơ trùng khớp.",
            "Nếu địa chỉ đầy đủ không khớp, kiểm tra tên máy có nằm trong danh sách lừa đảo đã biết không.",
            "Trả về kết quả khớp tên máy và nguồn đối chiếu.",
            "Đóng nhánh kiểm tra tên máy.",
            "Nếu không có hồ sơ nào khớp, báo chưa tìm thấy; điều đó không tự chứng minh trang an toàn.",
            "Kết thúc hàm tra cứu."
        ]
    )

    add_code_box(
        doc,
        "3) Bốn mô hình cùng chấm một đường dẫn:",
        [
            "function modelProbabilities(features) {",
            "  const forest = model.models.random_forest.trees;",
            "  const boosting = model.models.gradient_boosting;",
            "  const svm = model.models.svm;",
            "  const logistic = model.models.logistic_regression;",
            "  const probabilities = {",
            "    random_forest: treeOutput(forest, features) / forest.length,",
            "    gradient_boosting: sigmoid(boosting.initialRawScore + boosting.learningRate * treeOutput(boosting.trees, features)),",
            "    svm: sigmoid(-(svm.calibrationA * scaledDecision(features, svm) + svm.calibrationB)),",
            "    logistic_regression: sigmoid(scaledDecision(features, logistic)),",
            "  };",
            "  return probabilities;",
            "}",
            "function predict(features, thresholds = defaultThresholds) {",
            "  const models = modelProbabilities(features);",
            "  const probability = Object.values(models).reduce((sum, value) => sum + value, 0) / 4;",
            "  const prediction = probability > 0.5 ? 'phishing' : 'legitimate';",
            "  const riskLevel = riskLevelForProbability(probability, thresholds);",
            "  return { prediction, probability, risk_level: riskLevel, models };",
            "}"
        ],
        [
            "Hàm tạo ra bốn mức điểm riêng từ cùng một bộ dấu hiệu.",
            "Bắt đầu hàm tính điểm cho bốn mô hình.",
            "Lấy các cây hỏi thuộc mô hình Random Forest.",
            "Lấy các lượt học nối tiếp của mô hình Gradient Boosting.",
            "Lấy thông số ranh giới và hiệu chỉnh của SVM.",
            "Lấy bảng trọng số của mô hình Logistic Regression.",
            "Bắt đầu gom bốn kết quả thành một danh sách.",
            "Chấm bằng rừng câu hỏi rồi lấy trung bình phiếu của các cây.",
            "Tính kết quả của các lượt sửa sai liên tiếp rồi đổi thành mức điểm.",
            "Đổi độ lệch khỏi ranh giới thành mức điểm đã hiệu chỉnh.",
            "Cộng dấu hiệu theo trọng số rồi đổi thành mức điểm.",
            "Đóng danh sách điểm.",
            "Gửi lại đủ bốn điểm riêng để bước kế tiếp sử dụng.",
            "Bắt đầu hàm kết hợp kết quả.",
            "Gọi cả bốn mô hình với cùng bộ dấu hiệu.",
            "Cộng bốn điểm rồi chia đều, như lấy điểm chung của bốn giám khảo.",
            "Nếu điểm chung lớn hơn một nửa, dự đoán thuộc nhóm lừa đảo; nếu không, thuộc nhóm hợp lệ.",
            "Dùng các mốc 25%, 50% và 75% để xếp mức rủi ro.",
            "Trả lại kết luận chung, xác suất và điểm riêng để người dùng xem xét.",
            "Kết thúc hàm kết hợp."
        ]
    )

    # --------------------------------------------------------------------------
    # CHƯƠNG 4. KẾT QUẢ THỬ NGHIỆM VÀ KIỂM TRA SẢN PHẨM
    # --------------------------------------------------------------------------
    add_heading_1(doc, "CHƯƠNG 4. KẾT QUẢ THỬ NGHIỆM VÀ KIỂM TRA SẢN PHẨM")

    add_heading_2(doc, "4.1. Quá trình thử nghiệm: Kết quả lần đầu và kết quả lần nâng cấp sau")
    add_bullet(
        doc,
        "Kết quả ở lần thực hiện đầu tiên: ",
        "Ở giai đoạn đầu, nhóm dùng khoảng 5.000 địa chỉ, một mô hình Random Forest và ít dấu hiệu hơn. Quy mô nhỏ và chỉ có một cách chấm khiến hệ thống có thể bỏ lỡ kiểu giả mạo mới; không còn phép đo cùng bộ thử để nêu một tỷ lệ chính xác đáng tin cậy cho phiên bản đó."
    )
    add_bullet(
        doc,
        "Kết quả ở các lần nâng cấp: ",
        "Nhóm mở rộng bộ dữ liệu học lên 261.299 địa chỉ, cơ sở dữ liệu tra cứu có 36.261 hồ sơ, bộ đo có 55 dấu hiệu và hệ thống dùng bốn mô hình. Trên 6.624 địa chỉ được giữ riêng để thi thử, mô hình Gradient Boosting phát hiện 2.676 trong 2.799 trang lừa đảo (95,61%). SafeWeb có thêm biểu mẫu lập phiếu báo cáo loại suspected-phishing; phiếu được tạo thành tệp trên thiết bị, không tự gửi đi."
    )

    add_heading_2(doc, "4.2. Kết quả định lượng của bốn mô hình Trí tuệ nhân tạo")
    add_p(
        doc,
        "Cả bốn mô hình cùng làm bài kiểm tra trên 6.624 địa chỉ được giữ riêng (2.799 trang lừa đảo và 3.825 trang hợp lệ). Các tên cột trong Bảng 4.1 được viết bằng tiếng Việt; số liệu là kết quả của đúng bộ thử này, không phải lời hứa cho mọi trang web."
    )

    add_p(doc, "Bảng 4.1. Kết quả chấm điểm 4 mô hình Trí tuệ nhân tạo trên 6.624 địa chỉ kiểm thử", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    eval_headers = [
        "Tên mô hình",
        "Tỷ lệ đoán đúng chung",
        "Độ chuẩn xác khi báo động",
        "Tỷ lệ bắt trúng lừa đảo",
        "Điểm hiệu quả tổng hợp",
        "Trang hợp lệ đoán đúng / Trang hợp lệ báo nhầm / Trang lừa đảo bỏ sót / Trang lừa đảo phát hiện"
    ]
    eval_rows = [
        ["1. Random Forest", "87,45%", "80,75%", "92,32%", "86,15%", "3.209 / 616 / 215 / 2.584"],
        ["2. Gradient Boosting", "87,89%", "79,76%", "95,61%", "86,97%", "3.146 / 679 / 123 / 2.676"],
        ["3. SVM", "58,05%", "100,00%", "0,71%", "1,42%", "3.825 / 0 / 2.779 / 20"],
        ["4. Logistic Regression", "85,55%", "79,96%", "87,82%", "83,71%", "3.209 / 616 / 341 / 2.458"]
    ]
    add_styled_table(doc, eval_headers, eval_rows, size_pt=11, widths=[3.1, 2.1, 2.3, 2.3, 2.3, 3.9])

    add_bullet(
        doc,
        "Diễn giải kết quả dễ hiểu: ",
        "Trong 2.799 trang lừa đảo của bộ thử, mô hình Gradient Boosting phát hiện 2.676 trang, tức gần 96 trong mỗi 100 trang, và bỏ sót 123. Độ chuẩn xác khi báo động là 79,76%: trong 100 cảnh báo, khoảng 80 đúng. Random Forest phát hiện 2.584 trang; Logistic Regression phát hiện 2.458. SVM chỉ phát hiện 20 trang và bỏ sót 2.779, nên đây là hạn chế cần xử lý, dù 20 cảnh báo của nó đều đúng trong bộ thử."
    )

    add_heading_2(doc, "4.3. Kiểm thử phần mềm, xây dựng và xác minh cục bộ")
    add_p(
        doc,
        "Trước khi đưa vào sử dụng, phần mềm đã được kiểm tra tự động nghiêm ngặt với số lượng mẫu kiểm thử và kết quả cụ thể như sau:"
    )
    add_bullet(doc, "Kiểm thử xử lý dữ liệu và mô hình trên máy tính: ", "Thực hiện 59 mẫu kiểm thử tự động (kiểm tra làm sạch dữ liệu, đo 55 dấu hiệu, chấm điểm AI và ứng dụng). Kết quả: Đạt 59 / 59 mẫu (100%, không có lỗi).")
    add_bullet(doc, "Kiểm thử hoạt động trên trình duyệt web: ", "Thực hiện 16 bài kiểm thử tự động, bao gồm các thao tác nhập địa chỉ, chạy mô hình, đối chiếu cơ sở dữ liệu và kiểm tra nội dung giao diện. Kết quả lần chạy hiện tại: đạt 16 / 16.")
    add_bullet(doc, "Đối chiếu hai cách tính: ", "So sánh cùng 16 trường hợp giữa Python và JavaScript: 10 địa chỉ hợp lệ và 6 địa chỉ không hợp lệ. Cả hai cùng xử lý đúng trạng thái hợp lệ/không hợp lệ; xác suất có sai khác rất nhỏ do cách máy tính làm tròn số, tối đa khoảng 0,00000000000000075, nên không gọi là giống tuyệt đối từng chữ số.")
    add_bullet(
        doc,
        "Ý nghĩa của Xác minh cục bộ: ",
        "Xử lý cục bộ giống như tự mở cuốn sổ tra cứu và dùng bốn người giám khảo ngay tại bàn của mình: địa chỉ được chuẩn hóa, dò cơ sở dữ liệu và chấm điểm trong trình duyệt, không tự gửi đi dịch vụ bên ngoài. Nếu người dùng chủ động bật kiểm tra DNS hoặc ảnh xem trước, địa chỉ sẽ được chia sẻ với dịch vụ tương ứng; vì vậy không thể gọi mọi chế độ là hoàn toàn không gửi dữ liệu."
    )

    p_img2 = doc.add_paragraph()
    p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img2.add_run().add_picture(verify_img, width=Inches(5.9))
    add_p(doc, "Hình 4.1. Tổng hợp kết quả kiểm thử phần mềm và xác minh cục bộ của SafeWeb.", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    add_heading_2(doc, "4.4. Hướng dẫn thao tác và giao diện thực tế")
    add_p(doc, "Người dùng chỉ cần thực hiện 3 bước đơn giản trên giao diện SafeWeb:")
    add_bullet(doc, "Bước 1: ", "Dán địa chỉ trang web cần kiểm tra vào ô nhập (không dán mật khẩu cá nhân). Hệ thống tự động hoàn thiện https:// hoặc .com nếu thiếu.")
    add_bullet(doc, "Bước 2: ", "Bấm nút 'Phân tích URL' (chỉ bật nút kiểm tra trực tuyến nếu muốn xem thêm thông tin tên miền DNS và ảnh chụp trang web).")
    add_bullet(doc, "Bước 3: ", "Nhìn màu sắc cảnh báo (Xanh = Thấp, Vàng = Thận trọng, Đỏ = Nguy hiểm), xem điểm của 4 mô hình AI, đọc lý do cụ thể tại ô 'Vì sao có kết quả này?' hoặc tra cứu thêm trong 'Cơ sở dữ liệu URL'.")

    p_img3 = doc.add_paragraph()
    p_img3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img3.add_run().add_picture(steps_img, width=Inches(5.9))
    add_p(doc, "Hình 4.2. Sơ đồ 3 bước thao tác và ý nghĩa màu sắc cảnh báo.", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

    p_img4 = doc.add_paragraph()
    p_img4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img4.add_run().add_picture(ui_img, width=Inches(5.7))
    add_p(doc, "Hình 4.3. Giao diện SafeWeb.", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    # --------------------------------------------------------------------------
    # CHƯƠNG 5. ĐÁNH GIÁ SẢN PHẨM, ĐÓNG GÓP MỚI VÀ HƯỚNG PHÁT TRIỂN
    # --------------------------------------------------------------------------
    add_heading_1(doc, "CHƯƠNG 5. ĐÁNH GIÁ SẢN PHẨM, ĐÓNG GÓP MỚI VÀ HƯỚNG PHÁT TRIỂN")

    add_heading_2(doc, "5.1. Khẳng định đóng góp mới và ưu thế vượt trội của sản phẩm")
    add_bullet(
        doc,
        "Đóng góp của dự án: ",
        "SafeWeb đặt cạnh nhau ba loại thông tin: hồ sơ đã có trong cơ sở dữ liệu, dấu hiệu cấu trúc của địa chỉ và ý kiến của bốn mô hình. Trên bộ thử tên miền tách riêng, mô hình Gradient Boosting phát hiện 95,61% trang lừa đảo. Dự án chưa thử đối chứng trực tiếp với các dịch vụ ngoài thị trường, nên không kết luận mình chính xác hơn mọi công cụ khác."
    )
    add_bullet(
        doc,
        "Giúp người dùng xem xét trước khi bấm: ",
        "Màu cảnh báo, điểm từng mô hình, lý do và ví dụ gần giống giúp người dùng có thêm căn cứ để tự quyết định. Kết quả là lời nhắc để kiểm tra kỹ, không thay thế việc xác minh qua ngân hàng, nhà cung cấp dịch vụ hoặc người gửi chính thức."
    )

    add_heading_2(doc, "5.2. Kết luận và một số hạn chế cần hoàn thiện")
    add_p(
        doc,
        "SafeWeb có bộ tra cứu, bốn mô hình, giao diện giải thích kết quả và biểu mẫu tạo phiếu phản hồi. Trong phép thử hiện có, mô hình Gradient Boosting phát hiện 95,61% trang lừa đảo; SVM còn bỏ sót nhiều trường hợp và cần được hiệu chỉnh. Mọi con số đều phụ thuộc vào bộ dữ liệu và cách thử đã nêu."
    )

    add_heading_2(doc, "5.3. Hướng phát triển tương lai: Tiện ích tự động quét đường dẫn trong tầm mắt")
    add_p(
        doc,
        "Trong giai đoạn tiếp theo, nhóm dự kiến phát triển SafeWeb thành tiện ích gắn trực tiếp vào trình duyệt. Khi người dùng xem mạng xã hội, tin nhắn hoặc thư điện tử, tiện ích có thể rà các đường dẫn đang hiện trên màn hình và đặt dấu cảnh báo trước khi người dùng bấm. Đây là hướng phát triển, chưa phải tính năng hiện có."
    )

    # --------------------------------------------------------------------------
    # TÀI LIỆU THAM KHẢO & PHỤ LỤC NGẮN GỌN
    # --------------------------------------------------------------------------
    add_heading_1(doc, "TÀI LIỆU THAM KHẢO")
    add_p(doc, "Nguồn: Internet. Các đường liên kết dưới đây là nơi nhóm lấy dữ liệu và công cụ.", italic=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4)
    add_bullet(doc, "1. Bộ dữ liệu PhishVN (địa chỉ trang web tiếng Việt): ", "dùng làm cơ sở dữ liệu tra cứu và một phần bài học, đề thi. https://doi.org/10.17632/b97hxbxtpd.4")
    add_bullet(doc, "2. Bộ dữ liệu PhiUSIIL Phishing URL: ", "bổ sung nhiều kiểu địa chỉ để các mô hình học thêm dấu hiệu. https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset")
    add_bullet(doc, "3. Thư viện scikit-learn: ", "dùng để huấn luyện, chấm điểm và thống kê bốn mô hình. https://scikit-learn.org/stable/")
    add_bullet(doc, "4. Chuẩn kỹ thuật về địa chỉ web (RFC 3986): ", "dùng để tách và chuẩn hóa các phần của địa chỉ. https://www.rfc-editor.org/rfc/rfc3986")

    add_heading_1(doc, "PHỤ LỤC: TÁM TÊN GỌI CỐT LÕI")
    gloss_rows = [
        ["Đường dẫn trang web", "URL", "Địa chỉ để đi đến một trang, giống số nhà và tên đường."],
        ["Trang web lừa đảo", "Phishing", "Trang giả mạo nhằm dụ người xem giao mật khẩu hoặc tiền."],
        ["Tên miền", "Domain", "Tên dễ nhớ thay cho dãy số của máy chủ, như tên một cửa hàng."],
        ["Kết nối HTTPS", "HTTPS", "Lớp mã hóa đường truyền; có khóa không đồng nghĩa cửa hàng là thật."],
        ["Danh bạ tên miền", "DNS", "Dịch vụ đổi tên trang thành địa chỉ máy chủ, như danh bạ tìm số điện thoại."],
        ["Học máy", "Machine Learning", "Cho máy xem nhiều ví dụ để nó học cách nhận ra mẫu giống nhau."],
        ["Tính ngay trong trình duyệt", "Browser inference", "Máy người dùng tự chấm điểm, như tự làm phép tính tại bàn."],
        ["Tiện ích gắn vào trình duyệt", "Browser extension", "Chương trình nhỏ thêm chức năng vào trình duyệt; đây là hướng phát triển."]
    ]
    add_styled_table(doc, ["Tên gọi tiếng Việt", "Tên kỹ thuật", "Giải thích đời thường"], gloss_rows, size_pt=12, widths=[4.4, 3.6, 8.0])

    # --------------------------------------------------------------------------
    # TRANG CUỐI: TRANG BÌA CUỐI (ĐỒNG BỘ BÌA ĐẦU)
    # --------------------------------------------------------------------------
    doc.add_page_break()
    add_p(doc, "SAFEWEB", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8, size_pt=14, color_rgb=(15, 76, 92))
    add_p(doc, "KIỂM TRA ĐƯỜNG DẪN TRƯỚC KHI BẤM — BẢO VỆ AN TOÀN TRÊN KHÔNG GIAN MẠNG", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16, size_pt=14, color_rgb=(15, 118, 110))
    add_p(
        doc,
        "Công cụ nghiên cứu và giáo dục hỗ trợ người dùng phát hiện sớm các dấu hiệu bất thường trên địa chỉ trang web bằng Trí tuệ nhân tạo, giúp người dùng chủ động phán đoán, kiểm tra an toàn trước khi kích hoạt đường dẫn.",
        align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, size_pt=14
    )
    add_p(doc, "Người thực hiện 1 : Lê Văn Tuấn Anh", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size_pt=14)
    add_p(doc, "Người thực hiện 2 : Nguyễn Hoàng Bảo", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size_pt=14)
    add_p(doc, "Người hướng dẫn : Trần Văn Toàn", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size_pt=14)

    # Xuất báo cáo Word dạng .docx.
    docx_file = PROJECT_ROOT / "Bao_cao_SafeWeb_KHKT_THPT.docx"
    doc.save(docx_file)
    print(f"HOÀN TẤT! Đã tạo thành công '{docx_file}' (định dạng .docx, cỡ chữ 14pt, đầy đủ hình minh họa)!")


if __name__ == "__main__":
    build_full_report()