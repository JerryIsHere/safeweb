# SafeWeb v2.3.0

SafeWeb là công cụ nghiên cứu hỗ trợ nhận diện URL có dấu hiệu lừa đảo. Bản 2.3.0 kết hợp tra cứu trực tiếp PhishVN, bốn mô hình ML chạy cục bộ trên trình duyệt, khám phá dữ liệu tương tác, phân loại URL và các kiểm tra web tùy chọn. Kết quả là tín hiệu tham khảo, không phải chứng nhận một website an toàn hay độc hại.

## Tính năng

- **Đồng thuận bốn mô hình:** Random Forest, Gradient Boosting, SVM tuyến tính hiệu chuẩn và Logistic Regression chạy cục bộ; từng xác suất và kết luận được hiển thị cạnh trung bình tổ hợp.
- **Kết luận PhishVN trực tiếp:** khớp URL chính xác trả về nhãn và metadata gốc; các điểm ML vẫn được giữ riêng để đối chiếu.
- **Khám phá PhishVN:** tìm kiếm URL, lọc nhãn/category/tier, phân trang và gửi URL đã chọn tới máy quét.
- **Thông tin URL:** nhận diện danh mục, nền tảng hosting và thương hiệu liên quan theo luật xác định.
- **Tự hoàn thiện URL:** thêm `https://` cho tên miền thiếu giao thức; với từ đơn như `vietcombank`, thử `https://vietcombank.com`. URL được chuẩn hóa hiển thị trước khi đánh giá.
- **Kiểm tra trực tuyến có đồng ý:** mặc định URL chỉ được phân tích cục bộ. Khi bật phạm vi kiểm tra trực tuyến, SafeWeb truy vấn Google DNS-over-HTTPS và dịch vụ Microlink; nếu ảnh chụp không khả dụng, dùng WordPress mShots. Các dịch vụ này nhận URL và có thể truy cập trang đích.
- **DNS và đích chuyển hướng:** hiển thị bản ghi A/AAAA/MX/NS/CNAME, nhận diện URL lồng trong tham số chuyển hướng và đánh giá URL đích. Trình duyệt có thể chặn việc đọc redirect HTTP trực tiếp do CORS; trường hợp đó không được tuyên bố là đã theo dõi đầy đủ.
- **Thông tin trang và ảnh xem trước:** hiển thị tiêu đề, mô tả, tác giả/công cụ tạo trang nếu dịch vụ trả về, kèm ảnh xem trước có trạng thái tải và lỗi.
- **Giao diện:** tiếng Việt/Anh cùng các bản dịch Pháp/Đức, ba chế độ tương phản, bảng tiêu chí có trạng thái rõ ràng và tiến trình kiểm tra.

## Phạm vi và quyền riêng tư

Chế độ cục bộ không gửi URL đi đâu: nó sử dụng đặc trưng URL, chỉ mục PhishVN và mô hình được đóng gói trong trang. Các truy vấn DNS, metadata và ảnh chụp chỉ chạy sau khi người dùng chủ động bật tùy chọn kiểm tra trực tuyến. URL khi đó được chia sẻ với nhà cung cấp DNS/xem trước bên thứ ba. Tắt tùy chọn để giữ phân tích hoàn toàn cục bộ.

HTTPS chỉ phản ánh giao thức trong URL; SafeWeb không xác thực chứng thư TLS từ trình duyệt. Kết quả DNS, metadata, screenshot và redirect có thể không khả dụng do CORS, giới hạn dịch vụ hoặc website ngoại tuyến. Không nhập URL riêng tư, token hoặc thông tin đăng nhập.

## Dữ liệu PhishVN

Pipeline huấn luyện kết hợp hai nguồn độc lập: PhishVN v3.1.0 từ `data/raw/PhishVN A Time-Stamped Vietnamese URL Phishing Dat.zip` và PhiUSIIL từ `data/raw/phiusiil+phishing+url+dataset.zip`. Archive PhiUSIIL được giữ nguyên cho công việc khác; script chỉ đọc cột URL và nhãn. Nhãn PhiUSIIL được đảo về quy ước SafeWeb (`1 = phishing`). Sau chuẩn hóa scheme-independent, 86 dòng thuộc URL xung đột nhãn và 3.586 dòng trùng được loại; 461 dòng thuộc các domain PhishVN test bị loại để giữ domain-disjoint. Còn 231.662 URL PhiUSIIL để huấn luyện. PhishVN có 53.116 dòng gốc, nhãn phishing/benign, nguồn, tier, ngày ghi nhận, thời điểm thu thập, phân vùng và bảng CompPhish 21 đặc trưng. Test PhishVN chính thức tiếp tục giữ riêng 6.624 dòng.

