# Lab 00 — Bootstrap: account, budget, core stack, guardrails

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | Foundation |
| Thời gian | ~90 phút |
| Cần app stack | Không |
| Chi phí | Thấp |
| Lab ID | `00` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Đây không phải lab phá hệ thống. Đây là bước lắp "nền nhà": account, budget, VPC, S3, KMS, CloudTrail, IAM, SSM. Nếu bước này sai, mọi lab sau đều sai theo.
- **Việc đầu tiên:** Mở ô **Search** trên cùng, gõ `CloudFormation`, chọn **CloudFormation**.
- **Xong khi:** `./bin/lab verify 00` PASS: core stack healthy, Trail logging, S3 BPA on, SSM/KMS/budget tồn tại.
- **Nếu lạc:** `./bin/lab console 00` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Đây không phải lab phá hệ thống. Đây là bước lắp "nền nhà": account, budget, VPC, S3, KMS, CloudTrail, IAM, SSM. Nếu bước này sai, mọi lab sau đều sai theo.

## 2. Hiện tại có gì?

Core stack đã được tạo bởi `make bootstrap`. App stack có thể đang tắt. Chưa có fault nào.

## 3. Kiến trúc

```text
Internet
   │
   ▼
Core stack: VPC, S3 bucket, KMS, CloudTrail, SNS, IAM, SSM
   │
   └── App stack (bật sau, khi làm lab 01+)
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Chỉ cần core stack; không cần app stack.

- Đọc `labs/00-*/README.md` (file này) và dòng lab `00` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị baseline:

   ```bash
   ./bin/lab up 00
   ```

2. Lab 00 **không có fault**. Không cần break, không cần hint.

3. Verify baseline:

   ```bash
   ./bin/lab verify 00
   ```

4. Ghi note:

   ```bash
   ./bin/lab note 00
   ```

5. Không cần `down`; core stack được giữ cho các lab sau.


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
| Core stack | Nền nhà dùng chung: VPC, S3, KMS, CloudTrail, SNS, IAM, SSM. |
| CloudTrail | Camera ghi lại ai đã gọi API nào, lúc nào. |
| Block Public Access | Công tắc khoá cửa bucket S3, chặn truy cập nặc danh. |
| KMS alias | Tên dễ nhớ trỏ tới một khoá mã hoá, ví dụ `alias/soa-c03-lab`. |
| Parameter Store | Ngăn kéo lưu cấu hình dạng key/value. |
| Budget | Chuông báo chi phí, không phải công tắc chặn chi phí. |

### Khái niệm của lab này

- **Baseline** là trạng thái nền phải đúng trước khi phá bất cứ thứ gì: audit log đang ghi, bucket không public, khoá mã hoá bật, tham số cấu hình tồn tại, và có cảnh báo chi phí.
- Nếu nền sai, mọi lab sau sẽ cho kết quả sai.

### Đường bấm từng bước

1. Mở ô **Search** trên cùng, gõ `CloudFormation`, chọn **CloudFormation**.
2. Menu trái → **Stacks** → bấm stack `soa-c03-core`.
3. Tab **Outputs**: ghi lại `DataBucketName`, `KmsKeyId`, `AlertTopicArn`, `AppLogGroupName`.
4. Ô **Search** → `CloudTrail` → **Dashboard**. Thẻ **Logging status** phải hiện trail `soa-c03-trail` đang **Logging**.
5. Ô **Search** → `S3` → **Buckets** → bấm bucket vừa ghi ở bước 3 → tab **Permissions**.
6. Mục **Block public access (bucket settings)** → **Edit**: cả 4 dòng phải đang **On**.
7. Ô **Search** → `KMS` → **Customer managed keys** → bấm alias `alias/soa-c03-lab` → xem **Key state** = **Enabled**.
8. Ô **Search** → `Systems Manager` → menu trái **Parameter Store** → tìm `/soa-c03/app/port`.
9. Ô **Search** → `Billing and Cost Management` → **Budgets** → bấm `soa-c03-monthly`.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Stack status | Phải là `CREATE_COMPLETE` hoặc `UPDATE_COMPLETE`. |
| Outputs | Đây là tên thật của bucket, key, topic, log group mà lab sau dùng. |
| Logging status | `On` nghĩa là CloudTrail đang ghi; `Off` nghĩa là không có bằng chứng forensic. |
| 4 cờ Block Public Access | Thiếu một cờ là bucket vẫn có thể lộ. |
| Key state | `Enabled` mới dùng được; `Pending deletion` là sắp mất. |
| Budget alerts | Cho biết ngưỡng và email nhận cảnh báo. |

### Link nhanh

- [CloudFormation stack `soa-c03-core`](https://console.aws.amazon.com/cloudformation/home?region=ap-southeast-1#/stacks)
- [CloudTrail dashboard](https://console.aws.amazon.com/cloudtrail/home?region=ap-southeast-1#/dashboard)
- [S3 buckets](https://console.aws.amazon.com/s3/buckets?region=ap-southeast-1)
- [KMS keys](https://console.aws.amazon.com/kms/home?region=ap-southeast-1#/kms/keys)
- [SSM Parameter Store](https://console.aws.amazon.com/systems-manager/parameters/?region=ap-southeast-1)
- [AWS Budgets](https://console.aws.amazon.com/billing/home?region=ap-southeast-1#/budgets)

### Nếu không thấy mục đó

- Trang trắng hoặc “no resources”: kiểm tra region ở góc trên phải là **Singapore (ap-southeast-1)**.
- “Access denied”: tài khoản đang dùng thiếu quyền đọc service đó; quay lại CLI `make doctor` để xem lỗi thật.
- Không thấy stack `soa-c03-core`: chưa chạy `make bootstrap`; **hỏi trước khi chạy** vì nó tạo tài nguyên (~$1–2/tháng).

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Baseline — kiểm tra nền trước khi làm lab khác

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Đây là lab nền: kiểm tra account, audit log, bucket private, khoá mã hoá, tham số và budget trước khi làm lab khác.

### Bạn cần biết 4 khái niệm

- **Core stack**: Nền nhà dùng chung: VPC, S3, KMS, CloudTrail, SNS, IAM, SSM.
- **CloudTrail**: Camera ghi lại ai gọi API gì.
- **Block Public Access**: Công tắc khoá bucket S3, chặn truy cập nặc danh.
- **Budget**: Chuông báo chi phí, không phải công tắc chặn chi phí.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| CloudFormation | soa-c03-core | CREATE_COMPLETE | CloudFormation → Stacks |
| CloudTrail | soa-c03-trail | Logging ON | CloudTrail → Dashboard |
| S3 bucket | DataBucketName (Outputs) | 4 cờ BPA bật | S3 → Buckets → Permissions |
| KMS alias | alias/soa-c03-lab | Enabled | KMS → Customer managed keys |
| SSM parameter | /soa-c03/app/port | tồn tại | Systems Manager → Parameter Store |
| Budget | soa-c03-monthly | tồn tại | Billing → Budgets |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Core có khoẻ? | CloudFormation → stack → Stack info | Status và Status reason |
| Audit log đang ghi? | CloudTrail → Dashboard | Logging status |
| Bucket private? | S3 → Permissions | 4 cờ Block Public Access |
| Key và parameter? | KMS / Parameter Store | Key state, Parameter value |
| Budget? | Billing → Budgets | Budgeted amount và alerts |

### Trước khi làm lab khác, bạn phải trả lời 3 câu

1. Core stack đang ở trạng thái nào?
2. Nếu CloudTrail tắt, bạn mất loại bằng chứng gì?
3. Vì sao phải kiểm tra bucket private trước khi làm lab?

> Trả lời được 3 câu này rồi mới chuyển sang lab khác. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 00 --live` và `./bin/lab teach 00`.

