# Lab 14 — S3 public exposure: detect, contain, fix

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D4 Security 16% |
| Thời gian | ~150 phút |
| Cần app stack | Không |
| Chi phí | Thấp |
| Lab ID | `14` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học cách phát hiện và đóng bucket S3 bị public: Block Public Access, bucket policy, ACL, Access Analyzer.
- **Việc đầu tiên:** Ô **Search** → `S3` → **Buckets** → search `soa-c03-lab14` → bấm bucket.
- **Xong khi:** `verify 14` PASS: BPA on, policy không public, anonymous nhận 403.
- **Nếu lạc:** `./bin/lab console 14` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học cách phát hiện và đóng bucket S3 bị public: Block Public Access, bucket policy, ACL, Access Analyzer.

## 2. Hiện tại có gì?

Core stack đủ. Lab tạo bucket `soa-c03-lab14-<account>`, object `secret.txt`, BPA bật, Access Analyzer.

## 3. Kiến trúc

```text
Internet
   │
   ▼
S3 bucket (BPA + bucket policy)
   ├── object secret.txt
   └── Access Analyzer finding
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Chỉ cần core stack; không cần app stack.

- Đọc `labs/14-*/README.md` (file này) và dòng lab `14` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 14
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 14
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 14
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 14
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 14
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 14
   ```


<!-- console-guide:start -->
## 5c. Console — bấm ở đâu, thấy gì

> **Trước khi bấm:** mở https://console.aws.amazon.com/ và đăng nhập **đúng account lab**
> (không dùng account cá nhân). Kiểm tra region góc trên phải là **Singapore (ap-southeast-1)**.
> Console AWS dùng tiếng Anh; nhãn trong bài là nhãn tiếng Anh.
> **Đường bấm** là nguồn chính; **link nhanh** chỉ là shortcut và có thể đổi khi AWS cập nhật giao diện.
> **Cách AI dạy:** mỗi lượt chỉ một màn hình và một nút. Bạn bấm xong, mô tả bạn thấy gì;
> AI mới đi tiếp. Đừng làm cả danh sách bước một lúc.
> Nhãn tiếng Anh khó hiểu? Tra bảng nút ở [`docs/console-guide.md`](../../docs/console-guide.md) mục 2e.

### Từ vựng nhanh (đọc trước)

| Thuật ngữ | Nghĩa đời thường |
|---|---|
| Block Public Access | 4 công tắc chặn public ở mức bucket/account. |
| Bucket policy | JSON policy gắn vào bucket. |
| ACL | Quyền kiểu cũ, thường nên tắt. |
| Access Analyzer | Dịch vụ tìm resource cho phép truy cập ngoài. |
| Anonymous access | Truy cập không có credential, ví dụ curl không ký. |

### Khái niệm của lab này

- Bucket S3 có **ba lớp** bảo vệ: **Block Public Access** (công tắc tổng), **bucket policy** (luật tài nguyên), và **ACL** (quyền cũ).
- **Access Analyzer** tìm cấu hình cho phép truy cập ngoài account.
- Một bucket có thể private theo BPA nhưng policy vẫn public nếu BPA bị tắt.

### Đường bấm từng bước

1. Ô **Search** → `S3` → **Buckets** → search `soa-c03-lab14` → bấm bucket.
2. Tab **Permissions** → mục **Block public access (bucket settings)** → **Edit** → đọc 4 cờ.
3. Cùng tab → **Bucket policy** → **Edit** → tìm `"Principal": "*"` hoặc `"AWS": "*"`.
4. Cùng tab → **Access control list (ACL)** → xem grant cho `AllUsers`/`AuthenticatedUsers`.
5. Ô **Search** → `Access Analyzer` → **Access Analyzer** → analyzer `soa-c03-lab14` → tab **Findings**.
6. Terminal: `curl -I https://<bucket>.s3.ap-southeast-1.amazonaws.com/secret.txt` (không kèm credential).

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| 4 cờ BPA | Phải cùng `On`; thiếu `BlockPublicPolicy` là policy public vẫn có hiệu lực. |
| Policy Principal | `*` nghĩa là bất kỳ ai. |
| Policy status | `IsPublic = true` là bằng chứng bucket đang public. |
| ACL grants | `AllUsers` = public; `AuthenticatedUsers` = mọi AWS account. |
| Finding status | `Active` nghĩa là đường public đang mở. |
| HTTP code | `200` là public; `403` là đã chặn. |

