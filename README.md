# SafeWeb v2.1.0

SafeWeb là công cụ nghiên cứu hỗ trợ nhận diện URL có dấu hiệu lừa đảo. Bản 2.1.0 kết hợp tra cứu dữ liệu PhishVN, Random Forest chạy cục bộ trên trình duyệt và các kiểm tra web tùy chọn. Kết quả là tín hiệu tham khảo, không phải chứng nhận một website an toàn hay độc hại.

## Tính năng

- **Xác minh hai tầng:** đối chiếu URL, máy chủ và chữ ký đặc trưng với chỉ mục PhishVN; sau đó luôn chạy Random Forest để đánh giá mẫu rủi ro. Kết quả hiển thị nguồn khớp dữ liệu và trạng thái mô hình.
- **Tự hoàn thiện URL:** thêm `https://` cho tên miền thiếu giao thức; với từ đơn như `vietcombank`, thử `https://vietcombank.com`. URL được chuẩn hóa hiển thị trước khi đánh giá.
- **Kiểm tra trực tuyến có đồng ý:** mặc định URL chỉ được phân tích cục bộ. Khi bật phạm vi kiểm tra trực tuyến, SafeWeb truy vấn Google DNS-over-HTTPS và dịch vụ Microlink; nếu ảnh chụp không khả dụng, dùng WordPress mShots. Các dịch vụ này nhận URL và có thể truy cập trang đích.
- **DNS và đích chuyển hướng:** hiển thị bản ghi A/AAAA/MX/NS/CNAME, nhận diện URL lồng trong tham số chuyển hướng và đánh giá URL đích. Trình duyệt có thể chặn việc đọc redirect HTTP trực tiếp do CORS; trường hợp đó không được tuyên bố là đã theo dõi đầy đủ.
- **Thông tin trang và ảnh xem trước:** hiển thị tiêu đề, mô tả, tác giả/công cụ tạo trang nếu dịch vụ trả về, kèm ảnh xem trước có trạng thái tải và lỗi.
- **Giao diện:** tiếng Việt/Anh cùng các bản dịch Pháp/Đức, ba chế độ tương phản, bảng tiêu chí có trạng thái rõ ràng và tiến trình kiểm tra.

## Phạm vi và quyền riêng tư

Chế độ cục bộ không gửi URL đi đâu: nó sử dụng đặc trưng URL, chỉ mục PhishVN và mô hình được đóng gói trong trang. Các truy vấn DNS, metadata và ảnh chụp chỉ chạy sau khi người dùng chủ động bật tùy chọn kiểm tra trực tuyến. URL khi đó được chia sẻ với nhà cung cấp DNS/xem trước bên thứ ba. Tắt tùy chọn để giữ phân tích hoàn toàn cục bộ.

HTTPS chỉ phản ánh giao thức trong URL; SafeWeb không xác thực chứng thư TLS từ trình duyệt. Kết quả DNS, metadata, screenshot và redirect có thể không khả dụng do CORS, giới hạn dịch vụ hoặc website ngoại tuyến. Không nhập URL riêng tư, token hoặc thông tin đăng nhập.

## Dữ liệu PhishVN

Nguồn chuẩn là archive `PhishVN A Time-Stamped Vietnamese URL Phishing Dat.zip`, bên trong chứa PhishVN v3.1.0 open release. Bộ dữ liệu có 53.116 dòng URL, nhãn phishing/benign, nguồn, mức tin cậy, ngày ghi nhận, thời điểm thu thập, phân vùng và bảng CompPhish 21 đặc trưng. Các phân vùng train/validation/test chính thức đã được nhóm theo tên miền đăng ký và có 0 giao nhau giữa các phân vùng.

Quy trình chuẩn hóa hiện tạo 36.261 URL duy nhất: loại 16.855 biến thể trùng `www`/apex, không ghi nhận nhóm URL mâu thuẫn nhãn hoặc URL lỗi/truncated. Kết quả giữ lại 25.185 dòng train, 4.452 validation và 6.624 test; nhãn gồm 19.909 phishing và 16.352 benign. Các đặc trưng nguồn được kiểm tra khớp trên toàn bộ mẫu đã làm sạch. `scraped_at` và `collected_at` được giữ lại để truy xuất nguồn gốc; không dùng thời điểm scrape làm nhãn.