## 6. Hiện tượng bạn sẽ thấy

Không có sự cố. Bạn chỉ kiểm tra baseline: CloudTrail có ghi log, S3 có chặn public, KMS/SSM có tồn tại, budget có cảnh báo.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| CloudTrail có đang ghi log? | `aws cloudtrail get-trail-status --name soa-c03-trail` |
| S3 có chặn public hoàn toàn? | `aws s3api get-public-access-block --bucket <bucket>` |
| Budget có tồn tại? | `aws budgets describe-budget --account-id <account> --budget-name soa-c03-monthly` |
| SSM parameter cho app có chưa? | `aws ssm get-parameter --name /soa-c03/app/port` |

## 8. Thành công trông như thế nào?

`./bin/lab verify 00` PASS: core stack healthy, Trail logging, S3 BPA on, SSM/KMS/budget tồn tại.

Nếu FAIL, đọc:

```bash
cat labs/00-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Ops baseline: account guardrails, budget, tagging, expiry date.
- CloudTrail management events vs data events.
- Vì sao phải có budget trước khi làm lab tốn tiền.

## 10. Note mẫu

- 1. Tôi đã tạo gì? (core stack, budget, trail)
- 2. Không có fault; verify baseline thay vì đi tìm lỗi.
- 3. Bằng chứng: output của `make doctor` và `verify 00`.

## 11. Cleanup

```bash
./bin/lab down 00
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
./bin/lab hint 00
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 00. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
