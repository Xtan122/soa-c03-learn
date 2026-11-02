# Lab 13 — IAM + STS AssumeRole: trust policy vs permissions

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D4 Security 16% |
| Thời gian | ~120 phút |
| Cần app stack | Không |
| Chi phí | Thấp |
| Lab ID | `13` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học lỗi AssumeRole: trust policy quyết định ai được assume; permission policy quyết định làm được gì. Đây là cặp bài trùng rất hay nhầm.
- **Việc đầu tiên:** Ô **Search** → `IAM` → **Roles** → bấm `soa-c03-lab13-target`.
- **Xong khi:** `verify 13` PASS: AssumeRole thành công, identity là role, `aws s3 ls` được.
- **Nếu lạc:** `./bin/lab console 13` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học lỗi AssumeRole: trust policy quyết định ai được assume; permission policy quyết định làm được gì. Đây là cặp bài trùng rất hay nhầm.

## 2. Hiện tại có gì?

Core stack đủ. Lab tạo role `soa-c03-lab13-target` tin cậy account của bạn và có quyền đọc S3.

## 3. Kiến trúc

```text
Bạn (IAM user)
   │ sts:AssumeRole
   ▼
Role soa-c03-lab13-target
   ├── Trust policy: ai được assume?
   └── Permission policy: được làm gì? (S3)
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Chỉ cần core stack; không cần app stack.

- Đọc `labs/13-*/README.md` (file này) và dòng lab `13` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 13
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 13
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 13
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 13
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 13
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 13
   ```

## 5b. Ghi chú / lệnh riêng

Nếu user của bạn không có `sts:AssumeRole`, lab này sẽ fail ở bước assume; đó là lỗi quyền của user, không phải lab.

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
| Trust policy | Danh sách principal được phép assume role. |
| Permission policy | Quyền của role sau khi được assume. |
| AssumeRole | Đổi sang danh tính tạm thời của role. |
| Session | Phiên assume, có thời hạn. |
| External ID | Chuỗi bí mật thêm vào trust để tránh confused deputy. |

### Khái niệm của lab này

- **Trust policy** trả lời “ai được assume role này”; **permission policy** trả lời “sau khi assume thì làm được gì”.
- `AssumeRole` lỗi vì trust policy sai không liên quan gì tới quyền S3.
- Sau khi assume, bạn có credential tạm thời và danh tính `assumed-role/...`.

### Đường bấm từng bước

1. Ô **Search** → `IAM` → **Roles** → bấm `soa-c03-lab13-target`.
2. Tab **Trust relationships** → **Edit trust policy**: đọc `Principal.AWS`.
3. Tab **Permissions** → bấm policy `lab13-s3`: đọc action/resource.
4. Terminal: `aws sts assume-role --role-arn arn:aws:iam::<account>:role/soa-c03-lab13-target --role-session-name test`.
5. Nếu thành công, export 3 biến credential rồi chạy `aws sts get-caller-identity`.
6. Nếu lỗi, đọc `AccessDenied` message: principal nào, action nào.
7. Ô **Search** → `CloudTrail` → **Event history** → filter `AssumeRole` → xem `errorCode`/`errorMessage`.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Trust Principal | Phải là account/role của bạn, không phải account khác. |
| Conditions | Có thể yêu cầu MFA hoặc ExternalId. |
| Permission actions | Role có `s3:ListBucket`/`GetObject` không. |
| AccessDenied message | Nói rõ trust policy hay permission policy chặn. |
| get-caller-identity ARN | Phải chứa `assumed-role/soa-c03-lab13-target`. |
| Session duration | Mặc định 1h; hết hạn phải assume lại. |

### Link nhanh

- [IAM roles](https://console.aws.amazon.com/iam/home#/roles)
- [CloudTrail events](https://console.aws.amazon.com/cloudtrail/home?region=ap-southeast-1#/events)

### Nếu không thấy mục đó

- User của bạn không có `sts:AssumeRole`: thêm quyền cho user, không sửa trust policy của role lab.
- Trust policy đúng nhưng vẫn lỗi: có thể account ID trong ARN sai hoặc role name sai.
- Sau khi assume, credential chỉ nằm trong shell hiện tại; mở terminal mới phải export lại.
- `get-caller-identity` trả user gốc nghĩa là chưa export credential.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học AssumeRole: trust policy quyết định ai được assume; permission policy quyết định làm được gì.

### Bạn cần biết 4 khái niệm

- **Trust policy**: Danh sách principal được assume role.
- **Permission policy**: Quyền của role sau khi assume.
- **AssumeRole**: Đổi sang danh tính tạm thời.
- **Session**: Phiên assume, có thời hạn.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Role | soa-c03-lab13-target | tồn tại | IAM → Roles |
| Trust policy | tin cậy account lab | Principal đúng | IAM → Trust relationships |
| Permission | lab13-s3 | ListBucket, GetObject | IAM → Permissions |
| Core bucket | soa-c03-...-data | tồn tại | S3 → Buckets |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Ai được assume? | IAM → Trust relationships | Principal, Conditions |
| Assume xong làm gì? | IAM → Permissions | actions, resources |
| Lỗi STS? | CLI và CloudTrail | AccessDenied message |
| Danh tính sau assume? | aws sts get-caller-identity | assumed-role ARN |

### Trước khi phá, bạn phải trả lời 3 câu

1. Trust policy khác permission policy ở đâu?
2. AssumeRole lỗi thì sửa policy nào?
3. Làm sao chứng minh role đọc được S3?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 13 --live` và `./bin/lab teach 13`.

## 6. Hiện tượng bạn sẽ thấy

AssumeRole fail dù role có policy S3 đúng. Lỗi nằm ở trust policy, không phải permission.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Trust policy đang tin ai? | IAM → Roles → Trust relationships |
| Permission policy có gì? | IAM → Permissions |
| Lỗi STS nói gì? | `aws sts assume-role ...` |
| Sau khi assume, là ai? | `aws sts get-caller-identity` |

## 8. Thành công trông như thế nào?

`verify 13` PASS: AssumeRole thành công, identity là role, `aws s3 ls` được.

Nếu FAIL, đọc:

```bash
cat labs/13-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Trust policy vs permission policy.
- Role session, temporary credentials, expiry.
- Cross-account cần trust ở account đích + quyền sts:AssumeRole ở nguồn.

## 10. Note mẫu

- 1. Ai được assume?
- 2. Assume xong làm được gì?
- 3. Lỗi nằm ở trust hay permission?

## 11. Cleanup

```bash
./bin/lab down 13
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
./bin/lab hint 13
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 13. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