`data/raw/urls.csv` và các CSV 5.000 dòng cũ là dữ liệu tương thích/nghiên cứu trước đây, không phải nguồn huấn luyện production cho v2.1.0. Archive gốc không bị chỉnh sửa. Dữ liệu đã chuẩn hóa được tạo trong `data/processed/` (được gitignore); chỉ mục tra cứu PhishVN được xuất vào `data/phishvn_database.json` và `web/static/model-data.js`.

**Trích dẫn và giấy phép:** Thai Nguyen Vu, *PhishVN: A Time-Stamped Vietnamese URL Phishing Dataset with Impersonation-Scenario Labels and Confidence Tiers*, phiên bản 3.1.0 (2026), DOI [10.17632/b97hxbxtpd.4](https://doi.org/10.17632/b97hxbxtpd.4), giấy phép [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). SafeWeb đã chuẩn hóa URL, gộp bí danh `www`/apex và tạo chỉ mục chữ ký từ dữ liệu được cấp phép. URL phishing lấy từ nguồn NCSC Tin Nhiem Mang và các feed/cộng đồng được nêu trong datasheet PhishVN; nhãn nguồn/tier được giữ trong dữ liệu sạch.

## Mô hình và đánh giá

Random Forest 100 cây, giới hạn độ sâu 16, dùng 52 đặc trưng: đặc trưng URL SafeWeb và 22 trường PhishVN (21 đặc trưng CompPhish cùng cờ TLD đáng ngờ). Huấn luyện bằng train + validation; test chính thức được giữ ngoài huấn luyện.

Kết quả trên 6.624 URL test:

| Chỉ số | Giá trị |
| --- | ---: |
| Accuracy | 0,8752 |
| Precision (phishing) | 0,8231 |
| Recall (phishing) | 0,8975 |
| F1 (phishing) | 0,8587 |

Đây là kết quả trên một tập dữ liệu cụ thể, không phải ước lượng hiệu năng ngoài thực tế hoặc mức độ tin cậy đã hiệu chuẩn. Tra cứu database là một tầng tham chiếu riêng, không được tính vào các chỉ số ML trên.

## Kiến trúc

```text
PhishVN archive
  -> scripts/prepare_phishvn_dataset.py
  -> data/processed/phishvn_clean.csv + data/phishvn_database.json
  -> scripts/train_phishvn_model.py
  -> model/random_forest.joblib
  -> scripts/export_browser_model.py
  -> web/static/model-data.js
  -> web/static/browser-model.js + web/static/script.js
```

`src/` chứa xác thực URL, trích xuất đặc trưng, nạp dữ liệu và dự đoán Python. `web/` chứa ứng dụng Flask dùng khi phát triển cùng giao diện tĩnh production. GitHub Pages chạy mô hình trình duyệt; không cần backend Flask để phân tích URL.

## Cài đặt và chạy

Yêu cầu Python 3.11 trở lên và Node.js 22 trở lên.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm install
npm run dev
```

Mở `http://127.0.0.1:5000`. Để mở bản production tĩnh cục bộ:

```bash
npm run build
python -m http.server 8000 --directory _site
```

## Chuẩn bị dữ liệu, huấn luyện và kiểm thử

```bash
source .venv/bin/activate
python scripts/prepare_phishvn_dataset.py
python scripts/train_phishvn_model.py
python scripts/export_browser_model.py
python scripts/compare_browser_model.py
python -m pytest -q
npm run test:browser
npm test
npm run build
```

`compare_browser_model.py` đối chiếu vector đặc trưng, xác suất và phân loại giữa Python và trình duyệt trên các trường hợp cố định. Tệp `model/random_forest.joblib` được tạo cục bộ; bundle cần cho Pages nằm trong `web/static/model-data.js`.

## Triển khai GitHub Pages

Workflow `.github/workflows/pages.yml` chỉ chạy khi push lên `main` (cũng hỗ trợ chạy thủ công). Nó chạy kiểm thử trình duyệt, build `_site`, kiểm tra đường dẫn tương đối và triển khai bằng GitHub Pages artifact/deploy actions. Trong GitHub, đặt **Settings → Pages → Build and deployment → Source** thành **GitHub Actions**.

Tài liệu đánh giá và bằng chứng được lưu tại `ML_EXPERIMENT_REPORT.md`, `REPORT_EVIDENCE.md` và `docs/project_report.md`.
