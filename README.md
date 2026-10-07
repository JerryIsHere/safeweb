
## Mẫu nghiên cứu SafeWeb

SafeWeb là một nguyên mẫu giáo dục ước tính liệu các đặc trưng của URL có giống các mẫu trong tập dữ liệu lừa đảo đã gán nhãn hay không. Nó chỉ phân tích văn bản URL: không mở URL được gửi lên, không theo redirect, không tải xuống tệp hoặc liên hệ với trang web. Kết quả là một đánh giá rủi ro theo thang 0–100, kết hợp xác suất mô hình và các tín hiệu URL có sẵn, không phải bằng chứng cho thấy một trang web an toàn hoặc độc hại.

### Mô hình rủi ro mới

SafeWeb hiện đánh giá rủi ro theo thang bốn mức rõ ràng:

- `LOW`: 0–24
- `CAUTION`: 25–49
- `HIGH`: 50–74
- `VERY HIGH`: 75–100

Mỗi kết quả đều đi kèm giải thích dựa trên các tín hiệu thực tế thu được từ URL: độ dài URL, số tầng subdomain, địa chỉ IP, ký tự đặc biệt, từ khóa như `login`, `verify`, `password`, `bank`, v.v., cùng với tín hiệu HTTPS/HTTP. Các thông tin như độ tuổi tên miền, danh sách đen, DNS, redirect hoặc nội dung trang web không được giả định nếu chưa có nguồn đáng tin cậy và tương thích với GitHub Pages.

Nếu thông tin không thể kiểm tra an toàn trong trình duyệt, hệ thống hiển thị `Not checked` hoặc `Not available` thay vì giả cách đã xác minh.

### Trạng thái mô hình

- **Mô hình production hiện hành:** Random Forest 200 cây trên 30 đặc trưng URL baseline.
- **Trạng thái:** Không thay đổi/không nâng cấp production model.
- **Mô hình thử nghiệm:** Có tính năng mở rộng 12 đặc trưng xác định được, nhưng chưa được triển khai. Dữ liệu hiện tại là tổng hợp và không đại diện cho dữ liệu phòng chống lừa đảo thực tế.
- **Kết luận:** Chọn **B. Improve dataset first**. Cần bộ dữ liệu đã ghi lại nguồn, ngày thu thập, quy tắc gán nhãn và phân tách domain/source trước khi xem xét thay đổi mô hình.
- **Điểm rủi ro:** Kết quả cuối cùng 0–100 là **Risk Score**, không phải mức độ tin cậy cân bằng hay độ chắc chắn ML.

### Thiết lập

Sử dụng Python 3.11 hoặc mới hơn, sau đó cài đặt các phụ thuộc từ thư mục gốc của kho mã:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Trên Windows, kích hoạt môi trường với `.venv\\Scripts\\activate`.

### Bộ dữ liệu và mô hình

`data/raw/urls.csv` là dữ liệu mô phỏng phát triển tổng hợp. Nó hữu ích cho việc thực thi quy trình huấn luyện và giao diện web, nhưng không phải là dữ liệu nghiên cứu và không thể xác lập hiệu suất phát hiện lừa đảo trong thế giới thực. Không trình bày các số liệu từ tệp này như kết quả thực tế hoặc kết luận nghiên cứu. Đối với nghiên cứu, hãy thay thế bằng bộ dữ liệu đã được ghi chép rõ ràng và lưu lại nguồn gốc, giấy phép, ngày thu thập và phương pháp gán nhãn.

CSV phải chứa các cột bắt buộc sau:

| Cột | Giá trị bắt buộc |
| --- | --- |
| `url` | Chuỗi URL không rỗng |
| `label` | `0` cho hợp pháp hoặc `1` cho lừa đảo |

Lệnh mặc định đọc `data/raw/urls.csv`, hoặc bạn có thể truyền đường dẫn CSV khác một cách rõ ràng. Quá trình huấn luyện kiểm tra các URL HTTP(S) và nhãn nhị phân, báo cáo các hàng không hợp lệ hoặc mâu thuẫn rõ ràng, loại bỏ các URL trùng chính xác, và huấn luyện Random Forest trên tập huấn luyện 80% có thể tái lập. Đánh giá tái tạo tập kiểm tra riêng 20% và ghi các số liệu, báo cáo phân loại, ma trận nhầm lẫn, độ quan trọng của đặc trưng và phân tích lỗi trong `reports/`. Bất kỳ số liệu nào được tạo từ dữ liệu demo tổng hợp đi kèm đều chỉ nhằm xác minh quy trình.

```bash
python -m src.train
python -m src.evaluate data/raw/urls.csv
```

### Phát triển cục bộ

```bash
python run.py
```

Ứng dụng Flask được giữ lại cho phát triển cục bộ và so sánh ở phía Python. Nó lộ ra `GET /health` và `POST /predict`; giao diện phía production trên GitHub Pages không gọi đến route nào trong số này. Giao diện trình duyệt trích xuất đặc trưng, chạy mô hình cục bộ và bổ sung một lớp đánh giá rủi ro theo quy tắc có thể giải thích. Giới hạn rủi ro của Python là 0.25 cho `CAUTION`, 0.50 cho `HIGH` và 0.75 cho `VERY HIGH`; có thể ghi đè bằng `SAFEWEB_LOW_THRESHOLD`, `SAFEWEB_MEDIUM_THRESHOLD` và `SAFEWEB_HIGH_THRESHOLD` khi sử dụng backend phát triển.

