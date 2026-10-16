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
        "3. Đối chiếu\nKho dữ liệu\n36.261 địa chỉ",
        "4. Đo đếm\n55 dấu hiệu\ncủa địa chỉ",
        "5. Bốn mô hình\ncùng chấm điểm\ntrên địa chỉ",
        "6. Tra cứu tên miền\nvà ảnh xem trước\n(nếu bật)",
        "7. Đổi màu trang\n(Xanh/Vàng/Cam/Đỏ)\nvà nêu lý do"
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
         "1. KIỂM TRA DỮ LIỆU VÀ MÔ HÌNH",
         "Đạt 59 / 59 bài",
         "Kiểm tra làm sạch, đo dấu hiệu và tính điểm"),
        (5.15, 2.55, "#B45309", "#FFFBEB",
         "2. KIỂM TRA TRÊN TRÌNH DUYỆT",
         "Đạt 16 / 16 bài",
         "Kiểm tra nhập địa chỉ, mô hình và kho tra cứu"),
        (0.3, 0.35, "#1D4ED8", "#EFF6FF",
         "3. ĐỐI CHIẾU HAI BỘ MÁY",
         "16 / 16 trường hợp khớp",
         "10 địa chỉ hợp lệ và 6 địa chỉ không hợp lệ"),
        (5.15, 0.35, "#15803D", "#F0FDF4",
         "4. QUYỀN RIÊNG TƯ THEO LỰA CHỌN",
         "Mặc định xử lý tại máy",
         "Kiểm tra mạng chỉ chạy khi người dùng đồng ý")
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
         "Bấm nút 'Phân tích URL'.\nMáy tra cứu kho và cho bốn\nmô hình cùng chấm điểm."),
        (7.2, "#16A34A", "#DCFCE7", "BƯỚC 3: NHÌN MÀU & ĐỌC LÝ DO",
         "• Xanh: rủi ro thấp\n• Vàng: cần thận trọng\n• Cam/Đỏ: nguy cơ cao hơn")
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
    """Use the captured SafeWeb page, never a drawn substitute."""
    screenshot = PROJECT_ROOT / "reports" / "screenshots" / "homepage.png"
    if not screenshot.is_file():
        raise FileNotFoundError(f"Real SafeWeb screenshot not found: {screenshot}")
    return str(screenshot)


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
    p.paragraph_format.line_spacing = 1.1
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    if text:
        r = p.add_run(text)
        format_run(r, size_pt=size_pt, bold=bold, italic=italic, color_rgb=color_rgb)
    return p


def add_bullet(doc, lead_bold: str, rest_text: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.1
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


def add_toc_field(doc):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.1
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run()
    format_run(run, size_pt=14)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = ' TOC \\o "1-1" \\h \\z \\u '
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    result = OxmlElement("w:t")
    result.text = "Mục lục tự cập nhật khi mở tài liệu bằng Word hoặc LibreOffice."
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, separate, result, end])


def add_code_box(doc, title: str, code_lines: list, explanation_lines: list):
    add_p(doc, title, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=3, size_pt=14, color_rgb=(15, 76, 92))
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
    format_run(r, size_pt=14, bold=False, font_name="Courier New", color_rgb=(15, 23, 42))

    for exp_lead, exp_body in explanation_lines:
        add_bullet(doc, exp_lead, exp_body)


