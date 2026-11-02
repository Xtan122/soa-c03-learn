# Lab 10 — Secrets Manager + KMS: có quyền S3 vẫn AccessDenied

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D4 Security 16% |
| Thời gian | ~150 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Thấp |
| Lab ID | `10` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học lỗi "có quyền S3 nhưng vẫn AccessDenied" vì object mã hoá KMS. Đây là bẫy rất hay gặp trong đề và thực tế.
- **Việc đầu tiên:** Ô **Search** → `Secrets Manager` → **Secrets** → bấm `/soa-c03/lab10/api-key`.
- **Xong khi:** `verify 10` PASS: role `soa-c03-lab10-reader` đọc được object và secret.
- **Nếu lạc:** `./bin/lab console 10` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học lỗi "có quyền S3 nhưng vẫn AccessDenied" vì object mã hoá KMS. Đây là bẫy rất hay gặp trong đề và thực tế.

## 2. Hiện tại có gì?

App stack + core KMS. Lab tạo secret, một object S3 mã hoá KMS, và role `soa-c03-lab10-reader` có quyền S3/Secret nhưng chưa có KMS.

## 3. Kiến trúc

```text
Reader role
   ├── s3:GetObject ──► S3 object (SSE-KMS)
   ├── secretsmanager:GetSecretValue ──► Secret
   └── kms:Decrypt?  ← thiếu hoặc bị deny
                         │
                         ▼
                     KMS key policy
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/10-*/README.md` (file này) và dòng lab `10` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 10
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 10
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 10
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 10
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 10
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 10
   ```

## 5b. Ghi chú / lệnh riêng

Lab này cần quyền `sts:AssumeRole` cho user của bạn. Nếu AssumeRole fail, đó là lab 13.

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
| SSE-KMS | S3 mã hoá object bằng một key KMS. |
| Key policy | Ai được dùng key, gắn trực tiếp vào key. |
| IAM policy | Role/user được phép gọi action nào. |
| Explicit deny | Câu `Deny` luôn thắng `Allow`. |
| AssumeRole | Mượn danh tính tạm thời của một role. |

### Khái niệm của lab này

- Object S3 mã hoá **SSE-KMS** cần **hai** lần cho phép: quyền `s3:GetObject` trên object **và** quyền `kms:Decrypt` trên key.
- **Key policy** là resource policy của key; **explicit deny** trong key policy hoặc IAM thắng mọi allow.
- Secrets Manager cũng dùng KMS key riêng.

### Đường bấm từng bước

1. Ô **Search** → `Secrets Manager` → **Secrets** → bấm `/soa-c03/lab10/api-key`.
2. Tab **Overview**: xem **Secret ARN**, **Encryption key**, **Last retrieved**.
3. Ô **Search** → `KMS` → **Customer managed keys** → bấm alias `alias/soa-c03-lab`.
4. Tab **Key policy**: bấm **Switch to policy view** (nếu đang ở dạng editor) → tìm các `Sid` có `Lab10Reader` / `Lab10Deny`.
5. Tab **Key overview**: **Key state** phải **Enabled**; xem **Key ARN**.
6. Ô **Search** → `IAM` → **Roles** → `soa-c03-lab10-reader` → tab **Permissions** → bấm policy `lab10-read`.
7. Ô **Search** → `S3` → bucket core (Outputs) → thư mục `lab10/` → bấm `secret.txt` → tab **Properties** → **Server-side encryption**.
8. Ô **Search** → `CloudTrail` → **Event history** → filter **Event name** = `Decrypt` hoặc `GetSecretValue` → xem `errorCode`.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Encryption key | Object/secret đang dùng key nào; phải là key bạn đang sửa policy. |
| Key policy statements | Có `Allow` cho role reader và có `Deny` chen vào không. |
| IAM policy actions | Có `s3:GetObject` và `secretsmanager:GetSecretValue` chưa. |
| Object encryption | `AWS KMS` + key ARN, không phải `SSE-S3`. |
| CloudTrail errorCode | `AccessDenied` kèm message nói thiếu quyền gì. |
| Key state | Key bị disable/delete thì mọi thứ fail. |

### Link nhanh

- [Secrets Manager](https://console.aws.amazon.com/secretsmanager/landing?region=ap-southeast-1)
- [KMS keys](https://console.aws.amazon.com/kms/home?region=ap-southeast-1#/kms/keys)
- [IAM roles](https://console.aws.amazon.com/iam/home#/roles)
- [S3 buckets](https://console.aws.amazon.com/s3/buckets?region=ap-southeast-1)
- [CloudTrail events](https://console.aws.amazon.com/cloudtrail/home?region=ap-southeast-1#/events)

### Nếu không thấy mục đó

- Sửa key policy xong vẫn lỗi: policy có thể mất vài giây để áp dụng; thử lại.
- Không thấy statement lab: `up 10` chưa chạy hoặc `down 10` đã dọn.
- Đừng sửa IAM policy nếu lỗi là `kms:Decrypt`; đọc message trong CloudTrail trước.
- Nếu bạn không có quyền `sts:AssumeRole`, lab này sẽ fail ở bước assume; đó là quyền của user, không phải lỗi lab.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học lỗi có quyền S3 nhưng vẫn AccessDenied vì object mã hoá KMS; key policy và explicit deny.

### Bạn cần biết 4 khái niệm

- **SSE-KMS**: S3 mã hoá object bằng key KMS.
- **Key policy**: Ai được dùng key, gắn trực tiếp vào key.
- **Explicit deny**: Câu Deny luôn thắng Allow.
- **AssumeRole**: Mượn danh tính tạm thời của role.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Secret | /soa-c03/lab10/api-key | tồn tại | Secrets Manager |
| KMS key | alias/soa-c03-lab | Enabled | KMS → Customer managed keys |
| Reader role | soa-c03-lab10-reader | có policy S3 + secret | IAM → Roles |
| S3 object | lab10/secret.txt | SSE-KMS | S3 → bucket → Properties |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Secret đọc được? | Secrets Manager → Retrieve | AccessDenied? |
| Key policy? | KMS → Key policy | Allow/Deny cho reader |
| Role có quyền gì? | IAM → Permissions | s3:GetObject, GetSecretValue |
| Object mã hoá gì? | S3 → Properties | SSE-KMS, key ARN |
| Lỗi ở đâu? | CloudTrail | errorCode, eventName |

### Trước khi phá, bạn phải trả lời 3 câu

1. Có quyền S3 đã đủ đọc object SSE-KMS chưa?
2. Explicit deny nằm ở đâu?
3. Bạn sửa IAM hay key policy trước? Vì sao?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 10 --live` và `./bin/lab teach 10`.