### Tính mô tả và hướng dẫn khuyến nghị

Kết quả không chỉ hiển thị `phishing` hay `legitimate`; nó hiển thị:

- Điểm rủi ro 0–100
- Mức rủi ro theo thang 4 mức
- Lý do khả quan sát được từ URL
- Danh sách tín hiệu càng sớm càng rõ
- Hướng dẫn action phù hợp với mức độ cảnh báo: không nhập mật khẩu, không cung cấp tài khoản/chứng từ, xác minh qua kênh chính thức, đóng tab nếu rủi ro cao.

Giao diện cũng đổi màu theo trạng thái rủi ro: an toàn, cảnh báo, nguy cơ cao, nguy hiểm rất cao. Điểm nhấn là không dựa hoàn toàn vào màu sắc; có nhãn văn bản và icon phụ trợ cho khả năng truy cập.

Mô hình trình duyệt được xuất từ tệp tin mô hình scikit-learn đã huấn luyện với:

```bash
python scripts/export_browser_model.py
python scripts/compare_browser_model.py
```

### Triển khai trên GitHub Pages

Workflow `pages.yml` xây dựng và triển khai ứng dụng tĩnh hoàn toàn trên các đẩy lên `main`. Trong cài đặt kho mã, hãy đặt **Pages → Build and deployment → Source** thành **GitHub Actions**. Các đường dẫn tài sản tương đối với trang hỗ trợ các URL dự án như `https://jerryishere.github.io/safeweb/`.

SafeWeb vẫn là ứng dụng client-side: không có localhost backend bắt buộc, không gửi URL ra ngoài, không cần Flask để phân tích trên GitHub Pages. Quy trình build tĩnh giữ nguyên và nội dung mô hình trình duyệt được tạo từ tệp mô hình Python đã huấn luyện.

`web/static/model-data.js` chứa các cây Random Forest đã xuất và các quy tắc public-suffix ngoại tuyến cần thiết cho trình duyệt. Nó được tạo từ mô hình đã huấn luyện thực tế; sau khi huấn luyện lại, hãy tạo lại và cam kết tệp mô hình trình duyệt. Một khi trang và tài sản tĩnh tải xong, phân tích URL không gửi bất kỳ yêu cầu mạng nào, không mở URL nào được gửi lên và không cần Python, Flask, dịch vụ Render hoặc API dự đoán.

Chạy kiểm thử trình duyệt với `npm run test:browser`, kiểm thử Python với `python -m pytest`, và kiểm tra tính đồng nhất trực tiếp của mô hình với `python scripts/compare_browser_model.py` khi có sẵn tệp mô hình Python cục bộ. Xem `docs/project_report.md`, `docs/poster_content.md` và `docs/presentation_outline.md` để xem tài liệu nghiên cứu với kết quả thí nghiệm được giữ lại như placeholders.

## Kiến trúc

```text
data/
	raw/          Dữ liệu demo phát triển tổng hợp; thay thế cho nghiên cứu
	processed/    Dữ liệu dẫn xuất có thể tái lập (được tạo; không được cam kết theo mặc định)
	sample/       Dành riêng cho các ví dụ phát triển được gán nhãn rõ ràng
model/          Tệp mô hình Python do cục bộ tạo ra (không triển khai)
reports/        Kết quả đánh giá do cục bộ tạo ra (không được đóng gói)
src/            Các mô-đun dữ liệu, phân tích URL, mô hình và giải thích
web/            Các route phát triển Flask, template dùng chung và ứng dụng/trình duyệt mô hình tĩnh
scripts/        Xây dựng site tĩnh, xuất mô hình trình duyệt và xác thực tính đồng nhất
tests/          Các kiểm thử hành vi tự động
config/         Thiết lập chung của dự án
docs/           Kế hoạch dự án và tài liệu hội nghị khoa học
```

## Quy trình dự kiến

Quy trình nghiên cứu dự kiến là xác thực một tập dữ liệu URL đã gán nhãn và được ghi chép rõ ràng, tiền xử lý và chia tách có thể tái lập, trích xuất các đặc trưng số của URL/miền, huấn luyện Random Forest trên dữ liệu huấn luyện, đánh giá một lần trên tập kiểm tra tách biệt, rồi hiển thị dự đoán, mức rủi ro và giải thích dựa trên tín hiệu thông qua giao diện Flask cục bộ. Web MVP chỉ phân tích chuỗi URL; nó không được truy cập trang web đã gửi hoặc theo redirect. Đầu ra của mô hình là đánh giá rủi ro, không phải bằng chứng cho thấy một trang web an toàn hoặc độc hại. Không thêm dữ liệu nghiên cứu hoặc báo cáo số liệu cho đến khi nguồn và thí nghiệm của chúng được ghi chép.