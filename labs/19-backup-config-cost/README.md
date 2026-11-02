# Lab 19 — AWS Backup, Config, Cost Explorer, Budgets

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D2/D3 |
| Thời gian | ~180 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Trung bình |
| Lab ID | `19` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học vận hành backup/compliance/cost: backup plan, recovery point, Config recorder, budget, Cost Explorer. Không phải lab sửa app.
- **Việc đầu tiên:** Ô **Search** → `AWS Backup` → **Backup vaults** → bấm `soa-c03-lab19`.
- **Xong khi:** `verify 19` PASS: backup `COMPLETED`, có recovery point, Config `recording=True`, budget tồn tại.
- **Nếu lạc:** `./bin/lab console 19` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học vận hành backup/compliance/cost: backup plan, recovery point, Config recorder, budget, Cost Explorer. Không phải lab sửa app.

## 2. Hiện tại có gì?

App stack + RDS chạy. Lab tạo backup vault/plan/job, Config recorder/rule, budget riêng.

## 3. Kiến trúc

```text
AWS Backup
   ├── vault
   ├── plan (daily)
   └── on-demand job → recovery point

AWS Config
   ├── recorder → S3
   └── rule encrypted-volumes

Budgets + Cost Explorer
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/19-*/README.md` (file này) và dòng lab `19` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 19
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 19
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 19
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 19
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 19
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 19
   ```

## 5b. Ghi chú / lệnh riêng

Backup RDS có thể mất vài phút. Cost Explorer có thể chưa có dữ liệu trong ngày; verify chỉ cảnh báo, không fail.

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
| Backup vault | Kho chứa recovery point. |
| Backup plan | Lịch backup và thời gian giữ. |
| Recovery point | Một bản backup cụ thể. |
| Config recorder | Bộ ghi trạng thái tài nguyên. |
| Config rule | Luật compliance, ví dụ EBS phải mã hoá. |
| Budget | Cảnh báo chi phí theo ngưỡng. |

### Khái niệm của lab này

- **AWS Backup** dùng vault + plan + resource assignment để tạo **recovery point**.
- **AWS Config** ghi lại trạng thái tài nguyên và chấm compliance bằng rule; recorder phải đang chạy.
- **Budget** chỉ cảnh báo, không chặn chi phí; **Cost Explorer** có thể trễ tới 24h.

### Đường bấm từng bước

1. Ô **Search** → `AWS Backup` → **Backup vaults** → bấm `soa-c03-lab19`.
2. Tab **Recovery points**: xem recovery point mới nhất, **Status = Completed**.
3. Menu trái **Backup plans** → `soa-c03-lab19-plan` → **Resource assignments**: tag `Backup=lab19`.
4. Menu trái **Jobs** → bấm job gần nhất → đọc **Status**, **Resource**, **Completion time**.
5. Ô **Search** → `AWS Config` → **Rules** → `soa-c03-lab19-encrypted-volumes` → **Compliance**.
6. Menu trái **Settings**: xem **Recording is on/off** và delivery channel.
7. Ô **Search** → `Billing and Cost Management` → **Budgets** → `soa-c03-lab19`.
8. **Cost Explorer** → **Cost and usage** → group by **Service**.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Recovery point status | `Completed` mới dùng để restore. |
| Backup job status | `COMPLETED`, `FAILED`, `EXPIRED`. |
| Resource assignment | Tag đúng thì RDS mới được chọn. |
| Config recording | `On` thì rule mới có dữ liệu. |
| Rule compliance | `COMPLIANT`/`NON_COMPLIANT`; mới bật có thể `INSUFFICIENT_DATA`. |
| Budget vs Cost Explorer | Budget là ngưỡng; Cost Explorer là số tiền thực tế. |

### Link nhanh

- [AWS Backup vaults](https://console.aws.amazon.com/backup/home?region=ap-southeast-1#backup/vaults)
- [AWS Backup plans](https://console.aws.amazon.com/backup/home?region=ap-southeast-1#backup/plans)
- [AWS Config dashboard](https://console.aws.amazon.com/config/home?region=ap-southeast-1#/dashboard)
- [AWS Budgets](https://console.aws.amazon.com/billing/home?region=ap-southeast-1#/budgets)
- [Cost Explorer](https://console.aws.amazon.com/costmanagement/home?region=ap-southeast-1#/cost-explorer)

### Nếu không thấy mục đó

- Backup job chưa xong: RDS snapshot có thể mất vài phút; quay lại sau.
- Config `INSUFFICIENT_DATA`: recorder mới bật hoặc rule mới tạo; chờ vài phút.
- Cost Explorer trống: dữ liệu có thể trễ 24h; không kết luận là không tốn tiền.
- Budget không chặn chi phí; nó chỉ gửi cảnh báo.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học backup/compliance/cost: AWS Backup, Config recorder, budget, Cost Explorer.

### Bạn cần biết 4 khái niệm

- **Backup vault**: Kho chứa recovery point.
- **Backup plan**: Lịch backup và thời gian giữ.
- **Config recorder**: Bộ ghi trạng thái tài nguyên.
- **Budget**: Cảnh báo chi phí, không chặn chi phí.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Backup vault | soa-c03-lab19 | tồn tại | AWS Backup → Vaults |
| Backup plan | soa-c03-lab19-plan | tồn tại | AWS Backup → Plans |
| Config recorder | soa-c03-lab19 | recording | AWS Config → Settings |
| Config rule | soa-c03-lab19-encrypted-volumes | compliance | AWS Config → Rules |
| Budget | soa-c03-lab19 | tồn tại | Billing → Budgets |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Backup job? | AWS Backup → Jobs | State |
| Recovery point? | AWS Backup → Vault | số lượng, status |
| Config recording? | AWS Config → Settings | Recording on/off |
| Rule compliance? | AWS Config → Rules | COMPLIANT/NON_COMPLIANT |
| Cost? | Cost Explorer | service, ngày |

### Trước khi phá, bạn phải trả lời 3 câu

1. Backup job COMPLETED đã đủ chưa?
2. Config khác CloudTrail ở đâu?
3. Budget có chặn chi phí không?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 19 --live` và `./bin/lab teach 19`.

## 6. Hiện tượng bạn sẽ thấy

Config recorder bị stop; dữ liệu compliance trở nên cũ. Bạn kiểm tra backup job, recovery point, Config status, budget.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Backup job xong chưa? | `aws backup describe-backup-job --backup-job-id <id>` |
| Có recovery point không? | `aws backup list-recovery-points-by-backup-vault` |
| Config có recording không? | `aws configservice describe-configuration-recorder-status` |
| Budget có tồn tại không? | `aws budgets describe-budget` |
| Cost Explorer có dữ liệu không? | `aws ce get-cost-and-usage` (có thể trễ 24h) |

## 8. Thành công trông như thế nào?

`verify 19` PASS: backup `COMPLETED`, có recovery point, Config `recording=True`, budget tồn tại.

Nếu FAIL, đọc:

```bash
cat labs/19-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- AWS Backup vs RDS snapshot; recovery point.
- Config (resource state/compliance) vs CloudTrail (API audit).
- Budget alert không chặn chi phí; chỉ thông báo.

## 10. Note mẫu

- 1. Backup job mất bao lâu?
- 2. Recovery point nằm ở đâu?
- 3. Config khác CloudTrail thế nào?

## 11. Cleanup

```bash
./bin/lab down 19
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
./bin/lab hint 19
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 19. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