## 6. Hiện tượng bạn sẽ thấy

Role đọc S3 bị `AccessDenied` dù policy S3 đúng; secret cũng có thể bị chặn.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Role có quyền S3 không? | IAM role policy |
| Object dùng KMS key nào? | S3 object → Properties → Encryption |
| Key policy cho role chưa? | KMS → Key policy |
| Có explicit deny không? | Key policy + IAM policy |

## 8. Thành công trông như thế nào?

`verify 10` PASS: role `soa-c03-lab10-reader` đọc được object và secret.

Nếu FAIL, đọc:

```bash
cat labs/10-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- IAM cho S3 không đủ nếu object SSE-KMS.
- Key policy + IAM policy + resource policy; explicit deny thắng.
- Secrets Manager secret cũng có resource policy/KMS.

## 10. Note mẫu

- 1. AccessDenied ở API nào?
- 2. Thiếu `kms:Decrypt` hay bị deny?
- 3. Sửa IAM hay key policy?

## 11. Cleanup

```bash
./bin/lab down 10
make cost
```

Nếu hết buổi:

```bash
make app-down
make inventory
make cost
```

- Lab này có resource riêng; `down` sẽ dọn. Nếu đã dùng `reset`, ghi `SOLUTION_USED: yes` vào note.

## 12. Nếu bí

```bash
./bin/lab hint 10
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 10. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
