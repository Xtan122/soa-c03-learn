# Lab 21 — Incident: DB timeout + AccessDenied

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D2/D4 |
| Thời gian | ~180 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Thấp |
| Lab ID | `21` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Incident kết hợp data path và identity path: app không vào được DB, đồng thời role bị deny secret. Bạn phải sửa cả hai lớp.
- **Việc đầu tiên:** Ô **Search** → `EC2` → **Security groups** → SG DB (`soa-c03-db-...`) → **Inbound rules**: TCP 5432 từ SG app.
- **Xong khi:** `verify 21` PASS: DB SG allow 5432, không còn deny policy, `/db` 200, secret đọc được.
- **Nếu lạc:** `./bin/lab console 21` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Incident kết hợp data path và identity path: app không vào được DB, đồng thời role bị deny secret. Bạn phải sửa cả hai lớp.

## 2. Hiện tại có gì?

App stack chạy. `break 21` chặn DB SG 5432 và gắn explicit deny `secretsmanager:GetSecretValue` cho app role.

## 3. Kiến trúc

```text
App → DB SG (5432 bị chặn) → RDS
  │
  └── Secrets Manager (bị deny)
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/21-*/README.md` (file này) và dòng lab `21` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 21
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 21
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 21
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 21
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 21
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 21
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
| DB timeout | Kết nối TCP không thành công hoặc quá chậm. |
| AccessDenied | Lỗi quyền, không phải lỗi mạng. |
| Explicit deny | Câu Deny thắng mọi Allow. |
| Secret | Chuỗi bí mật lưu trong Secrets Manager. |
| App role | Role gắn vào EC2 app qua instance profile. |

### Khái niệm của lab này

- Hai đường hỏng độc lập: **data path** (app → SG → RDS) và **identity path** (app role → Secrets Manager).
- DB timeout thường do SG/NACL/route/DNS; `AccessDenied` thường do identity/resource policy, KMS, hoặc explicit deny.
- Phải chứng minh từng đường bằng một evidence riêng.

### Đường bấm từng bước

1. Ô **Search** → `EC2` → **Security groups** → SG DB (`soa-c03-db-...`) → **Inbound rules**: TCP 5432 từ SG app.
2. Ô **Search** → `IAM` → **Roles** → role app (lấy tên từ CloudFormation Outputs `AppInstanceRoleName`) → tab **Permissions** → tìm inline `lab21-deny-secret`.
3. Ô **Search** → `Secrets Manager` → secret DB (Output `DbSecretArn`) → **Overview**; thử **Retrieve secret value**.
4. **CloudWatch** → **Logs Insights** → log app → filter `db_check_failed` hoặc `AccessDenied`.
5. Terminal: `curl -i http://<alb>/db`.
6. **Systems Manager** → **Run Command** → `aws secretsmanager get-secret-value ...` để tách lỗi quyền khỏi app.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| SG 5432 | Thiếu rule là DB timeout ngay. |
| Inline policy name | `lab21-deny-secret` là deny chủ động, không phải policy thiếu. |
| Secret retrieve | Nếu console đọc được mà app không, so role của bạn với role app. |
| Log error | `timeout` vs `AccessDenied` cho biết đường nào hỏng. |
| `/db` code | 200 chỉ khi cả SG và secret đều đúng. |
| CloudTrail | `GetSecretValue` + `errorCode` là bằng chứng quyền. |

### Link nhanh

- [Security groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#SecurityGroups:)
- [IAM roles](https://console.aws.amazon.com/iam/home#/roles)
- [Secrets Manager](https://console.aws.amazon.com/secretsmanager/landing?region=ap-southeast-1)
- [Logs Insights](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#logsV2:logs-insights)

### Nếu không thấy mục đó

- Sửa SG xong vẫn timeout: kiểm tra NACL outbound ephemeral ports.
- Secret đọc được nhưng app vẫn lỗi: app có thể cache secret cũ; restart service qua SSM.
- IAM policy thay đổi có thể mất vài giây; thử lại.
- Đừng sửa cả hai lớp cùng lúc; mỗi lần một thay đổi rồi verify.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Incident data + identity: DB timeout và AccessDenied. Sửa cả hai lớp.

### Bạn cần biết 4 khái niệm

- **DB timeout**: Kết nối TCP không thành công hoặc quá chậm.
- **AccessDenied**: Lỗi quyền, không phải lỗi mạng.
- **Explicit deny**: Câu Deny thắng mọi Allow.
- **App role**: Role gắn vào EC2 qua instance profile.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| RDS | soa-c03-db | available | RDS → Databases |
| DB SG | soa-c03-db-... | cho 5432 từ app SG | EC2 → Security groups |
| App role | AppInstanceRoleName | không có deny lab21 | IAM → Roles |
| Secret | DbSecretArn | đọc được | Secrets Manager |
| App | soa-c03-app | /db 200 | ./bin/lab status |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| DB SG? | Security groups → Inbound | 5432 từ app SG |
| Secret bị deny? | IAM → Role → Permissions | inline lab21-deny-secret |
| Secret đọc được? | Secrets Manager / CLI | GetSecretValue |
| Log nói gì? | Logs Insights | timeout, AccessDenied |
| /db? | curl /db | HTTP status |

### Trước khi phá, bạn phải trả lời 3 câu

1. DB timeout khác AccessDenied ở đâu?
2. Hai lỗi này có cùng root cause không?
3. Bạn sửa mạng hay quyền trước? Vì sao?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 21 --live` và `./bin/lab teach 21`.

## 6. Hiện tượng bạn sẽ thấy

`/db` trả 503/timeout; log app báo không lấy được secret hoặc không kết nối DB.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| DB SG có cho app SG vào 5432? | EC2 → Security Groups → DB SG |
| Secret có đọc được không? | `aws secretsmanager get-secret-value` |
| Role có explicit deny không? | IAM → Role → Permissions |
| App log nói gì? | Logs Insights `db_check_failed` |

## 8. Thành công trông như thế nào?

`verify 21` PASS: DB SG allow 5432, không còn deny policy, `/db` 200, secret đọc được.

Nếu FAIL, đọc:

```bash
cat labs/21-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- DB timeout: SG, NACL, route, DNS, max connections.
- AccessDenied: identity/resource/KMS/SCP/boundary.
- Hai triệu chứng có thể cùng root cause hoặc hai lỗi độc lập.

## 10. Note mẫu

- 1. DB timeout hay auth error?
- 2. Secret bị chặn ở đâu?
- 3. Sửa mạng hay sửa quyền trước?

## 11. Cleanup

```bash
./bin/lab down 21
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
./bin/lab hint 21
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 21. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
