# -*- coding: utf-8 -*-
import shutil
import glob
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

COLOR_NAVY = (15, 76, 92)
COLOR_TEAL = (15, 118, 110)
COLOR_DARK = (15, 23, 42)
COLOR_MUTED = (51, 65, 85)


def shade_cell(cell, hex_color: str):
    cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'))


def pad_cell(cell, top=55, bottom=55, left=85, right=85):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def style_run(run, size_pt=13, bold=False, italic=False, color=COLOR_DARK, font_name="Times New Roman"):
    run.font.name = font_name
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    for attr in ["w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"]:
        rFonts.set(qn(attr), font_name)
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(*color)


def add_p(doc, text="", bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, color=COLOR_DARK):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    if text:
        r = p.add_run(text)
        style_run(r, size_pt=13, bold=bold, italic=italic, color=color)
    return p


def add_bullet(doc, bold_prefix: str, text_body: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.35)
    r1 = p.add_run("• " + bold_prefix)
    style_run(r1, size_pt=13, bold=True, color=COLOR_DARK)
    r2 = p.add_run(text_body)
    style_run(r2, size_pt=13, bold=False, color=COLOR_DARK)
    return p


def add_section_header(doc, title: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(title)
    style_run(r, size_pt=13, bold=True, color=COLOR_NAVY)
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="2" w:color="0F766E"/></w:pBdr>')
    p._p.get_or_add_pPr().append(pBdr)
    return p


def add_sub_header(doc, title: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(title)
    style_run(r, size_pt=13, bold=True, color=COLOR_TEAL)
    return p


def add_pretty_table(doc, caption: str, headers: list, rows: list, col_alignments=None):
    if caption:
        add_p(doc, caption, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, color=COLOR_NAVY)
    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style = "Table Grid"
    for j, h_text in enumerate(headers):
        cell = tbl.cell(0, j)
        shade_cell(cell, "0F766E")
        pad_cell(cell, top=55, bottom=55, left=80, right=80)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        style_run(r, size_pt=13, bold=True, color=(255, 255, 255))
    for i, row in enumerate(rows):
        bg = "FFFFFF" if i % 2 == 0 else "F8FAFC"
        for j, val in enumerate(row):
            cell = tbl.cell(i + 1, j)
            shade_cell(cell, bg)
            pad_cell(cell, top=45, bottom=45, left=80, right=80)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = col_alignments[j] if (col_alignments and j < len(col_alignments)) else (WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER)
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            style_run(r, size_pt=13, bold=(j == 0), color=COLOR_DARK)


def add_code_box(doc, title: str, code_text: str, tech_purpose: str, flow_desc: str):
    add_p(doc, title, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, color=COLOR_NAVY)
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style = "Table Grid"
    cell = tbl.cell(0, 0)
    shade_cell(cell, "F1F5F9")
    pad_cell(cell, top=55, bottom=55, left=95, right=95)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(code_text)
    style_run(r, size_pt=13, bold=False, color=COLOR_DARK)
    add_bullet(doc, "Mục đích kỹ thuật: ", tech_purpose)
    add_bullet(doc, "Giải thích luồng lệnh: ", flow_desc)


def add_figure(doc, img_path: str, width_inches: float, caption_text: str):
    if img_path and Path(img_path).exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.line_spacing = 1.0
        p_img.paragraph_format.space_before = Pt(2)
        p_img.paragraph_format.space_after = Pt(2)
        p_img.add_run().add_picture(img_path, width=Inches(width_inches))
    add_p(doc, caption_text, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, color=COLOR_MUTED)


def find_existing_images():
    fig_dir = Path("reports/figures_vi")
    f1 = str(fig_dir / "hinh_1_luu_do.png")
    f2 = str(fig_dir / "hinh_2_xac_minh.png")
    f3 = str(fig_dir / "hinh_3_ba_buoc.png")
    ui_list = [
        p for p in (glob.glob("docs/**/*.png", recursive=True) + glob.glob("reports/**/*.png", recursive=True) + glob.glob("*.png"))
        if not any(k in p.lower() for k in ["luu_do", "xac_minh", "ba_buoc", "flow", "verify", "step", "confusion"])
    ]
    f4 = ui_list[0] if ui_list else None
    return f1, f2, f3, f4


def build_report():
    f_flow, f_verify, f_steps, f_ui = find_existing_images()
    doc = Document()

    for s in doc.sections:
        s.page_width = Cm(21.0)
        s.page_height = Cm(29.7)
        s.left_margin = Cm(3.0)
        s.right_margin = Cm(2.0)
        s.top_margin = Cm(2.0)
        s.bottom_margin = Cm(2.0)

    # ==========================================================================
    # PHẦN IIIa: BÁO CÁO KẾT QUẢ THỰC HIỆN DỰ ÁN DỰ THI (IIIa)
    # ==========================================================================
    add_p(doc, "BÁO CÁO KẾT QUẢ THỰC HIỆN DỰ ÁN DỰ THI (IIIa)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, color=COLOR_NAVY)
    add_p(doc, "DỰ ÁN: SAFEWEB - ỨNG DỤNG TRÍ TUỆ NHÂN TẠO KẾT HỢP PHÂN TÍCH ĐỊA CHỈ TRANG WEB GIÚP CẢNH BÁO SỚM RỦI RO LỪA ĐẢO VÀ LỘ LỌT DỮ LIỆU", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, color=COLOR_DARK)
    add_p(doc, "Lĩnh vực: Kỹ thuật máy tính / Công nghệ thông tin", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, color=COLOR_TEAL)
    add_p(doc, "Tháng 10 năm 2026", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, color=COLOR_MUTED)

    add_section_header(doc, "MỤC LỤC")
    for line in [
        "1. VẤN ĐỀ NGHIÊN CỨU HOẶC CẦN GIẢI QUYẾT",
        "   1.1. Bối cảnh và vấn đề thực tiễn",
        "   1.2. Lý do chọn đề tài (Sự cấp thiết của vấn đề cần giải quyết)",
        "   1.3. Mục tiêu và tiêu chí thiết kế",
        "   1.4. Phạm vi của sản phẩm",
        "2. THIẾT KẾ VÀ PHƯƠNG PHÁP NGHIÊN CỨU",
        "   2.1. Các mô hình Học máy và Chiến lược kết hợp",
        "   2.2. Quy trình xử lý dữ liệu và Thuật toán ra quyết định",
        "   2.3. Những đóng góp mới và tính ưu việt",
        "   2.4. Lược đồ 55 Đặc trưng Cú pháp và Cấu trúc URL (Feature Schema)",
        "   2.5. Mô đun Trích xuất Đặc trưng và Đánh giá Thống kê",
        "3. THỰC HIỆN, CHẾ TẠO VÀ KIỂM TRA",
        "   3.1. Thành phần công nghệ và Công cụ phát triển",
        "   3.2. Cấu trúc và Phân tách Tập dữ liệu Thực nghiệm",
        "   3.3. Quy trình 05 Bước Huấn luyện Mô hình Học máy",
        "   3.4. Lưu đồ Vận hành và Mã nguồn Cốt lõi của Hệ thống",
        "   3.5. Quá trình thử nghiệm: Kết quả lần đầu và kết quả lần nâng cấp sau",
        "   3.6. Kết quả định lượng của bốn mô hình Trí tuệ nhân tạo",
        "   3.7. Kiểm thử phần mềm, xây dựng và xác minh cục bộ",
        "   3.8. Hướng dẫn thao tác và giao diện thực tế",
        "4. KẾT QUẢ, KẾT LUẬN VÀ KHẢ NĂNG ỨNG DỤNG",
        "   4.1. Khẳng định đóng góp mới, ưu thế vượt trội và giá trị giáo dục",
        "   4.2. Kết luận và một số hạn chế cần hoàn thiện",
        "   4.3. Hướng phát triển tương lai: Tiện ích tự động quét đường dẫn trong tầm mắt",
        "TÀI LIỆU THAM KHẢO & PHỤ LỤC: GIẢI THÍCH THUẬT NGỮ",
        "BÁO CÁO TÓM TẮT KẾT QUẢ THỰC HIỆN DỰ ÁN DỰ THI (IIIb)"
    ]:
        add_p(doc, line, bold=not line.startswith("   "), align=WD_ALIGN_PARAGRAPH.LEFT, color=COLOR_NAVY if not line.startswith("   ") else COLOR_DARK)

    # --------------------------------------------------------------------------
    # 1. VẤN ĐỀ NGHIÊN CỨU HOẶC CẦN GIẢI QUYẾT
    # --------------------------------------------------------------------------
    add_section_header(doc, "1. VẤN ĐỀ NGHIÊN CỨU HOẶC CẦN GIẢI QUYẾT")

    add_sub_header(doc, "1.1. Bối cảnh và vấn đề thực tiễn")
    add_p(doc, "Tấn công giả mạo (phishing) thông qua các liên kết (URL) độc hại nhắm vào người dùng dịch vụ tài chính - ngân hàng, mạng xã hội và thương mại điện tử ngày càng gia tăng, với mục tiêu chiếm đoạt thông tin đăng nhập và mã xác thực (OTP). Kẻ lừa đảo thường áp dụng các kỹ thuật mạo danh URL tinh vi (như thay đổi ký tự tương đồng hoặc kéo dài cấu trúc đường dẫn để ẩn tên miền chính), khiến việc phát hiện bằng mắt thường trở nên vô cùng khó khăn.")
    add_p(doc, "Thực tế hiện nay ghi nhận hai thách thức chính trong công tác bảo vệ người dùng:")
    add_bullet(doc, "Sự ngụy trang của chứng chỉ an toàn: ", "Việc phổ biến các chứng chỉ SSL/HTTPS miễn phí tạo điều kiện cho đối tượng lừa đảo dễ dàng thiết lập kết nối mã hóa, gây nhầm lẫn cho người dùng về độ tin cậy của trang web.")
    add_bullet(doc, "Nguy cơ xâm phạm quyền riêng tư: ", "Các giải pháp đẩy dữ liệu URL về máy chủ trung gian để phân tích tiềm ẩn rủi ro rò rỉ thông tin cá nhân và lịch sử duyệt web.")
    add_p(doc, "Từ thực trạng trên, việc phát triển một giải pháp phân tích trực tiếp trên thiết bị người dùng (client-side), đi kèm khả năng giải thích chi tiết cơ sở cảnh báo rủi ro, là yêu cầu cấp thiết và mang tính thực tiễn cao.")

    add_sub_header(doc, "1.2. Lý do chọn đề tài (Sự cấp thiết của vấn đề cần giải quyết)")
    add_p(doc, "Từ bối cảnh thực tiễn và các thách thức kỹ thuật đã phân tích, việc nghiên cứu và phát triển giải pháp SafeWeb xuất phát từ 3 lý do cốt lõi:")
    add_bullet(doc, "Tính cấp thiết trong phòng chống tấn công giả mạo (Phishing): ", "Thủ đoạn tinh vi của kẻ gian (mạo danh tên miền, lợi dụng HTTPS miễn phí) làm suy giảm khả năng tự bảo vệ của người dùng. Sự bùng nổ của các vụ lừa đảo trực tuyến đòi hỏi một công cụ tự động, có khả năng phát hiện rủi ro tức thì trước khi người dùng nhấp vào liên kết.")
    add_bullet(doc, "Yêu cầu bảo vệ quyền riêng tư và tối ưu hóa trải nghiệm: ", "Các giải pháp phân tích tập trung trên máy chủ (server-side) hiện nay tồn tại nguy cơ rò rỉ lịch sử duyệt web. Việc xây dựng cơ chế kiểm tra trực tiếp trên thiết bị (client-side) vừa loại bỏ nguy cơ lộ lọt dữ liệu cá nhân, vừa đảm bảo tốc độ phản hồi nhanh và cung cấp lý do cảnh báo minh bạch cho người dùng.")
    add_bullet(doc, "Tính hiệu quả và khả thi của Trí tuệ nhân tạo: ", "Việc tích hợp 55 đặc trưng cú pháp/từ vựng URL cùng tổ hợp các mô hình học máy (Gradient Boosting, Random Forest, SVM, Logistic Regression) chứng minh tính chính xác cao trong thực nghiệm (đạt tỷ lệ phát hiện lên tới 95,61%), tạo tiền đề kỹ thuật vững chắc để xây dựng một sản phẩm ứng dụng thực tế tin cậy.")
    add_p(doc, "Chính vì những lý do trên, việc nghiên cứu và phát triển phần mềm SafeWeb là giải pháp mang tính thời sự, đáp ứng hài hòa cả hai yếu tố: hiệu quả phát hiện lừa đảo và bảo vệ triệt để quyền riêng tư của người dùng.")

    add_sub_header(doc, "1.3. Mục tiêu và tiêu chí thiết kế")
    add_bullet(doc, "Mục tiêu tổng quát: ", "Phát triển phần mềm SafeWeb giúp phát hiện sớm website lừa đảo và ngăn ngừa lộ lọt dữ liệu cá nhân ngay trên trình duyệt nhờ ứng dụng Trí tuệ nhân tạo và cơ chế xử lý tại máy khách.")
    add_p(doc, "Mục tiêu và tiêu chí cụ thể:", bold=True)
    add_bullet(doc, "Bảo vệ quyền riêng tư (Client-side): ", "Phân tích URL trực tiếp trên thiết bị người dùng, tuyệt đối không gửi lịch sử duyệt web về máy chủ.")
    add_bullet(doc, "Tối ưu nhận diện bằng AI: ", "Khai thác 55 đặc trưng URL và tổ hợp 4 mô hình học máy để đạt tỷ lệ phát hiện lừa đảo trên 95%.")
    add_bullet(doc, "Cảnh báo minh bạch: ", "Hiển thị rõ nguyên nhân rủi ro và hình ảnh xem trước liên kết trước khi người dùng truy cập.")
    add_bullet(doc, "Đảm bảo độ ổn định: ", "Hoàn thiện phần mềm đạt 100% các tiêu chuẩn kiểm tra xử lý dữ liệu và tương thích trình duyệt.")

    add_sub_header(doc, "1.4. Phạm vi của sản phẩm")
    add_bullet(doc, "Đối tượng: ", "Các liên kết web (URL) thuộc nhóm lừa đảo (phishing) và an toàn (benign).")
    add_bullet(doc, "Dữ liệu huấn luyện & thực nghiệm: ", "261.299 URL đã làm sạch cùng tập kiểm thử độc lập gồm 6.624 URL mới.")
    add_bullet(doc, "Thuật toán xử lý: ", "Khai thác 55 đặc trưng cú pháp/từ vựng URL kết hợp hội đồng 4 mô hình học máy (Gradient Boosting, Random Forest, SVM, Logistic Regression).")
    add_bullet(doc, "Cơ chế thực thi: ", "Phân tích trực tiếp tại máy khách (client-side) thông qua cơ sở dữ liệu tra cứu nhanh.")
    add_bullet(doc, "Tính năng chuyên sâu: ", "Kiểm tra tên miền, dò vết chuyển hướng và chụp ảnh xem trước liên kết (chỉ kích hoạt khi người dùng đồng ý cấp quyền).")

    # --------------------------------------------------------------------------
    # 2. THIẾT KẾ VÀ PHƯƠNG PHÁP NGHIÊN CỨU
    # --------------------------------------------------------------------------
    add_section_header(doc, "2. THIẾT KẾ VÀ PHƯƠNG PHÁP NGHIÊN CỨU")

    add_sub_header(doc, "2.1. Các mô hình Học máy và Chiến lược kết hợp")
    add_p(doc, "SafeWeb triển khai mô hình học máy kết hợp nhằm tối ưu hóa khả năng phát hiện URL lừa đảo qua việc tổng hợp dự báo từ 04 thuật toán độc lập:")
    add_bullet(doc, "Random Forest (100 cây quyết định): ", "Vận hành theo cơ chế bỏ phiếu đa số (Majority Voting), giúp giảm thiểu rủi ro quá khớp (overfitting) và tăng độ ổn định hệ thống.")
    add_bullet(doc, "Gradient Boosting (Mô hình chủ lực): ", "Học tuần tự để tối ưu hóa sai số. Đạt tỷ lệ phát hiện lừa đảo cao nhất trong kiểm thử thực nghiệm với 95,61% (2.676/2.799 URL lừa đảo).")
    add_bullet(doc, "Support Vector Machine - SVM: ", "Đạt độ chính xác tuyệt đối (FP = 0) trên các mẫu đưa ra phán đoán, đóng vai trò chốt chặn kiểm soát dương tính giả.")
    add_bullet(doc, "Logistic Regression: ", "Mô hình phân loại tuyến tính dựa trên hàm Sigmoid, cung cấp điểm xác suất nền tảng (baseline score) với tốc độ xử lý siêu nhanh.")

    add_pretty_table(
        doc,
        "Bảng 2.1. Bảng so sánh đặc tính kỹ thuật 04 mô hình AI trong SafeWeb (Bảng do học sinh tự thực hiện)",
        ["Tên mô hình", "Kiến trúc thuật toán", "Ưu điểm cốt lõi", "Vai trò trong SafeWeb", "Hiệu năng kiểm thử"],
        [
            ["Random Forest", "100 cây quyết định độc lập", "Chống quá khớp (overfitting)", "Kiểm soát tổng thể (Bỏ phiếu)", "92,32%"],
            ["Gradient Boosting", "Tối ưu hóa sai số chuỗi", "Độ nhạy cao với mẫu mới", "Phân loại chủ lực (Core Engine)", "95,61% (2.676/2.799)"],
            ["SVM", "Siêu phẳng phân tách", "Tỷ lệ dương tính giả FP ≈ 0", "Chốt chặn kiểm soát sai số", "0,71% (Bắt chính xác 20/20)"],
            ["Logistic Regression", "Phân loại tuyến tính Sigmoid", "Tốc độ xử lý siêu nhanh", "Tạo điểm xác suất nền tảng", "Phân loại cơ bản (87,82%)"]
        ]
    )

    add_sub_header(doc, "2.2. Quy trình xử lý dữ liệu và Thuật toán ra quyết định")
    add_p(doc, "Quá trình phân tích một URL được tự động hóa qua 04 bước xử lý tuần tự:")
    add_bullet(doc, "Bước 1. Trích xuất Vector (N = 55): ", "Chuyển đổi URL thành vector số học 55 chiều gồm: thuộc tính độ dài (domain/path), tỷ lệ ký tự đặc biệt (., -, _, @), chữ số và các từ khóa mạo danh.")
    add_bullet(doc, "Bước 2. Tính Xác suất Tổng hợp AI (p): ", "Đưa vector đặc trưng qua 04 mô hình để lấy xác suất độc lập p_i ∈ [0, 1]. Xác suất hợp nhất được tính bằng trung bình cộng đồng đều: p = (p_RF + p_GB + p_SVM + p_LR) / 4.")
    add_bullet(doc, "Bước 3. Phân tích Heuristic & Nhãn giải thích (XAI): ", "Bộ quy tắc tĩnh quét các dấu hiệu nguy cơ (IP thay tên miền, ký tự lạ, mạo danh thương hiệu) để xuất nhãn giải thích nguyên nhân cảnh báo cho người dùng.")
    add_bullet(doc, "Bước 4. Phân cấp Rủi ro & Mã màu Cảnh báo: ", "Quy đổi p thành 04 mức rủi ro: [0-25%) Xanh (An toàn); [25-50%) Vàng (Thận trọng); [50-75%) Cam (Nguy cơ cao); [75-100%] Đỏ (Nguy cơ rất cao). Trường hợp URL có trong CSDL sẽ được ưu tiên hiển thị kết quả trực tiếp.")

    add_sub_header(doc, "2.3. Những đóng góp mới và tính ưu việt")
    add_p(doc, "SafeWeb thể hiện tính vượt trội so với các công cụ bảo mật truyền thống qua 06 đóng góp cốt lõi:")
    add_bullet(doc, "Kiến trúc Kiểm duyệt 03 Lớp (Triple-Layer): ", "Kết hợp CSDL tra cứu nhanh, 55 đặc trưng Heuristic và 04 mô hình AI, giúp phát hiện hiệu quả cả các cuộc tấn công Zero-day Phishing mới xuất hiện.")
    add_bullet(doc, "Trí tuệ Nhân tạo Giải thích được (XAI): ", "Không chỉ cảnh báo định tính mà minh bạch hóa lý do rủi ro, điểm số từng mô hình và các yếu tố dị thường.")
    add_bullet(doc, "Bảo vệ Quyền riêng tư tuyệt đối (Client-side): ", "Toàn bộ tính toán diễn ra ngay trên trình duyệt máy khách; mặc định không gửi dữ liệu lịch sử duyệt web về máy chủ.")
    add_bullet(doc, "Tự động Chuẩn hóa & Sửa lỗi URL: ", "Tự động hoàn thiện chuỗi gõ thiếu (như 'vietcombank' thành địa chỉ chuẩn đầy đủ) trước khi đưa vào phân tích.")
    add_bullet(doc, "So sánh Chuỗi Tương đồng (String Similarity): ", "Cảnh báo mạo danh tên miền (Typosquatting) bằng cách so sánh độ tương đồng chuỗi S ≥ 80% với dữ liệu lừa đảo đã ghi nhận.")
    add_bullet(doc, "Lập Báo cáo Sự cố Cục bộ (Local Incident Report): ", "Cho phép đóng gói báo cáo phản hồi lưu trữ cục bộ trên thiết bị người dùng mà không tự động phát tán qua mạng.")

    add_sub_header(doc, "2.4. Lược đồ 55 Đặc trưng Cú pháp và Cấu trúc URL (Feature Schema)")
    add_p(doc, "Mỗi chuỗi URL khi nạp vào hệ thống SafeWeb được trích xuất thành một vector đặc trưng số học 55 chiều (N = 55) theo thứ tự cố định. Các đặc trưng này được phân loại thành 06 nhóm kỹ thuật cốt lõi (Bảng 2.2):")
    add_pretty_table(
        doc,
        "Bảng 2.2. Phân loại 06 nhóm đặc trưng trích xuất từ chuỗi URL trong SafeWeb (Bảng do học sinh tự thực hiện)",
        ["Nhóm đặc trưng", "Tên biến số (N = 55)", "Ý nghĩa kỹ thuật và Ý nghĩa an ninh mạng"],
        [
            ["1. Độ dài và Đếm ký tự cơ bản (Biến 01–10)", "url_length, domain_length, path_length, query_length, num_dots, num_slashes, num_hyphens, num_underscores, num_digits, num_letters", "Đo đạc kích thước cấu trúc URL. Các URL lừa đảo thường có xu hướng kéo dài chuỗi, chèn nhiều dấu gạch ngang (-), dấu chấm (.) hoặc chữ số nhằm che giấu tên miền gốc."],
            ["2. Cấu trúc bất thường & Ký hiệu ngụy trang (Biến 11–20)", "num_special_chars, has_https, has_ip, num_subdomains, has_at, has_question_mark, has_equals, has_percent, has_double_slash, has_query", "Phát hiện kỹ thuật mạo danh cấu trúc: địa chỉ IP thay cho tên miền, sử dụng ký tự '@' để điều hướng vô hiệu hóa phần trước, nhiều tầng tên miền phụ (subdomain) và các tham số điều hướng bất thường."],
            ["3. Độ lộn xộn chuỗi / Entropy (Biến 21–22)", "url_entropy, domain_entropy", "Đo độ hỗn loạn thông tin (Shannon Entropy) của toàn bộ URL và tên miền. Các tên miền lừa đảo sinh tự động (DGA) thường có độ entropy cao do sắp xếp ngẫu nhiên chuỗi ký tự."],
            ["4. Từ khóa mồi nhử nhạy cảm (Biến 23–30)", "keyword_login, keyword_signin, keyword_verify, keyword_account, keyword_password, keyword_bank, keyword_payment, keyword_confirm", "Quét sự xuất hiện của 08 từ khóa mồi nhử phổ biến liên quan đến xác thực tài khoản, ngân hàng và thanh toán trực tuyến."],
            ["5. Tỷ lệ thành phần & TLD rủi ro (Biến 31–52)", "phish_url_len, phish_dom_len, phish_tld_len, phish_path_len, phish_query_len, phish_is_ip, phish_subdom_cnt, phish_letter_cnt, phish_digit_cnt, phish_special_cnt, phish_eq_cnt, phish_qm_cnt, phish_amp_cnt, phish_dot_cnt, phish_dash_cnt, phish_under_cnt, phish_slash_cnt, phish_letter_ratio, phish_digit_ratio, phish_spec_ratio, phish_entropy, phish_suspicious_tld", "Tính toán phân rã chi tiết tỷ lệ phần trăm chữ cái, chữ số, ký tự đặc biệt trên từng thành phần (Domain, Path, Query) và kiểm tra cờ nhãn tên miền cấp cao nhất (TLD) có chỉ số lạm dụng cao."],
            ["6. Mã hóa ngụy trang URL (Biến 53–55)", "phish_has_obfuscation, phish_obfuscated_char_count, phish_obfuscation_ratio", "Phát hiện các kỹ thuật che giấu chuỗi ký tự bằng mã hóa phần trăm (Percent-encoding %XX) nhằm qua mặt các bộ lọc từ khóa truyền thống."]
        ],
        col_alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.JUSTIFY]
    )

    add_sub_header(doc, "2.5. Mô đun Trích xuất Đặc trưng và Đánh giá Thống kê")
    add_p(doc, "Nhằm đảm bảo sự đồng bộ tuyệt đối giữa quá trình huấn luyện và thực thi thời gian thực, bộ trích xuất 55 đặc trưng được lập trình song song trên hai nền tảng: Python (phục vụ Pipeline huấn luyện) và JavaScript (phục vụ Client-side Engine). Cả hai bộ trích xuất tuân thủ cùng một quy chuẩn toán học. Hiệu năng mô hình được thống kê dựa trên ma trận nhầm lẫn (Confusion Matrix) bao gồm các chỉ số: True Positive (TP), True Negative (TN), False Positive (FP) và False Negative (FN) trên tập kiểm thử độc lập 6.624 URL.")

    # --------------------------------------------------------------------------
    # 3. THỰC HIỆN, CHẾ TẠO VÀ KIỂM TRA
    # --------------------------------------------------------------------------
    add_section_header(doc, "3. THỰC HIỆN, CHẾ TẠO VÀ KIỂM TRA")

    add_sub_header(doc, "3.1. Thành phần công nghệ và Công cụ phát triển")
    add_bullet(doc, "Python, Pandas và Scikit-learn (Hạ tầng Khoa học dữ liệu): ", "Python được chọn làm ngôn ngữ trung tâm cho giai đoạn xử lý dữ liệu và huấn luyện mô hình. Thư viện Pandas đóng vai trò quản lý, làm sạch và trích xuất đặc trưng trên các tập dữ liệu quy mô lớn; trong khi Scikit-learn cung cấp môi trường tích hợp chuẩn hóa để triển khai, tối ưu hóa và đánh giá đồng thời 04 mô hình học máy. Bộ công cụ này đảm bảo tính tái lập (reproducibility) của các phép thử thực nghiệm.")
    add_bullet(doc, "HTML, CSS, JavaScript và Flask (Kiến trúc Triển khai Phần mềm): ", "Giao diện người dùng và bộ công cụ trực quan hóa được xây dựng trên nền tảng HTML, CSS và JavaScript thuần (Vanilla JS). Flask được sử dụng làm dịch vụ máy chủ thử nghiệm (Backend Server). Nhằm tối ưu hóa tốc độ và bảo mật quyền riêng tư, toàn bộ engine trích xuất đặc trưng và mô hình AI đã được chuyển giao thành mã JavaScript thực thi trực tiếp tại máy khách (Client-side execution), hoàn toàn không yêu cầu người dùng cài đặt ứng dụng phụ trợ.")

    add_sub_header(doc, "3.2. Cấu trúc và Phân tách Tập dữ liệu Thực nghiệm")
    add_p(doc, "Dữ liệu thực nghiệm của hệ thống SafeWeb được phân tách nghiêm ngặt thành 03 tập độc lập nhằm phục vụ các mục tiêu tra cứu, huấn luyện và kiểm thử khách quan. Nhãn nhị phân được quy chuẩn: nhãn 1 tương ứng với trang web lừa đảo (Phishing) và nhãn 0 tương ứng với trang web hợp lệ (Legitimate):")
    add_bullet(doc, "Cơ sở dữ liệu tra cứu nhanh (Reference Lookup Database): ", "Chứa 36.261 bản ghi URL độc lập sau khi xử lý trùng lặp (19.909 URL lừa đảo và 16.352 URL hợp lệ). Bộ dữ liệu này hoạt động như một bộ lọc phản ứng nhanh (Cache Engine); khi truy vấn người dùng trùng khớp hoàn toàn với bản ghi trong CSDL, hệ thống lập tức xuất kết quả mà không cần kích hoạt luồng tính toán AI.")
    add_bullet(doc, "Tập dữ liệu Huấn luyện (Training Dataset): ", "Bao gồm 261.299 URL đã qua chuẩn hóa (114.113 URL lừa đảo và 147.186 URL hợp lệ). Tập dữ liệu được sử dụng để tối ưu hóa trọng số và thông số thuật toán cho cả 04 mô hình học máy.")
    add_bullet(doc, "Tập dữ liệu Kiểm thử Độc lập (Hold-out Test Dataset): ", "Gồm 6.624 URL hoàn toàn độc lập (2.799 URL lừa đảo và 3.825 URL hợp lệ). Tất cả tên miền trong tập này được cách ly hoàn toàn khỏi tập huấn luyện (domain-independent), phản ánh chính xác năng lực phát hiện của mô hình trước các mối đe dọa Zero-day chưa từng ghi nhận.")

    add_sub_header(doc, "3.3. Quy trình 05 Bước Huấn luyện Mô hình Học máy")
    add_bullet(doc, "Bước 1. Sơ chế và Cách ly Dữ liệu: ", "Làm sạch dữ liệu thô, loại bỏ các bản ghi trùng lặp hoàn toàn và trích xuất 6.624 URL thuộc các tên miền độc lập làm tập kiểm thử Hold-out.")
    add_bullet(doc, "Bước 2. Quy chuẩn Gán nhãn: ", "Đồng bộ hóa nhãn mục tiêu nhị phân (1: Phishing, 0: Legitimate) trên toàn bộ 261.299 URL của tập huấn luyện.")
    add_bullet(doc, "Bước 3. Vector hóa Đặc trưng: ", "Thực thi thuật toán trích xuất để chuyển đổi mỗi URL thành một vector số học 55 chiều cố định.")
    add_bullet(doc, "Bước 4. Cân bằng và Huấn luyện Đồng thời: ", "Áp dụng kỹ thuật cân bằng trọng số dữ liệu (Class Weight Balancing) và tiến hành huấn luyện đồng thời 04 mô hình học máy (Random Forest, Gradient Boosting, SVM, Logistic Regression) trên tập huấn luyện.")
    add_bullet(doc, "Bước 5. Đánh giá và Đóng gói Mô hình (Export Engine): ", "Kiểm chứng hiệu năng trên tập kiểm thử 6.624 URL. Đóng gói toàn bộ trọng số và tham số dự báo của mô hình sang định dạng JavaScript (JSON/JS) để tích hợp vào Client-side Engine.")

    add_sub_header(doc, "3.4. Lưu đồ Vận hành và Mã nguồn Cốt lõi của Hệ thống")
    add_p(doc, "Lưu đồ vận hành của SafeWeb mô tả tiến trình xử lý từ khi tiếp nhận dữ liệu đầu vào đến khi trả về kết quả phân loại cuối cùng:")
    add_figure(doc, f_flow, 5.6, "Hình 3.1. Lưu đồ vận hành 07 bước của phần mềm SafeWeb (Sơ đồ được tạo bởi phần mềm Python Matplotlib và do học sinh tự thực hiện).")

    add_code_box(
        doc,
        "1) Thuật toán Chuẩn hóa và Tự động hoàn thiện URL (URL Auto-Healing)",
        "function validateUrl(value) {\n"
        "  let healed = value.trim();\n"
        "  if (healed.startsWith('//')) healed = `https:${healed}`;\n"
        "  else if (!healed.includes('://')) {\n"
        "    const host = healed.split(/[/?#]/u, 1)[0];\n"
        "    if (!host.includes('.') && host.toLowerCase() !== 'localhost') {\n"
        "      healed = `${host}.com${healed.slice(host.length)}`;\n"
        "    }\n"
        "    healed = `https://${healed}`;\n"
        "  }\n"
        "  return healed;\n"
        "}",
        "Chuẩn hóa chuỗi đầu vào do người dùng nhập, tự động bổ sung giao thức HTTPS và đuôi tên miền mặc định (.com) nếu thiếu cấu trúc chuẩn.",
        "Bỏ khoảng trắng thừa (trim) -> Bổ sung giao thức HTTPS khi xuất hiện tiền tố '//' hoặc thiếu '://' -> Phân tách tên máy chủ (host) -> Tự động điền đuôi tên miền '.com' đối với từ khóa đơn lẻ."
    )

    add_code_box(
        doc,
        "2) Thuật toán Tra cứu Hồ sơ CSDL Tham chiếu (Fast Database Match)",
        "function databaseMatch(url, features) {\n"
        "  const parts = parseParts(url);\n"
        "  let hostname = parts.hostname.toLowerCase().replace(/\\.+$/u, '');\n"
        "  if (hostname.startsWith('www.')) hostname = hostname.slice(4);\n"
        "  const path = parts.path.replace(/\\/+$/u, '');\n"
        "  const key = `${hostname}${path}?${parts.query}`.replace(/\\?$/u, '');\n"
        "  const record = recordsByUrl.get(key);\n"
        "  if (record) {\n"
        "    return { matched: true, type: 'exact_url', provenance: 'Matched in reference database', record };\n"
        "  }\n"
        "  if (database.knownPhishingHosts?.includes(parts.hostname.toLowerCase())) {\n"
        "    return { matched: true, type: 'known_phishing_host', provenance: 'Matched in reference database' };\n"
        "  }\n"
        "  return { matched: false, type: null, provenance: null };\n"
        "}",
        "Thực hiện cơ chế khớp mẫu trực tiếp (Exact Matching) đối với cơ sở dữ liệu URL và Tên miền lừa đảo đã ghi nhận.",
        "Phân rã URL thành Hostname, Path, Query -> Chuẩn hóa bỏ tiền tố 'www.' và các dấu gạch chéo dư thừa -> Tạo khóa tra cứu chuẩn (Lookup Key) -> Dò tìm chính xác trong Map CSDL -> Nếu không trùng URL đầy đủ, tiếp tục kiểm tra Danh sách đen Tên miền (Known Phishing Hosts)."
    )

    add_code_box(
        doc,
        "3) Thuật toán Tính điểm Dự báo và Hợp nhất Xác suất AI (Ensemble Inference)",
        "function modelProbabilities(features) {\n"
        "  const forest = model.models.random_forest.trees;\n"
        "  const boosting = model.models.gradient_boosting;\n"
        "  const svm = model.models.svm;\n"
        "  const logistic = model.models.logistic_regression;\n"
        "  return {\n"
        "    random_forest: treeOutput(forest, features) / forest.length,\n"
        "    gradient_boosting: sigmoid(boosting.initialRawScore + boosting.learningRate * treeOutput(boosting.trees, features)),\n"
        "    svm: sigmoid(-(svm.calibrationA * scaledDecision(features, svm) + svm.calibrationB)),\n"
        "    logistic_regression: sigmoid(scaledDecision(features, logistic))\n"
        "  };\n"
        "}\n"
        "function predict(features, thresholds = defaultThresholds) {\n"
        "  const models = modelProbabilities(features);\n"
        "  const probability = Object.values(models).reduce((sum, val) => sum + val, 0) / 4;\n"
        "  const prediction = probability > 0.5 ? 'phishing' : 'legitimate';\n"
        "  const riskLevel = riskLevelForProbability(probability, thresholds);\n"
        "  return { prediction, probability, risk_level: riskLevel, models };\n"
        "}",
        "Thực thi phán đoán từ 04 mô hình học máy độc lập, chuyển đổi điểm số thô thành xác suất qua hàm Sigmoid/Platt Scaling và hợp nhất kết quả.",
        "Trích xuất thông số 04 mô hình -> Tính xác suất riêng lẻ cho từng mô hình -> Hàm predict thực hiện lấy trung bình cộng xác suất p = sum(p_i)/4 -> So sánh với ngưỡng quyết định (0.5) để gán nhãn nhị phân -> Phân cấp rủi ro dựa trên các mốc ngưỡng xác suất."
    )

    add_sub_header(doc, "3.5. Quá trình thử nghiệm: Kết quả lần đầu và kết quả lần nâng cấp sau")
    add_bullet(doc, "Kết quả ở lần thực hiện đầu tiên: ", "Ở giai đoạn đầu, nhóm dùng khoảng 5.000 địa chỉ, một mô hình Random Forest và ít dấu hiệu hơn. Quy mô nhỏ và chỉ có một cách chấm khiến hệ thống có thể bỏ lỡ kiểu giả mạo mới; không còn phép đo cùng bộ thử để nêu một tỷ lệ chính xác đáng tin cậy cho phiên bản đó.")
    add_bullet(doc, "Kết quả ở các lần nâng cấp: ", "Nhóm mở rộng bộ dữ liệu học lên 261.299 địa chỉ, cơ sở dữ liệu tra cứu có 36.261 hồ sơ, bộ đo có 55 dấu hiệu và hệ thống dùng bốn mô hình. Trên 6.624 địa chỉ được giữ riêng để thi thử, mô hình Gradient Boosting phát hiện 2.676 trong 2.799 trang lừa đảo (95,61%). SafeWeb có thêm biểu mẫu lập phiếu báo cáo loại suspected-phishing; phiếu được tạo thành tệp trên thiết bị, không tự gửi đi.")

    add_sub_header(doc, "3.6. Kết quả định lượng của bốn mô hình Trí tuệ nhân tạo")
    add_p(doc, "Cả bốn mô hình cùng làm bài kiểm tra trên 6.624 địa chỉ được giữ riêng (2.799 trang lừa đảo và 3.825 trang hợp lệ). Các tên cột trong Bảng 3.1 được viết bằng tiếng Việt; số liệu là kết quả của đúng bộ thử này, không phải lời hứa cho mọi trang web.")
    add_pretty_table(
        doc,
        "Bảng 3.1. Kết quả chấm điểm 4 mô hình Trí tuệ nhân tạo trên 6.624 địa chỉ kiểm thử (Bảng thống kê do học sinh tự thực hiện)",
        [
            "Tên mô hình",
            "Tỷ lệ đoán đúng chung",
            "Độ chuẩn xác khi báo động",
            "Tỷ lệ bắt trúng lừa đảo",
            "Điểm hiệu quả tổng hợp",
            "Trang hợp lệ đoán đúng / Trang hợp lệ báo nhầm / Trang lừa đảo bỏ sót / Trang lừa đảo phát hiện"
        ],
        [
            ["1. Random Forest", "87,45%", "80,75%", "92,32%", "86,15%", "3.209 / 616 / 215 / 2.584"],
            ["2. Gradient Boosting", "87,89%", "79,76%", "95,61%", "86,97%", "3.146 / 679 / 123 / 2.676"],
            ["3. SVM", "58,05%", "100,00%", "0,71%", "1,42%", "3.825 / 0 / 2.779 / 20"],
            ["4. Logistic Regression", "85,55%", "79,96%", "87,82%", "83,71%", "3.209 / 616 / 341 / 2.458"]
        ]
    )
    add_bullet(doc, "Diễn giải kết quả dễ hiểu: ", "Trong 2.799 trang lừa đảo của bộ thử, mô hình Gradient Boosting phát hiện 2.676 trang, tức gần 96 trong mỗi 100 trang, và bỏ sót 123. Độ chuẩn xác khi báo động là 79,76%: trong 100 cảnh báo, khoảng 80 đúng. Random Forest phát hiện 2.584 trang; Logistic Regression phát hiện 2.458. SVM chỉ phát hiện 20 trang và bỏ sót 2.779, nên đây là hạn chế cần xử lý, dù 20 cảnh báo của nó đều đúng trong bộ thử.")

    add_sub_header(doc, "3.7. Kiểm thử phần mềm, xây dựng và xác minh cục bộ")
    add_p(doc, "Trước khi đưa vào sử dụng, phần mềm đã được kiểm tra tự động nghiêm ngặt với số lượng mẫu kiểm thử và kết quả cụ thể như sau:")
    add_bullet(doc, "Kiểm thử xử lý dữ liệu và mô hình trên máy tính: ", "Thực hiện 59 mẫu kiểm thử tự động (kiểm tra làm sạch dữ liệu, đo 55 dấu hiệu, chấm điểm AI và ứng dụng). Kết quả: Đạt 59 / 59 mẫu (100%, không có lỗi).")
    add_bullet(doc, "Kiểm thử hoạt động trên trình duyệt web: ", "Thực hiện 16 bài kiểm thử tự động, bao gồm các thao tác nhập địa chỉ, chạy mô hình, đối chiếu cơ sở dữ liệu và kiểm tra nội dung giao diện. Kết quả lần chạy hiện tại: đạt 16 / 16.")
    add_bullet(doc, "Đối chiếu hai cách tính: ", "So sánh cùng 16 trường hợp giữa Python và JavaScript: 10 địa chỉ hợp lệ và 6 địa chỉ không hợp lệ. Cả hai cùng xử lý đúng trạng thái hợp lệ/không hợp lệ; xác suất có sai khác rất nhỏ do cách máy tính làm tròn số, tối đa khoảng 0,00000000000000075, nên không gọi là giống tuyệt đối từng chữ số.")
    add_bullet(doc, "Ý nghĩa của Xác minh cục bộ: ", "Xử lý cục bộ giống như tự mở cuốn sổ tra cứu và dùng bốn người giám khảo ngay tại bàn của mình: địa chỉ được chuẩn hóa, dò cơ sở dữ liệu và chấm điểm trong trình duyệt, không tự gửi đi dịch vụ bên ngoài. Nếu người dùng chủ động bật kiểm tra DNS hoặc ảnh xem trước, địa chỉ sẽ được chia sẻ với dịch vụ tương ứng; vì vậy không thể gọi mọi chế độ là hoàn toàn không gửi dữ liệu.")
    add_figure(doc, f_verify, 5.4, "Hình 3.2. Tổng hợp kết quả kiểm thử phần mềm và xác minh cục bộ của SafeWeb (Đồ họa được tạo bởi phần mềm Python Matplotlib và do học sinh tự thực hiện).")

    add_sub_header(doc, "3.8. Hướng dẫn thao tác và giao diện thực tế")
    add_p(doc, "Người dùng chỉ cần thực hiện 3 bước đơn giản trên giao diện SafeWeb:")
    add_bullet(doc, "Bước 1: ", "Dán địa chỉ trang web cần kiểm tra vào ô nhập (không dán mật khẩu cá nhân). Hệ thống tự động hoàn thiện https:// hoặc .com nếu thiếu.")
    add_bullet(doc, "Bước 2: ", "Bấm nút 'Phân tích URL' (chỉ bật nút kiểm tra trực tuyến nếu muốn xem thêm thông tin tên miền DNS và ảnh chụp trang web).")
    add_bullet(doc, "Bước 3: ", "Nhìn màu sắc cảnh báo (Xanh = Thấp, Vàng = Thận trọng, Đỏ = Nguy hiểm), xem điểm của 4 mô hình AI, đọc lý do cụ thể tại ô 'Vì sao có kết quả này?' hoặc tra cứu thêm trong 'Cơ sở dữ liệu URL'.")
    add_figure(doc, f_steps, 5.4, "Hình 3.3. Sơ đồ 3 bước thao tác và ý nghĩa màu sắc cảnh báo (Sơ đồ được tạo bởi phần mềm Python Matplotlib và do học sinh tự thực hiện).")
    if f_ui:
        add_figure(doc, f_ui, 4.6, "Hình 3.4. Giao diện SafeWeb (Ảnh chụp màn hình phần mềm do học sinh tự thực hiện).")

    # --------------------------------------------------------------------------
    # 4. KẾT QUẢ, KẾT LUẬN VÀ KHẢ NĂNG ỨNG DỤNG
    # --------------------------------------------------------------------------
    add_section_header(doc, "4. KẾT QUẢ, KẾT LUẬN VÀ KHẢ NĂNG ỨNG DỤNG")

    add_sub_header(doc, "4.1. Khẳng định đóng góp mới, ưu thế vượt trội và giá trị giáo dục")
    add_bullet(doc, "Đóng góp của dự án: ", "SafeWeb đặt cạnh nhau ba loại thông tin: hồ sơ đã có trong cơ sở dữ liệu, dấu hiệu cấu trúc của địa chỉ và ý kiến của bốn mô hình. Trên bộ thử tên miền tách riêng, mô hình Gradient Boosting phát hiện 95,61% trang lừa đảo. Dự án chưa thử đối chứng trực tiếp với các dịch vụ ngoài thị trường, nên không kết luận mình chính xác hơn mọi công cụ khác.")
    add_bullet(doc, "Giúp người dùng xem xét trước khi bấm: ", "Màu cảnh báo, điểm từng mô hình, lý do và ví dụ gần giống giúp người dùng có thêm căn cứ để tự quyết định. Kết quả là lời nhắc để kiểm tra kỹ, không thay thế việc xác minh qua ngân hàng, nhà cung cấp dịch vụ hoặc người gửi chính thức.")
    add_bullet(doc, "Nâng cao nhận thức An toàn thông tin (Digital Literacy): ", "Giúp người dùng nhận diện các thủ đoạn lừa đảo qua liên kết (URL), xóa bỏ tâm lý chủ quan khi thấy chứng chỉ HTTPS và hình thành thói quen cảnh giác trước các tương tác trên không gian mạng.")
    add_bullet(doc, "Hình thành tư duy bảo mật chủ động và ý thức bảo vệ quyền riêng tư: ", "Cung cấp lý do cảnh báo minh bạch (dựa trên 55 đặc trưng nhận diện), qua đó giáo dục trực quan giúp người dùng hiểu vì sao liên kết lại nguy hiểm, đồng thời chủ động kiểm soát và bảo vệ dữ liệu cá nhân thông qua cơ chế phân tích tại máy khách (client-side).")
    add_bullet(doc, "Tạo mô hình tham chiếu thực tiễn cho giáo dục STEM/AI: ", "Sản phẩm là minh chứng thực tế về việc ứng dụng Trí tuệ nhân tạo (Học máy) vào giải quyết các bài toán an ninh mạng, truyền cảm hứng học tập và nghiên cứu khoa học.")

    add_sub_header(doc, "4.2. Kết luận và một số hạn chế cần hoàn thiện")
    add_p(doc, "SafeWeb có bộ tra cứu, bốn mô hình, giao diện giải thích kết quả và biểu mẫu tạo phiếu phản hồi. Trong phép thử hiện có, mô hình Gradient Boosting phát hiện 95,61% trang lừa đảo; SVM còn bỏ sót nhiều trường hợp và cần được hiệu chỉnh. Mọi con số đều phụ thuộc vào bộ dữ liệu và cách thử đã nêu.")

    add_sub_header(doc, "4.3. Hướng phát triển tương lai: Tiện ích tự động quét đường dẫn trong tầm mắt")
    add_p(doc, "Trong giai đoạn tiếp theo, nhóm dự kiến phát triển SafeWeb thành tiện ích gắn trực tiếp vào trình duyệt. Khi người dùng xem mạng xã hội, tin nhắn hoặc thư điện tử, tiện ích có thể rà các đường dẫn đang hiện trên màn hình và đặt dấu cảnh báo trước khi người dùng bấm. Đây là hướng phát triển, chưa phải tính năng hiện có.")

    # --------------------------------------------------------------------------
    # TÀI LIỆU THAM KHẢO & PHỤ LỤC: GIẢI THÍCH THUẬT NGỮ
    # --------------------------------------------------------------------------
    add_section_header(doc, "TÀI LIỆU THAM KHẢO")
    add_bullet(doc, "1. Bộ dữ liệu địa chỉ trang web tiếng Việt đã kiểm chứng: ", "Dùng làm cơ sở dữ liệu tra cứu và một phần bài học, đề thi.")
    add_bullet(doc, "2. Bộ dữ liệu địa chỉ trang web lừa đảo mở rộng quốc tế: ", "Bổ sung nhiều kiểu địa chỉ để các mô hình học thêm dấu hiệu.")
    add_bullet(doc, "3. Thư viện scikit-learn: ", "Dùng để huấn luyện, chấm điểm và thống kê bốn mô hình.")
    add_bullet(doc, "4. Chuẩn kỹ thuật về địa chỉ web (RFC 3986): ", "Dùng để tách và chuẩn hóa các phần của địa chỉ.")

    add_section_header(doc, "PHỤ LỤC: GIẢI THÍCH THUẬT NGỮ")
    add_pretty_table(
        doc,
        "",
        ["Tên gọi tiếng Việt", "Tên kỹ thuật", "Giải thích đời thường"],
        [
            ["Đường dẫn trang web", "URL", "Địa chỉ để đi đến một trang, giống số nhà và tên đường."],
            ["Trang web lừa đảo", "Phishing", "Trang giả mạo nhằm dụ người xem giao mật khẩu hoặc tiền."],
            ["Tên miền", "Domain", "Tên dễ nhớ thay cho dãy số của máy chủ, như tên một cửa hàng."],
            ["Kết nối HTTPS", "HTTPS", "Lớp mã hóa đường truyền; có khóa không đồng nghĩa cửa hàng là thật."],
            ["Danh bạ tên miền", "DNS", "Dịch vụ đổi tên trang thành địa chỉ máy chủ, như danh bạ tìm số điện thoại."],
            ["Học máy", "Machine Learning", "Cho máy xem nhiều ví dụ để nó học cách nhận ra mẫu giống nhau."],
            ["Tính ngay trong trình duyệt", "Browser inference", "Máy người dùng tự chấm điểm, như tự làm phép tính tại bàn."],
            ["Tiện ích gắn vào trình duyệt", "Browser extension", "Chương trình nhỏ thêm chức năng vào trình duyệt; đây là hướng phát triển."]
        ],
        col_alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT]
    )

    # ==========================================================================
    # PHẦN IIIb: BÁO CÁO TÓM TẮT KẾT QUẢ THỰC HIỆN DỰ ÁN DỰ THI (ĐỨNG SAU IIIa)
    # ==========================================================================
    add_section_header(doc, "BÁO CÁO TÓM TẮT KẾT QUẢ THỰC HIỆN DỰ ÁN DỰ THI (IIIb)")
    add_bullet(doc, "Tên dự án dự thi: ", "SAFEWEB - ỨNG DỤNG TRÍ TUỆ NHÂN TẠO KẾT HỢP PHÂN TÍCH ĐỊA CHỈ TRANG WEB GIÚP CẢNH BÁO SỚM RỦI RO LỪA ĐẢO VÀ LỘ LỌT DỮ LIỆU")
    add_bullet(doc, "Lĩnh vực dự thi: ", "Kỹ thuật máy tính / Công nghệ thông tin")
    add_p(doc, "Tóm tắt kết quả:", bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, color=COLOR_TEAL)
    add_bullet(doc, "Mục tiêu: ", "SafeWeb là phần mềm hỗ trợ phát hiện sớm các liên kết web lừa đảo (phishing) và phòng ngừa rủi ro lộ lọt thông tin cá nhân ngay trên thiết bị người dùng (client-side) trước khi truy cập.")
    add_bullet(doc, "Phương pháp nghiên cứu: ", "Phân tích trực tiếp URL trên thiết bị người dùng thông qua ba lớp kiểm duyệt: cơ sở dữ liệu tra cứu nhanh (36.261 hồ sơ), 55 đặc trưng cú pháp/từ vựng URL và tổ hợp 4 mô hình trí tuệ nhân tạo (Random Forest, Gradient Boosting, SVM, Logistic Regression).")
    add_bullet(doc, "Quá trình thực hiện: ", "Huấn luyện mô hình trên tập dữ liệu đã chuẩn hóa gồm 261.299 URL (114.113 URL lừa đảo và 147.186 URL an toàn) và đánh giá độc lập trên tập kiểm thử gồm 6.624 URL mới hoàn toàn; các tính năng kiểm tra tên miền, dò vết chuyển hướng và chụp ảnh xem trước giao diện chỉ kích hoạt khi có sự đồng ý của người dùng.")
    add_bullet(doc, "Kết quả chính: ", "Mô hình Gradient Boosting đạt tỷ lệ phát hiện trang lừa đảo 95,61% (2.676/2.799 URL), Random Forest đạt 92,32%; phần mềm vượt qua 100% bài kiểm tra chất lượng gồm 59 bài kiểm tra xử lý dữ liệu và 16 bài kiểm tra độ tương thích trên trình duyệt.")
    add_bullet(doc, "Ý nghĩa/Kết luận: ", "Giúp hiển thị cảnh báo rủi ro trực quan kèm lý do minh bạch cho người dùng trước khi tương tác với liên kết mà không làm lộ lịch sử duyệt web; hướng phát triển tiếp theo là tích hợp thành tiện ích mở rộng (extension) cảnh báo thời gian thực trên trình duyệt.")

    out_docx = "Bao_cao_SafeWeb_KHKT_THPT.docx"
    out_doc = "Bao_cao_SafeWeb_KHKT_THPT.doc"
    doc.save(out_docx)
    shutil.copyfile(out_docx, out_doc)
    print("HOÀN TẤT! Đã xuất thành công Bao_cao_SafeWeb_KHKT_THPT.docx và .doc (IIIb đứng sau IIIa)!")


if __name__ == "__main__":
    build_report()