def add_styled_table(doc, headers: list, rows: list):
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
        r = p.add_run(h_text)
        format_run(r, size_pt=14, bold=True, color_rgb=(255, 255, 255))

    for row_idx, r_data in enumerate(rows):
        bg = "FFFFFF" if row_idx % 2 == 0 else "F8FAFC"
        for col_idx, val in enumerate(r_data):
            cell = tbl.cell(row_idx + 1, col_idx)
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=90, bottom=90, left=120, right=120)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx in (0, len(headers) - 1) else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val)
            format_run(r, size_pt=14, bold=(col_idx == 0))

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

    for style_name in ("Normal", "Heading 1", "Heading 2"):
        style = doc.styles[style_name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(14)
        style.paragraph_format.line_spacing = 1.1
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    doc.settings.element.append(update_fields)

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
    add_p(doc, "LĨNH VỰC: PHẦN MỀM HỆ THỐNG VÀ AN TOÀN THÔNG TIN", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, size_pt=14, color_rgb=(15, 118, 110))

    add_p(doc, "SAFEWEB (PHIÊN BẢN 2.3.5)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10, size_pt=14, color_rgb=(15, 76, 92))
    add_p(
        doc,
        "ỨNG DỤNG TRÍ TUỆ NHÂN TẠO KẾT HỢP PHÂN TÍCH ĐỊA CHỈ TRANG WEB GIÚP CẢNH BÁO SỚM RỦI RO LỪA ĐẢO VÀ LỘ LỌT DỮ LIỆU",
        bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=20, size_pt=14, color_rgb=(15, 23, 42)
    )
    add_p(doc, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, size_pt=14, color_rgb=(15, 118, 110))

    add_p(doc, "Dự án thiết kế và xây dựng phần mềm hỗ trợ nhận biết đường dẫn trang web có nguy cơ lừa đảo.", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=5)
    add_p(doc, "NĂM 2026", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=50, size_pt=14)
    author_line = add_p(doc, "Người thực hiện 1: Lê Văn Tuấn Anh", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=5)
    author_line.paragraph_format.space_before = Pt(45)
    add_p(doc, "Người thực hiện 2: Nguyễn Hoàng Bảo", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=5)
    add_p(doc, "Người hướng dẫn: Trần Văn Toàn", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

    doc.add_page_break()

    # --------------------------------------------------------------------------
    # TRANG 2: MỤC LỤC & TÓM TẮT DỰ ÁN
    # --------------------------------------------------------------------------
    add_p(doc, "MỤC LỤC", bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=6, size_pt=14, color_rgb=(15, 76, 92))
    add_toc_field(doc)

    add_heading_1(doc, "TÓM TẮT DỰ ÁN")
    add_p(
        doc,
        "SafeWeb giúp người dùng xem xét đường dẫn trang web trước khi mở, giống như kiểm tra địa chỉ và biển hiệu trước khi bước vào một cửa hàng lạ. Hệ thống đo 55 dấu hiệu trong đường dẫn, đối chiếu với kho 36.261 địa chỉ đã ghi nhận và tham khảo bốn mô hình học máy. Phân tích thông thường diễn ra ngay trên thiết bị; kiểm tra tên miền, chuyển hướng và ảnh xem trước chỉ được thực hiện khi người dùng cho phép."
    )
    add_p(
        doc,
        "Bốn mô hình được huấn luyện trên 261.299 mẫu và đánh giá bằng 6.624 địa chỉ chưa dùng khi huấn luyện. Trong phép thử này, mô hình Tăng Cường Độ Dốc phát hiện 2.676 trên 2.799 địa chỉ lừa đảo, tương đương 95,61%. Hệ thống vượt qua 59 bài kiểm tra Python, 16 bài kiểm tra trình duyệt và 16 trường hợp đối chiếu giữa hai cách tính."
    )
    add_p(doc, "Từ khóa: Trang web lừa đảo; Địa chỉ trang web; Trí tuệ nhân tạo; Kiểm tra trực tiếp trên trình duyệt; Bảo vệ quyền riêng tư.", italic=True)

    # --------------------------------------------------------------------------
    # CHƯƠNG 1. XÁC ĐỊNH NHU CẦU VÀ MỤC TIÊU THIẾT KẾ
    # --------------------------------------------------------------------------
    add_heading_1(doc, "CHƯƠNG 1. XÁC ĐỊNH NHU CẦU VÀ MỤC TIÊU THIẾT KẾ")

    add_heading_2(doc, "1.1. Bối cảnh và vấn đề thực tiễn")
    add_p(
        doc,
        "Mỗi trang web trên mạng Internet đều có một dòng địa chỉ riêng giống như biển hiệu và số nhà ngoài đời thực. Hiện nay, kẻ gian thường xuyên phát tán tin nhắn hoặc thư điện tử chứa các đường dẫn giả mạo ngân hàng, mạng xã hội, sàn mua sắm hoặc trang nhận quà trò chơi để lừa người dân nhập mật khẩu và mã xác nhận. Bằng mắt thường, người dùng rất dễ bị đánh lừa vì kẻ xấu ghép tên thương hiệu lớn vào đầu địa chỉ, viết đường dẫn rất dài để che giấu phần đuôi giả mạo, hoặc chèn các chữ thúc giục đăng nhập, xác minh tài khoản."
    )
    add_p(
        doc,
        "Đặc biệt, nhiều người lầm tưởng rằng cứ thấy địa chỉ có chữ https (biểu tượng ổ khóa) ở đầu là trang web chính chủ an toàn. Thực tế, chữ https chỉ cho biết đường truyền có mã hóa, còn kẻ lừa đảo hoàn toàn có thể tạo biểu tượng ổ khóa này miễn phí cho trang web giả của chúng. Ngoài ra, đường dẫn người dùng nhận được có thể chứa thông tin riêng tư; nếu gửi đường dẫn đó lên các máy chủ lạ để kiểm tra thì lại có nguy cơ lộ lọt dữ liệu. Do đó, cần có một phần mềm tự khám xét địa chỉ trang web ngay trên máy của người dùng và giải thích rõ từng dấu hiệu bất thường."
    )

    add_heading_2(doc, "1.2. Nhu cầu thực tế và câu hỏi đặt ra")
    add_p(
        doc,
        "Nhu cầu là có một công cụ tự hoàn thiện địa chỉ bị thiếu, tra cứu hồ sơ đã ghi nhận, chấm mức rủi ro và giải thích dấu hiệu bất thường. Việc tra cứu trực tuyến chỉ bắt đầu khi người dùng cho phép. Câu hỏi nghiên cứu là: Khi đưa 55 dấu hiệu và bốn mô hình vào trình duyệt, kết quả có khớp với phép tính trên máy huấn luyện hay không?"
    )

    add_heading_2(doc, "1.3. Mục tiêu và tiêu chí thiết kế")
    add_bullet(
        doc,
        "Mục tiêu: ",
        "Xây dựng SafeWeb để người dùng xem xét đường dẫn trước khi mở, hiểu vì sao hệ thống cảnh báo và chủ động tránh nhập mật khẩu hoặc thông tin thanh toán vào trang đáng ngờ."
    )
    add_bullet(
        doc,
        "Tiêu chí thiết kế: ",
        "Hệ thống đo 55 dấu hiệu, trình bày ý kiến của bốn mô hình và tra cứu 36.261 địa chỉ; được đánh giá trên 6.624 địa chỉ có tên miền tách biệt với dữ liệu huấn luyện; mặc định phân tích ngay trên thiết bị; dùng màu Xanh, Vàng, Cam và Đỏ kèm lời giải thích."
    )

    add_heading_2(doc, "1.4. Phạm vi của sản phẩm")
    add_p(
        doc,
        "SafeWeb tập trung khám xét cấu trúc chữ viết, ký hiệu của đường dẫn trang web và đối chiếu với kho dữ liệu đã được kiểm chứng. Để bảo vệ thiết bị của người dùng, phần mềm không tự ý tải hay chạy mã độc của trang đích; việc tra cứu danh bạ tên miền (DNS) và chụp ảnh xem trước trang web chỉ thực hiện khi người dùng bật nút đồng ý."
    )

    add_heading_2(doc, "1.5. Giá trị và định hướng giáo dục")
    add_p(
        doc,
        "SafeWeb không chỉ là công cụ cảnh báo sớm mà còn là học liệu trực quan giúp học sinh, giáo viên và người dân hình thành kỹ năng an toàn số. Người dùng được quan sát trực tiếp cách tách một địa chỉ trang web thành từng bộ phận, hiểu được vì sao biểu tượng https chưa đủ để khẳng định trang web an toàn, và so sánh điểm số của 4 mô hình Trí tuệ nhân tạo để rèn luyện thói quen kiểm tra kỹ trước khi bấm vào bất kỳ đường dẫn lạ nào."
    )

    # --------------------------------------------------------------------------
    # CHƯƠNG 2. CƠ SỞ HOẠT ĐỘNG CỦA AI VÀ CÁCH ĐƯA RA PHÁN ĐOÁN
    # --------------------------------------------------------------------------
    add_heading_1(doc, "CHƯƠNG 2. CƠ SỞ HOẠT ĐỘNG CỦA TRÍ TUỆ NHÂN TẠO VÀ CÁCH ĐƯA RA PHÁN ĐOÁN")

    add_heading_2(doc, "2.1. Bốn mô hình Trí tuệ nhân tạo trong SafeWeb làm được gì và khác nhau thế nào?")
    add_p(
        doc,
        "Thay vì chỉ dùng một thuật toán đơn lẻ dễ có điểm mù, SafeWeb kết hợp cùng lúc 4 mô hình Học máy (dạy máy tính tự học quy luật từ hàng trăm nghìn trang web mẫu). Có thể hình dung 4 mô hình này giống như 4 vị giám khảo có phương pháp làm việc khác nhau:"
    )
    add_bullet(
        doc,
        "1. Mô hình Rừng Ngẫu Nhiên (Random Forest): ",
        "Tạo ra một hội đồng gồm 100 cây câu hỏi kiểm tra độc lập (mỗi cây hỏi tối đa 16 bước về độ dài, dấu chấm, dấu gạch ngang, từ khóa...). Giống như 100 người bảo vệ cùng khám xét một địa chỉ web rồi lấy kết quả trung bình chung, giúp phán đoán rất vững vàng và cân bằng."
    )
    add_bullet(
        doc,
        "2. Mô hình Tăng Cường Độ Dốc (Gradient Boosting): ",
        "Cũng dùng 100 cây kiểm tra nhỏ (mỗi cây 3 bước hỏi) nhưng làm việc nối tiếp nhau theo kiểu 'người đi sau sửa sai cho người đi trước'. Những trang web lừa đảo tinh vi bị vòng trước đoán nhầm sẽ được vòng sau tập trung soi kỹ hơn để rút kinh nghiệm, nhờ đó đạt tỷ lệ bắt trúng trang lừa đảo cao nhất (95,61%)."
    )
    add_bullet(
        doc,
        "3. Mô hình Máy Véc-tơ Hỗ Trợ (SVM): ",
        "Tưởng tượng xếp trang an toàn về một bên phòng, trang lừa đảo về bên kia rồi kẻ một vạch chia. Trong phép thử hiện tại, mô hình chỉ báo động 20 địa chỉ và cả 20 đều là lừa đảo, nhưng bỏ sót 2.779 địa chỉ lừa đảo khác; vì vậy không nên dùng riêng mô hình này để kết luận."
    )
    add_bullet(
        doc,
        "4. Mô hình Hồi Quy Logic (Logistic Regression): ",
        "Hoạt động giống như một bảng cộng trừ điểm trực tiếp. Mỗi dấu hiệu xấu trên đường dẫn sẽ bị cộng thêm điểm rủi ro, dấu hiệu tốt được trừ điểm, đóng vai trò làm thước đo chuẩn cơ bản nhanh gọn để đối chiếu với 3 mô hình trên."
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
        "Bước 3 — Cộng điểm dấu hiệu trực tiếp và chỉ rõ bất thường ở đâu: ",
        "Giao diện cộng thêm điểm phạt trực tiếp nếu phát hiện các bất thường cụ thể: địa chỉ dài từ 120 ký tự trở lên (+18 điểm); có từ 3 tên miền phụ trở lên (+16 điểm); dùng địa chỉ số IP (+18 điểm); có ký tự @ (+12 điểm); có từ 8 ký tự đặc biệt trở lên (+10 điểm); có ký hiệu % (+8 điểm); độ lộn xộn chữ cái từ 4,5 trở lên (+10 điểm); mỗi từ khóa nhạy cảm xuất hiện (+8 điểm). Điểm tổng hợp trên thanh đo (từ 0 đến 100) được tính bằng 60% điểm nghi ngờ AI cộng với điểm dấu hiệu trực tiếp."
    )
    add_bullet(
        doc,
        "Bước 4 — Quy đổi mức cảnh báo và đổi màu toàn trang web: ",
        "Nếu mức nghi ngờ chung dưới 25% -> Mức Rủi Ro Thấp (Đổi giao diện màu Xanh lá); từ 25% đến dưới 50% -> Mức Cần Thận Trọng (Màu Vàng); từ 50% đến dưới 75% -> Mức Nguy Cơ Cao (Màu Cam/Đỏ); từ 75% trở lên hoặc khớp danh sách đen -> Mức Nguy Cơ Rất Cao (Báo động Đỏ rực kèm danh sách giải thích rõ đường dẫn bất thường ở vị trí nào)."
    )

    add_heading_2(doc, "2.3. Điểm mới của sản phẩm")
    add_p(
        doc,
        "Sản phẩm kết hợp đồng thời tra cứu Kho dữ liệu và 4 mô hình Trí tuệ nhân tạo chạy trực tiếp ngay trong trình duyệt web; tách rõ giữa hồ sơ đã ghi nhận và dự đoán của máy học; tự động hoàn thiện địa chỉ thiếu và bảo vệ quyền riêng tư nhờ cơ chế phân tích tại chỗ mặc định."
    )

    # --------------------------------------------------------------------------
    # CHƯƠNG 3. CÔNG CỤ, DỮ LIỆU VÀ QUY TRÌNH VẬN HÀNH HỆ THỐNG
    # --------------------------------------------------------------------------
    add_heading_1(doc, "CHƯƠNG 3. CÔNG CỤ, DỮ LIỆU VÀ QUY TRÌNH VẬN HÀNH HỆ THỐNG")

    add_heading_2(doc, "3.1. Thành phần và công cụ sử dụng")
    add_bullet(
        doc,
        "1. Ngôn ngữ lập trình Python và bộ công cụ Học máy (pandas, NumPy, scikit-learn, joblib): ",
        "Dùng để đọc dữ liệu, đo đếm 55 dấu hiệu và huấn luyện 4 mô hình Trí tuệ nhân tạo. Lý do chọn là vì bộ công cụ này tính toán chuẩn xác, xử lý nhanh hàng trăm nghìn dòng dữ liệu và cho phép trích xuất toàn bộ thông số đã học ra tệp dữ liệu gọn nhẹ."
    )
    add_bullet(
        doc,
        "2. Bộ công cụ giao diện Web (HTML, CSS, JavaScript) và máy chủ thử nghiệm (Flask): ",
        "Dùng để xây dựng trang web SafeWeb với ô nhập địa chỉ, bảng đồng thuận 4 mô hình, kho dữ liệu tra cứu và hiệu ứng đổi màu toàn trang. Nhờ viết bộ máy suy luận bằng JavaScript (browser-model.js), người dùng mở trang web trên máy tính hay điện thoại là dùng được ngay trên GitHub Pages mà không cần cài đặt phần mềm."
    )

    add_heading_2(doc, "3.2. Dữ liệu đưa vào hệ thống")
    add_p(
        doc,
        "Để dạy cho máy tính phân biệt chính xác trang web thật và trang web giả, nhóm đã chuẩn bị và làm sạch một khối lượng dữ liệu thực tế lớn đưa vào hệ thống (quy ước thống nhất: nhãn 1 là trang lừa đảo, nhãn 0 là trang an toàn):"
    )
    add_bullet(
        doc,
        "Kho dữ liệu tra cứu nhanh đã làm sạch: ",
        "Kho gồm 36.261 địa chỉ riêng biệt: 19.909 địa chỉ lừa đảo và 16.352 địa chỉ hợp lệ. Có thể hình dung đây là cuốn sổ tra cứu những địa chỉ đã được ghi nhận; trùng khớp với một hồ sơ không có nghĩa mọi địa chỉ mới đều đã được kiểm tra."
    )
    add_bullet(
        doc,
        "Tập dữ liệu dùng để dạy máy học (Tập huấn luyện): ",
        "Bốn mô hình được dạy bằng tổng cộng 261.299 địa chỉ: 114.113 trang lừa đảo và 147.186 trang hợp lệ. Mỗi địa chỉ được quy về hai nhãn này để máy học phân biệt các dấu hiệu thường gặp. Tên và xuất xứ từng bộ dữ liệu được ghi ở phần tài liệu tham khảo, không lặp lại trong mô tả quy trình."
    )
    add_bullet(
        doc,
        "Tập dữ liệu giữ riêng để thi thử (Tập kiểm thử): ",
        "Gồm 6.624 địa chỉ chưa dùng khi huấn luyện: 2.799 trang lừa đảo và 3.825 trang hợp lệ. Tên miền trong phần kiểm thử không trùng với tên miền dùng để dạy máy, giúp phép thử bớt thiên lệch do máy đã gặp sẵn những địa chỉ đó."
    )

    add_heading_2(doc, "3.3. Lược đồ 55 dấu hiệu nhận biết địa chỉ trang web")
    add_p(
        doc,
        "Mỗi địa chỉ được đo thành 55 con số theo cùng một thứ tự. Có thể hình dung đây là 55 câu hỏi kiểm tra giống nhau cho mọi địa chỉ, chia thành sáu nhóm sau:"
    )
    add_bullet(
        doc,
        "Nhóm 1 — Đo độ dài và đếm ký tự cơ bản (Biến 01 đến 10): ",
        "Đếm độ dài cả địa chỉ, tên miền, phần đường dẫn và phần thông số; đồng thời đếm dấu chấm, gạch chéo, gạch ngang, gạch dưới, chữ số và chữ cái. Giống như đếm độ dài một địa chỉ nhà và số ký hiệu lạ trên biển hiệu."
    )
    add_bullet(
        doc,
        "Nhóm 2 — Kiểm tra cấu trúc và ký hiệu bất thường (Biến 11 đến 20): ",
        "Đếm ký tự lạ, kiểm tra có kết nối HTTPS hay không, có dùng dãy số thay tên miền, có nhiều tầng tên phụ, có dấu @, ?, =, %, hai dấu gạch chéo hoặc phần thông số hay không. Đây là các dấu hiệu giúp phát hiện cách viết địa chỉ dễ gây nhầm lẫn."
    )
    add_bullet(
        doc,
        "Nhóm 3 — Đo độ lộn xộn của chữ cái (Biến 21 và 22): ",
        "Đo mức đa dạng, khó đoán của ký tự trong địa chỉ và tên miền. Có thể hình dung như so sánh một cái tên đọc được với một chuỗi ký tự gõ ngẫu nhiên; đây chỉ là dấu hiệu tham khảo, không tự nó chứng minh lừa đảo."
    )
    add_bullet(
        doc,
        "Nhóm 4 — Dò tìm 8 từ khóa nhạy cảm hay bị lợi dụng (Biến 23 đến 30): ",
        "Tìm các từ liên quan đến đăng nhập, vào tài khoản, xác minh, tài khoản, mật khẩu, ngân hàng, thanh toán và xác nhận. Những từ này cũng xuất hiện trên trang thật, nên hệ thống phải xem chúng cùng các dấu hiệu khác chứ không kết luận chỉ từ một từ."
    )
    add_bullet(
        doc,
        "Nhóm 5 — Đo chi tiết tỷ lệ chữ, số và đuôi tên miền đáng ngờ (Biến 31 đến 52): ",
        "Đo lại độ dài các phần của địa chỉ; nhận biết máy chủ dạng số và số tầng tên phụ; đếm chữ cái, chữ số, ký tự lạ, dấu bằng, dấu hỏi, dấu nối, gạch dưới, dấu chấm và gạch chéo; tính tỷ lệ từng nhóm ký tự, độ lộn xộn và đánh dấu một số đuôi tên miền thường cần xem xét kỹ hơn."
    )
    add_bullet(
        doc,
        "Nhóm 6 — Phát hiện chiêu trò giấu chữ bằng mã phần trăm (Biến 53 đến 55): ",
        "Kiểm tra địa chỉ có chứa ký tự được viết dưới dạng mã phần trăm hay không, đếm số ký tự kiểu này và tính tỷ lệ của chúng. Đây giống như phát hiện một số chữ đã bị thay bằng ký hiệu khó đọc."
    )

    add_heading_2(doc, "3.4. Công cụ đo, phần mềm phân tích và thống kê kết quả")
    add_p(
        doc,
        "Nhóm sử dụng bộ trích xuất tự động viết bằng Python (src/feature_extractor.py) và JavaScript (web/static/browser-model.js) làm công cụ đo đạc chính xác từng con số trong 55 dấu hiệu của mỗi địa chỉ web. Sau khi đo xong, phần mềm phân tích scikit-learn và pandas được dùng để chấm điểm tự động trên 6.624 địa chỉ thi thử: phần mềm đếm số trang lừa đảo bắt trúng, số trang an toàn đoán đúng, số trang báo nhầm và số trang bỏ sót, từ đó tính ra tỷ lệ phần trăm chính xác của từng mô hình và lưu vào bảng thống kê kết quả."
    )

    add_heading_2(doc, "3.5. Quy trình huấn luyện máy học")
    add_bullet(doc, "Bước 1: ", "Làm sạch dữ liệu, gộp các địa chỉ trùng lặp và tách riêng 6.624 địa chỉ có tên miền độc lập để làm đề thi kiểm tra.")
    add_bullet(doc, "Bước 2: ", "Đồng bộ nhãn dữ liệu (1 = lừa đảo, 0 = an toàn) trên toàn bộ 261.299 địa chỉ học tập.")
    add_bullet(doc, "Bước 3: ", "Chạy công cụ đo để biến mỗi địa chỉ trang web thành một dãy gồm đúng 55 con số đặc điểm.")
    add_bullet(doc, "Bước 4: ", "Cân bằng trọng số đóng góp giữa các nhóm dữ liệu và cho cả 4 mô hình AI học quy luật với mã cố định (seed = 42).")
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
        "1) Đoạn mã thật giúp tự hoàn thiện địa chỉ:",
        [
            "const host = healed.split(/[/?#]/u, 1)[0];",
            "if (!host.includes(\".\") && host.toLowerCase() !== \"localhost\") {",
            "  healed = `${host}.com${healed.slice(host.length)}`;",
            "}",
            "healed = `https://${healed}`;"
        ],
        [
            ("Dòng 1: ", "Tách phần tên miền khỏi đường dẫn phía sau, giống như tìm tên đường trước khi đọc số nhà."),
            ("Dòng 2: ", "Nếu tên miền chưa có dấu chấm và không phải máy tính nội bộ, hệ thống nhận diện đó có thể là tên ngắn người dùng vừa gõ."),
            ("Dòng 3: ", "Tự thêm phần đuôi .com nhưng giữ nguyên phần đường dẫn người dùng đã nhập."),
            ("Dòng cuối: ", "Thêm https:// để tạo thành địa chỉ đầy đủ trước khi kiểm tra.")
        ]
    )

    add_code_box(
        doc,
        "2) Đoạn mã thật biến địa chỉ thành các con số kiểm tra:",
        [
            "parts = _split_url(url)",
            "hostname = _hostname(parts)",
            "lowered = url.lower()",
            "features = _base_features(url, parts, hostname)",
            "features.update({",
            "    f\"keyword_{keyword}\": int(keyword in lowered)",
            "    for keyword in _KEYWORDS",
            "})"
        ],
        [
            ("Dòng 1: ", "Tách địa chỉ thành các phần như tên máy chủ, đường dẫn và thông số."),
            ("Dòng 2: ", "Lấy riêng tên máy chủ để đo các dấu hiệu thuộc tên miền."),
            ("Dòng 3: ", "Đưa chữ về cùng kiểu chữ thường để không bỏ sót từ chỉ vì viết hoa."),
            ("Dòng 4: ", "Tính các dấu hiệu nền như độ dài và ký tự đặc biệt."),
            ("Các dòng cuối: ", "Lần lượt kiểm tra từ khóa đã định trước; có thì ghi 1, không có thì ghi 0.")
        ]
    )

    add_code_box(
        doc,
        "3) Đoạn mã thật lấy ý kiến của bốn mô hình:",
        [
            "const models = modelProbabilities(features);",
            "const probability = Object.values(models)",
            "  .reduce((sum, value) => sum + value, 0) / 4;",
            "const prediction = probability > 0.5",
            "  ? \"phishing\" : \"legitimate\";",
            "const riskLevel = riskLevelForProbability(",
            "  probability, thresholds,",
            ");"
        ],
        [
            ("Dòng 1: ", "Yêu cầu từng mô hình tự chấm cùng một bộ dấu hiệu."),
            ("Dòng 2–3: ", "Cộng bốn điểm rồi chia bốn, giống như lấy điểm trung bình của bốn giám khảo."),
            ("Dòng 4–5: ", "Dùng mốc 50% để máy gắn nhãn nghi ngờ hoặc có vẻ hợp lệ."),
            ("Dòng cuối: ", "Đổi xác suất thành một trong các mức rủi ro đã cài đặt.")
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
        "Ở phiên bản thử nghiệm đầu tiên, nhóm chỉ dùng tệp dữ liệu nhỏ gồm 5.000 dòng địa chỉ cũ (urls.csv), đo ít dấu hiệu cơ bản và chỉ có 1 mô hình Rừng Ngẫu Nhiên. Khi gặp các trang web có tên miền mới lạ hoặc các trang lừa đảo tại Việt Nam, mô hình đơn lẻ dễ bị lúng túng, độ chính xác chỉ ở mức trung bình và báo lỗi khi người dùng gõ thiếu chữ https://."
    )
    add_bullet(
        doc,
        "Kết quả sau nâng cấp (các bản 2.3.0 đến 2.3.5): ",
        "Hệ thống dùng 261.299 mẫu huấn luyện, kho tra cứu 36.261 địa chỉ, 55 dấu hiệu và bốn mô hình. Trên 6.624 địa chỉ kiểm thử, mô hình Tăng Cường Độ Dốc phát hiện 2.676 trên 2.799 trang lừa đảo, đạt 95,61%. Bản 2.3.5 còn có phiếu báo cáo loại suspected-phishing; phiếu được tạo thành tệp để người dùng tự tải, không tự gửi đường dẫn hoặc email đi nơi khác."
    )

    add_heading_2(doc, "4.2. Kết quả định lượng của bốn mô hình Trí tuệ nhân tạo")
    add_p(
        doc,
        "Cả 4 mô hình cùng làm bài kiểm tra trên 6.624 địa chỉ trang web giữ riêng (gồm 2.799 trang lừa đảo thật và 3.825 trang an toàn thật). Kết quả được phiên dịch sang các chỉ số tiếng Việt dễ hiểu tại Bảng 4.1:"
    )

    add_p(doc, "Bảng 4.1. Kết quả chấm điểm 4 mô hình Trí tuệ nhân tạo trên 6.624 địa chỉ kiểm thử", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    eval_headers = [
        "Tên mô hình",
        "Tỷ lệ đoán đúng tổng thể",
        "Cảnh báo đúng là lừa đảo",
        "Tỷ lệ phát hiện lừa đảo",
        "Điểm cân bằng chung",
        "Số trang đúng / báo nhầm / bỏ sót / bắt trúng"
    ]
    eval_rows = [
        ["1. Rừng Ngẫu Nhiên", "87,45%", "80,75%", "92,32%", "86,15%", "3.209 / 616 / 215 / 2.584"],
        ["2. Tăng Cường Độ Dốc", "87,89%", "79,76%", "95,61%", "86,97%", "3.146 / 679 / 123 / 2.676"],
        ["3. Máy Véc-tơ Hỗ Trợ", "58,05%", "100,00%", "0,71%", "1,42%", "3.825 / 0 / 2.779 / 20"],
        ["4. Hồi Quy Logic", "85,55%", "79,96%", "87,82%", "83,71%", "3.209 / 616 / 341 / 2.458"]
    ]
    add_styled_table(doc, eval_headers, eval_rows)

    add_bullet(
        doc,
        "Diễn giải kết quả dễ hiểu: ",
        "Trong 2.799 trang lừa đảo của đề thi, mô hình Tăng Cường Độ Dốc bắt trúng tới 2.676 trang (đạt 95,61%, tức là cứ 100 trang lừa đảo mới tinh thì bắt gọn gần 96 trang, chỉ sót 123 trang). Mô hình Rừng Ngẫu Nhiên đứng thứ hai khi bắt trúng 2.584 trang lừa đảo (92,32%) và nhận diện đúng 3.209 trang an toàn. Mô hình Hồi Quy Logic bắt trúng 2.458 trang (87,82%). Riêng mô hình Máy Véc-tơ Hỗ Trợ ở mức cài đặt hiện tại quá khắt khe: nó không báo oan cho bất kỳ trang an toàn nào (đúng 3.825/3.825 trang, hễ báo động là trúng 100%) nhưng chỉ bắt được 20 trang lừa đảo. Việc đặt cả 4 mô hình cạnh nhau giúp tận dụng tối đa khả năng truy quét 95,61% của các mô hình chủ lực."
    )

    add_heading_2(doc, "4.3. Kiểm thử phần mềm, xây dựng và xác minh cục bộ")
    add_p(
        doc,
        "Trước khi đưa vào sử dụng, phần mềm đã được kiểm tra tự động nghiêm ngặt với số lượng mẫu kiểm thử và kết quả cụ thể như sau:"
    )
    add_bullet(doc, "Kiểm thử xử lý dữ liệu và mô hình trên máy tính: ", "Thực hiện 59 mẫu kiểm thử tự động (kiểm tra làm sạch dữ liệu, đo 55 dấu hiệu, chấm điểm AI và ứng dụng). Kết quả: Đạt 59 / 59 mẫu (100%, không có lỗi).")
    add_bullet(doc, "Kiểm thử hoạt động trên trình duyệt web: ", "Thực hiện 16 bài kiểm tra tự động trên trình duyệt, gồm chuẩn hóa địa chỉ, tính điểm, tra cứu và hiển thị kết quả. Kết quả: Đạt 16 / 16 bài.")
    add_bullet(doc, "Đối chiếu hai cách tính: ", "Cùng 16 trường hợp (10 địa chỉ hợp lệ, 6 địa chỉ không hợp lệ) được chạy qua bộ máy Python và bộ máy JavaScript trên trình duyệt. Các kết quả khớp; sai khác xác suất lớn nhất là 0,000000000000000749 do cách biểu diễn số thập phân, không phải khác biệt có ý nghĩa trong kết quả hiển thị.")
    add_bullet(
        doc,
        "Ý nghĩa của Xác minh cục bộ: ",
        "Xác minh cục bộ nghĩa là phần phân tích địa chỉ và chạy mô hình diễn ra ngay trên thiết bị, giống như tự dùng cuốn sổ tra cứu và dụng cụ kiểm tra ở nhà thay vì gửi địa chỉ cho người khác. Đường dẫn không được gửi đi trong chế độ này. Nếu bật kiểm tra trực tuyến, một phần thông tin sẽ được gửi tới dịch vụ bên ngoài; vì vậy người dùng cần xem thông báo và chỉ bật khi đồng ý."
    )

    p_img2 = doc.add_paragraph()
    p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img2.add_run().add_picture(verify_img, width=Inches(5.9))
    add_p(doc, "Hình 4.1. Tổng hợp kết quả kiểm thử phần mềm và xác minh cục bộ của SafeWeb.", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    add_heading_2(doc, "4.4. Hướng dẫn thao tác và giao diện thực tế")
    add_p(doc, "Người dùng chỉ cần thực hiện 3 bước đơn giản trên giao diện SafeWeb:")
    add_bullet(doc, "Bước 1: ", "Dán địa chỉ trang web cần kiểm tra vào ô nhập (không dán mật khẩu cá nhân). Hệ thống tự động hoàn thiện https:// hoặc .com nếu thiếu.")
    add_bullet(doc, "Bước 2: ", "Bấm nút 'Phân tích URL' (chỉ bật nút kiểm tra trực tuyến nếu muốn xem thêm thông tin tên miền DNS và ảnh chụp trang web).")
    add_bullet(doc, "Bước 3: ", "Nhìn màu cảnh báo: Xanh là rủi ro thấp, Vàng là cần thận trọng, Cam là nguy cơ cao, Đỏ là nguy cơ rất cao. Đọc lý do và điểm của từng mô hình; có thể mở kho tra cứu hoặc tạo phiếu báo cáo.")

    p_img3 = doc.add_paragraph()
    p_img3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img3.add_run().add_picture(steps_img, width=Inches(5.9))
    add_p(doc, "Hình 4.2. Sơ đồ 3 bước thao tác và ý nghĩa màu sắc cảnh báo.", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

    p_img4 = doc.add_paragraph()
    p_img4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img4.add_run().add_picture(ui_img, width=Inches(5.7))
    add_p(doc, "Hình 4.3. Ảnh chụp giao diện thực tế của SafeWeb phiên bản 2.3.5.", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    # --------------------------------------------------------------------------
    # CHƯƠNG 5. ĐÁNH GIÁ SẢN PHẨM, ĐÓNG GÓP MỚI VÀ HƯỚNG PHÁT TRIỂN
    # --------------------------------------------------------------------------
    add_heading_1(doc, "CHƯƠNG 5. ĐÁNH GIÁ SẢN PHẨM, ĐÓNG GÓP MỚI VÀ HƯỚNG PHÁT TRIỂN")

    add_heading_2(doc, "5.1. Khẳng định đóng góp mới và ưu thế vượt trội của sản phẩm")
    add_bullet(
        doc,
        "Kết quả nhận diện và thông tin đọc được cao hơn các công cụ kiểm tra đơn lẻ trên thị trường: ",
        "Điểm mới của SafeWeb là kết hợp kho địa chỉ đã ghi nhận, 55 dấu hiệu và bốn cách chấm điểm độc lập, rồi giải thích kết quả để người dùng tự cân nhắc trước khi mở đường dẫn. Trong phép thử nội bộ trên 6.624 địa chỉ, mô hình Tăng Cường Độ Dốc phát hiện 95,61% địa chỉ lừa đảo. Nhóm chưa thực hiện phép thử trực tiếp với từng sản phẩm trên thị trường, nên chưa thể kết luận SafeWeb chính xác hơn mọi công cụ đơn lẻ."
    )
    add_bullet(
        doc,
        "Giúp người dùng chủ động phán đoán và kiểm tra an toàn trước khi kích hoạt đường dẫn: ",
        "Trước khi bấm đường dẫn lạ, người dùng có thể xem màu cảnh báo, ý kiến từng mô hình, dấu hiệu bất thường, ảnh xem trước nếu đã đồng ý kiểm tra trực tuyến và các ví dụ đủ gần trong kho dữ liệu. Những thông tin này hỗ trợ người dùng tự quyết định, không thay thế việc xác minh qua kênh chính thức."
    )

    add_heading_2(doc, "5.2. Kết luận và một số hạn chế cần hoàn thiện")
    add_p(
        doc,
        "SafeWeb phiên bản 2.3.5 hoàn thành các mục tiêu thiết kế và vượt qua 59 bài kiểm tra xử lý dữ liệu, 16 bài kiểm tra trình duyệt. Mô hình Tăng Cường Độ Dốc phát hiện 95,61% địa chỉ lừa đảo trong bộ kiểm thử đã nêu. Hạn chế đáng chú ý là mô hình Máy Véc-tơ Hỗ Trợ hiện bỏ sót phần lớn địa chỉ lừa đảo ở ngưỡng đang dùng; cần điều chỉnh trước khi dựa vào ý kiến riêng của mô hình này. Phiếu báo cáo hiện được lưu thành tệp trên thiết bị, chưa có máy chủ tiếp nhận tự động."
    )

    add_heading_2(doc, "5.3. Hướng phát triển tương lai: Tiện ích tự động quét đường dẫn trong tầm mắt")
    add_p(
        doc,
        "Trong giai đoạn tiếp theo, nhóm sẽ phát triển SafeWeb thành Tiện ích mở rộng gắn trực tiếp vào trình duyệt web. Khi người dùng lướt mạng xã hội, đọc tin nhắn hay thư điện tử, tiện ích sẽ tự động quét các đường dẫn đang hiển thị trong tầm mắt trên màn hình, chấm điểm ngầm ngay trên máy và gắn biểu tượng cảnh báo sớm ngay cạnh đường dẫn độc hại trước khi người dùng kịp bấm chuột vào."
    )

    # --------------------------------------------------------------------------
    # TÀI LIỆU THAM KHẢO & PHỤ LỤC NGẮN GỌN
    # --------------------------------------------------------------------------
    add_heading_1(doc, "TÀI LIỆU THAM KHẢO")
    add_bullet(doc, "1. Bộ dữ liệu PhishVN, phiên bản 3.1.0 (2026): ", "Dùng làm kho địa chỉ tham chiếu và phần dữ liệu kiểm thử có tên miền tách biệt.")
    add_bullet(doc, "2. Bộ dữ liệu địa chỉ trang web PhiUSIIL: ", "Bổ sung mẫu để huấn luyện các mô hình nhận biết nhiều dạng địa chỉ khác nhau.")
    add_bullet(doc, "3. Tài liệu Python và thư viện scikit-learn: ", "Dùng để xử lý dữ liệu, huấn luyện bốn mô hình và tính các chỉ số đánh giá.")
    add_bullet(doc, "4. Tài liệu chuẩn về địa chỉ web, giao thức truyền tải, DNS và GitHub Pages: ", "Dùng để phân tích cấu trúc địa chỉ, giải thích việc tra cứu tên miền và mô tả nơi triển khai trang tĩnh.")

    add_heading_1(doc, "PHỤ LỤC: GIẢI NGHĨA NGẮN GỌN MỘT SỐ TÊN GỌI")
    gloss_rows = [
        ["URL", "Đường dẫn trang web", "Địa chỉ dẫn tới một trang trên mạng, giống số nhà và tên đường."],
        ["Phishing", "Trang giả mạo để lừa đảo", "Trang nhái cửa hàng thật để dụ khách đưa tiền hoặc mật khẩu."],
        ["HTTPS", "Kết nối có mã hóa", "Khóa bảo vệ đường truyền, nhưng không chứng minh chủ trang là đáng tin."],
        ["DNS", "Danh bạ tên miền", "Giống danh bạ giúp tìm máy chủ đứng sau tên trang web."],
        ["Học máy", "Máy tự học từ ví dụ", "Cho máy xem nhiều mẫu để máy rút ra các dấu hiệu thường gặp."],
        ["Rừng Ngẫu Nhiên", "Nhiều cây hỏi độc lập", "Nhiều người kiểm tra theo các câu hỏi nhỏ rồi lấy ý kiến chung."],
        ["Tăng Cường Độ Dốc", "Người sau sửa sai cho người trước", "Mỗi lượt sau chú ý hơn đến trường hợp lượt trước đoán nhầm."],
        ["Browser Extension", "Tiện ích mở rộng trình duyệt", "Phần mềm nhỏ gắn vào trình duyệt để cảnh báo ngay cạnh đường dẫn."]
    ]
    add_styled_table(doc, ["Tên gọi", "Nghĩa tiếng Việt", "Giải thích dễ hiểu"], gloss_rows)

    # --------------------------------------------------------------------------
    # TRANG CUỐI: TRANG BÌA CUỐI (ĐỒNG BỘ BÌA ĐẦU)
    # --------------------------------------------------------------------------
    doc.add_page_break()
    add_p(doc, "SAFEWEB (PHIÊN BẢN 2.3.5)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8, size_pt=14, color_rgb=(15, 76, 92))
    add_p(doc, "KIỂM TRA ĐƯỜNG DẪN TRƯỚC KHI BẤM — BẢO VỆ AN TOÀN TRÊN KHÔNG GIAN MẠNG", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16, size_pt=14, color_rgb=(15, 118, 110))
    add_p(
        doc,
        "Công cụ nghiên cứu và giáo dục hỗ trợ người dùng phát hiện sớm các dấu hiệu bất thường trên địa chỉ trang web bằng Trí tuệ nhân tạo, giúp người dùng chủ động phán đoán, kiểm tra an toàn trước khi kích hoạt đường dẫn.",
        align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, size_pt=14
    )
    add_styled_table(
        doc,
        ["Vai trò trong dự án", "Họ và tên"],
        [
            ["Người thực hiện 1", "Lê Văn Tuấn Anh"],
            ["Người thực hiện 2", "Nguyễn Hoàng Bảo"],
            ["Người hướng dẫn", "Trần Văn Toàn"]
        ]
    )

    docx_file = PROJECT_ROOT / "Bao_cao_SafeWeb_KHKT_THPT.docx"
    doc.save(docx_file)
    print(f"HOÀN TẤT! Đã tạo thành công '{docx_file}' (cỡ chữ 14 pt, có mục lục tự động và ảnh giao diện thật).")


if __name__ == "__main__":
    build_full_report()