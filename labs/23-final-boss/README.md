# Lab 23 — Final boss: 5 faults cùng lúc

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | All domains |
| Thời gian | ~240 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Trung bình |
| Lab ID | `23` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Bài cuối: 5 lỗi cùng lúc. Không có hint. Bạn phải ưu tiên user-facing path, rồi data, rồi quyền, và chứng minh từng lớp.
- **Việc đầu tiên:** Terminal: `curl -i http://<alb>/health` → ghi status code.
- **Xong khi:** `verify 23` PASS: path `/health`, SG app/DB allow, IAM không deny, `/db` 200, S3 OK, CPU < 60%, target healthy.
- **Nếu lạc:** `./bin/lab console 23` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Bài cuối: 5 lỗi cùng lúc. Không có hint. Bạn phải ưu tiên user-facing path, rồi data, rồi quyền, và chứng minh từng lớp.

## 2. Hiện tại có gì?

App stack chạy. `break 23` inject: health check path sai, SG app chặn 8080, SG DB chặn 5432, IAM deny S3, CPU load.

## 3. Kiến trúc

```text
Client → ALB → Target Group (path sai)
                    ├── App SG chặn 8080
                    ├── DB SG chặn 5432
                    ├── IAM deny s3:GetObject
                    └── CPU load
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/23-*/README.md` (file này) và dòng lab `23` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 23
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 23
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 23
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 23
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 23
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 23
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
| Triage | Phân loại và ưu tiên theo mức ảnh hưởng. |
| User-facing path | Đường người dùng đi: ALB → target → app. |
| Data path | Đường app → DB. |
| Identity path | Đường app role → S3/secret. |
| Layered fix | Sửa từng lớp, verify sau mỗi lần. |

### Khái niệm của lab này

- Bài cuối không có hint: năm lỗi ở năm lớp.
- **Thứ tự triage**: user-facing (`/health`, target) → data (`/db`) → identity (S3) → performance (CPU).
- Mỗi fix phải verify ngay; một fix có thể làm lộ lỗi tiếp theo.

### Đường bấm từng bước

1. Terminal: `curl -i http://<alb>/health` → ghi status code.
2. **EC2** → **Target groups** → `soa-c03-tg` → **Targets** + **Health checks**.
3. **EC2** → **Security groups** → SG app → **Inbound** 8080; SG DB → **Inbound** 5432.
4. **IAM** → **Roles** → role app → **Permissions** → inline `lab23-deny-s3`.
5. **CloudWatch** → **Logs Insights** → log app → lọc ERROR/AccessDenied.
6. **Systems Manager** → **Run Command** → `aws s3 ls s3://<bucket>` trên app instance.
7. **CloudWatch** → **Metrics** → EC2 CPU; **RDS** → `/db`.
8. Sửa một lớp → chạy `./bin/lab verify 23` → sang lớp tiếp.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| `/health` code | 503 thường là target/health check/SG. |
| Target health reason | Chỉ ra lớp mạng hoặc app. |
| SG app/DB | Hai rule độc lập; thiếu một cái là một đường chết. |
| Inline deny | `lab23-deny-s3` là deny chủ động. |
| S3 result | `aws s3 ls` fail = identity path. |
| CPU | Cao có thể do load, không nhất thiết là root cause. |

### Link nhanh

- [Target groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#TargetGroups:)
- [Security groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#SecurityGroups:)
- [IAM roles](https://console.aws.amazon.com/iam/home#/roles)
- [CloudWatch metrics](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#metricsV2:)
- [Logs Insights](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#logsV2:logs-insights)

### Nếu không thấy mục đó

- Sửa một lỗi mà verify vẫn fail: đọc output verify, nó nói lớp nào còn sai.
- Không chắc lỗi nào trước: làm user-facing trước, rồi data, rồi identity, cuối cùng performance.
- Đừng reset; reset chỉ dùng sau khi đã thử và phải ghi `SOLUTION_USED: yes`.
- Nếu bí quá 30 phút, dùng hint 1 rồi hint 2; không nhảy thẳng đáp án.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Final boss: năm lỗi cùng lúc. Triage user-facing → data → identity → performance.

### Bạn cần biết 4 khái niệm

- **Triage**: Phân loại và ưu tiên theo mức ảnh hưởng.
- **User-facing path**: ALB → target → app.
- **Data path**: app → DB.
- **Identity path**: app role → S3/secret.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| App | soa-c03-app | /health 200, /db 200 | ./bin/lab status |
| Target group | soa-c03-tg | 1 healthy | EC2 → Target groups |
| App SG | soa-c03-app-... | cho 8080 | EC2 → Security groups |
| DB SG | soa-c03-db-... | cho 5432 | EC2 → Security groups |
| App role | AppInstanceRoleName | không deny lab23 | IAM → Roles |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Health/target? | Target group + curl /health | 503/200, health reason |
| SG app/DB? | Security groups → Inbound | 8080, 5432 |
| S3 được không? | IAM role + SSM aws s3 ls | AccessDenied? |
| DB? | curl /db | 200/timeout |
| CPU? | CloudWatch → Metrics | CPUUtilization |

### Trước khi phá, bạn phải trả lời 3 câu

1. Bạn ưu tiên lỗi nào trước? Vì sao?
2. Lỗi nào có thể bị lỗi khác che?
3. Bạn chứng minh từng lớp bằng gì?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 23 --live` và `./bin/lab teach 23`.

## 6. Hiện tượng bạn sẽ thấy

Nhiều triệu chứng cùng lúc: 503, /db timeout, S3 AccessDenied, CPU cao. Bạn phải lập bảng symptom → layer → evidence.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| User-facing path có 200 không? | `/health` |
| Target có healthy không? | Target health |
| DB path có 200 không? | `/db` |
| Instance có đọc S3 không? | SSM: `aws s3 ls s3://<bucket>` |
| CPU còn cao không? | CloudWatch CPU |

## 8. Thành công trông như thế nào?

`verify 23` PASS: path `/health`, SG app/DB allow, IAM không deny, `/db` 200, S3 OK, CPU < 60%, target healthy.

Nếu FAIL, đọc:

```bash
cat labs/23-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Triage: user-facing → data → identity → performance.
- Mỗi fix phải verify ngay, không gộp.
- Không có hint; dùng evidence và thứ tự lớp.

## 10. Note mẫu

- 1. Triệu chứng nào ưu tiên nhất?
- 2. Lỗi nào bị che?
- 3. Bạn chứng minh từng lớp bằng gì?

## 11. Cleanup

```bash
./bin/lab down 23
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
./bin/lab hint 23
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 23. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