### Link nhanh

- [S3 buckets](https://console.aws.amazon.com/s3/buckets?region=ap-southeast-1)
- [Access Analyzer](https://console.aws.amazon.com/access-analyzer/home?region=ap-southeast-1#/analyzer)

### Nếu không thấy mục đó

- Không thấy bucket: search theo prefix `soa-c03-lab14`; tên bucket có account ID.
- BPA `On` nhưng vẫn public: kiểm tra policy; BPA không tự xoá policy.
- curl trả 403 ngay cả trước khi sửa: có thể bucket ở region khác hoặc object key sai.
- Access Analyzer cần vài phút mới có finding; đừng kết luận vội.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học phát hiện và đóng bucket S3 public: Block Public Access, bucket policy, ACL, Access Analyzer.

### Bạn cần biết 4 khái niệm

- **Block Public Access**: 4 công tắc chặn public.
- **Bucket policy**: JSON policy gắn vào bucket.
- **ACL**: Quyền kiểu cũ, thường nên tắt.
- **Access Analyzer**: Tìm resource cho phép truy cập ngoài.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Bucket | soa-c03-lab14-account | 4 cờ BPA bật | S3 → Buckets → Permissions |
| Object | secret.txt | tồn tại | S3 → bucket |
| Analyzer | soa-c03-lab14 | Active | Access Analyzer |
| Anonymous | object URL | 403 | curl không credential |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| BPA đủ 4 cờ? | S3 → Permissions | BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy, RestrictPublicBuckets |
| Policy public? | S3 → Bucket policy | Principal * |
| ACL public? | S3 → ACL | AllUsers, AuthenticatedUsers |
| Analyzer finding? | Access Analyzer → Findings | status |
| Anonymous? | curl object URL | 200 hay 403 |

### Trước khi phá, bạn phải trả lời 3 câu

1. Ba lớp bảo vệ bucket là gì?
2. BPA bật có tự xoá bucket policy không?
3. Anonymous 403 chứng minh điều gì?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 14 --live` và `./bin/lab teach 14`.

## 6. Hiện tượng bạn sẽ thấy

Bucket bị mở public. Bạn phải chứng minh nó public, rồi đóng lại mà vẫn giữ object.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| BPA có bật đủ 4 cờ? | `aws s3api get-public-access-block` |
| Bucket policy có public không? | `get-bucket-policy-status` |
| ACL có public không? | `get-bucket-acl` |
| Anonymous truy cập được không? | `curl -I https://<bucket>.s3.<region>.amazonaws.com/secret.txt` |

## 8. Thành công trông như thế nào?

`verify 14` PASS: BPA on, policy không public, anonymous nhận 403.

Nếu FAIL, đọc:

```bash
cat labs/14-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- BPA vs bucket policy vs ACL: ba lớp khác nhau.
- Access Analyzer tìm public/cross-account access.
- Public object có thể bị cache; đóng bucket trước, kiểm tra lại.

## 10. Note mẫu

- 1. Public qua đường nào?
- 2. BPA có che được bucket policy không?
- 3. Anonymous 200 hay 403 chứng minh gì?

## 11. Cleanup

```bash
./bin/lab down 14
make cost
```

Nếu hết buổi:

```bash
make app-down
make inventory
make cost
```

- Lab 00 không có resource riêng; core stack được giữ lại cho các lab sau.

## 12. Nếu bí

```bash
./bin/lab hint 14
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 14. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