Quy trình PhishVN giữ 36.261 URL duy nhất sau khi gộp alias `www`/apex: 25.185 train, 4.452 validation và 6.624 test; nhãn gồm 19.909 phishing và 16.352 benign. Bốn mô hình fit trên 29.637 dòng PhishVN train+validation cùng 231.662 dòng PhiUSIIL (tổng 261.299). Mỗi nguồn nhận tổng trọng số bằng nhau và hai lớp được cân bằng bên trong từng nguồn; 6.624 PhishVN test giữ ngoài huấn luyện. Đặc trưng nguồn PhishVN khớp với 797.742 giá trị gốc; ba tín hiệu URL PhiUSIIL bổ sung là cờ obfuscation, số ký tự `%xx` được mã hóa và tỷ lệ của chúng trên URL. `scraped_at` và `collected_at` chỉ dùng truy xuất nguồn gốc.

`data/raw/urls.csv` và các CSV 5.000 dòng cũ là dữ liệu tương thích/nghiên cứu trước đây, không phải nguồn huấn luyện production. Archive gốc không bị chỉnh sửa. Dữ liệu đã chuẩn hóa được tạo trong `data/processed/` (được gitignore); chỉ mục tra cứu và bundle hồ sơ PhishVN được xuất vào `data/phishvn_database.json`, `web/static/model-data.js` và `web/static/database-records.json`.

**Trích dẫn và giấy phép:** Thai Nguyen Vu, *PhishVN: A Time-Stamped Vietnamese URL Phishing Dataset with Impersonation-Scenario Labels and Confidence Tiers*, phiên bản 3.1.0 (2026), DOI [10.17632/b97hxbxtpd.4](https://doi.org/10.17632/b97hxbxtpd.4), giấy phép [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). SafeWeb đã chuẩn hóa URL, gộp bí danh `www`/apex và tạo chỉ mục chữ ký từ dữ liệu được cấp phép. URL phishing lấy từ nguồn NCSC Tin Nhiem Mang và các feed/cộng đồng được nêu trong datasheet PhishVN; nhãn nguồn/tier được giữ trong dữ liệu sạch.

## Mô hình và đánh giá

Tất cả mô hình dùng chung 55 đặc trưng: 30 đặc trưng URL SafeWeb, 22 đặc trưng PhishVN và 3 tín hiệu URL PhiUSIIL. Chúng dùng cùng tập PhishVN test domain-disjoint (6.624 URL). Precision, recall và F1 đo lớp phishing; confusion matrix theo thứ tự `[benign, phishing]`. Trọng số huấn luyện cân bằng đóng góp hai nguồn.

Kết quả trên 6.624 URL test:

| Mô hình | Accuracy | Precision | Recall | F1 | ROC-AUC | TN / FP / FN / TP |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Random Forest | 0,8745 | 0,8075 | 0,9232 | 0,8615 | 0,9426 | 3209 / 616 / 215 / 2584 |
| Gradient Boosting | 0,8789 | 0,7976 | 0,9561 | 0,8697 | 0,9436 | 3146 / 679 / 123 / 2676 |
| SVM tuyến tính hiệu chuẩn | 0,5805 | 1,0000 | 0,0071 | 0,0142 | 0,9308 | 3825 / 0 / 2779 / 20 |
| Logistic Regression | 0,8555 | 0,7996 | 0,8782 | 0,8371 | 0,9330 | 3209 / 616 / 341 / 2458 |

SVM có ROC-AUC cao nhưng ngưỡng phân loại mặc định gần như bỏ sót toàn bộ phishing (recall 0,0071); không nên diễn giải xác suất/nhãn SVM hiện tại như kết quả hữu dụng trước khi hiệu chỉnh thêm. Các chỉ số còn lại cũng chỉ mô tả tập test này, không phải ước lượng hiệu năng ngoài thực tế. Tra cứu database là tầng riêng, không nằm trong các chỉ số ML.

## Kiến trúc

```text
PhishVN archive
  -> scripts/prepare_phishvn_dataset.py
  -> data/processed/phishvn_clean.csv + data/phishvn_database.json
  -> scripts/train_phishvn_model.py
  -> model/{random_forest,gradient_boosting,svm,logistic_regression}.joblib
  -> scripts/export_browser_model.py
  -> web/static/model-data.js + web/static/database-records.json
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
