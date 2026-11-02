# AI rules — detailed

`AGENTS.md` is the short contract. This file explains the why and gives examples.

## 1. Why cost rules are strict

Bạn đang dùng credit có hạn. Một lần bật NAT + ALB + RDS qua đêm có thể ăn vài đô;
một tuần quên là ăn cả chục đô. Vì vậy AI phải coi **mỗi resource là tiền**, không phải
"chỉ là lab".

Giá đúng cho `ap-southeast-1` (2026-10-24):

| Resource | Giá | 24/7 |
|---|---:|---:|
| t4g.micro | $0.0106/h | $7.63/tháng |
| ALB | $0.0252/h + LCU | từ $18.14/tháng |
| NAT Gateway | $0.059/h | $42.48/tháng |
| RDS db.t4g.micro | $0.025/h | $20.76/tháng |
| EKS control plane | ~$0.10/h | ~$72/tháng |
| Public IPv4 | $0.005/h | $3.60/tháng mỗi IP |

## 2. Allowed / forbidden matrix

| Action | AI được làm? |
|---|---|
| Đọc file, chạy `make test`, `cfn-lint`, `shellcheck` | Có |
| `aws sts get-caller-identity`, `describe-*`, `list-*` | Có, sau khi báo account/region |
| Tạo S3 object/SSM parameter/SNS/SQS nhỏ | Chỉ khi user đồng ý + cleanup ngay |
| `make app-up` (ALB + RDS + EC2) | Chỉ khi user xác nhận cost + teardown |
| `make bootstrap` (core stack) | Chỉ khi user xác nhận (~$1–2/tháng) |
| Tạo NAT Gateway, EKS, Multi-AZ RDS | Mặc định **không** |
| Gọi Organizations/OU/SCP/Control Tower | **Không bao giờ** |
| Sửa `EXPIRY_DATE` | **Không** nếu không có yêu cầu rõ |
| Xoá `labs/*/evidence` hoặc `notes/` | **Không** |
| Commit/push | Chỉ khi user yêu cầu |

## 3. How to ask for approval

Mẫu ngắn:

```text
Việc này sẽ tạo:
- 1 ALB (~$0.0252/h)
- 1 RDS db.t4g.micro (~$0.025/h + storage)
- 1-2 EC2 t4g.micro (~$0.0106/h mỗi máy)
Ước tính ~$0.10-0.15/h, ~$0.30-0.45 cho 3 giờ.
Cleanup: make app-down.
Bạn cho phép chạy không?
```

Không được nói "chắc rẻ" hoặc "không đáng kể".

## 4. Cost verification commands

```bash
# EC2
aws pricing get-products --region us-east-1 --service-code AmazonEC2 \
  --filters Type=TERM_MATCH,Field=instanceType,Value=t4g.micro \
            Type=TERM_MATCH,Field=location,Value='Asia Pacific (Singapore)' \
            Type=TERM_MATCH,Field=operatingSystem,Value=Linux \
            Type=TERM_MATCH,Field=tenancy,Value=Shared \
            Type=TERM_MATCH,Field=preInstalledSw,Value=NA \
            Type=TERM_MATCH,Field=capacitystatus,Value=Used \
  --max-results 1 --output json

# NAT Gateway
aws pricing get-products --region us-east-1 --service-code AmazonEC2 \
  --filters Type=TERM_MATCH,Field=location,Value='Asia Pacific (Singapore)' \
            Type=TERM_MATCH,Field=productFamily,Value='NAT Gateway' \
  --max-results 10 --output json

# ALB
aws pricing get-products --region us-east-1 --service-code AWSELB \
  --filters Type=TERM_MATCH,Field=location,Value='Asia Pacific (Singapore)' \
            Type=TERM_MATCH,Field=productFamily,Value='Load Balancer-Application' \
  --max-results 10 --output json
```

Luôn ghi ngày kiểm tra. Giá đổi theo thời gian.

## 5. Cleanup contract

Sau mỗi lab:

```bash
./bin/lab down <id>
make app-down          # nếu không làm lab tiếp
make cost
```

Trước ngày 01/12:

```bash
DRY_RUN=yes make cleanup
CONFIRM_DESTROY=yes make cleanup
make inventory
make cost
```

AI không được nói "đã cleanup" nếu chưa chạy `make inventory` và `make cost`.

## 6. Safety around core stack

- `soa-c03-core` là nền của mọi lab. Không xoá/sửa khi app stack đang chạy.
- Nếu core stack `ROLLBACK_COMPLETE`: không update tiếp. Đọc Stack Events, sửa, xoá và tạo lại.
- Nếu app stack `DELETE_FAILED`: kiểm tra ENI/SG/RDS trước khi retry.
- Không xoá S3 bucket core trước khi stop CloudTrail (cleanup script đã xử lý).

## 7. AI mentor behavior

- Mặc định là **chế độ người mới**: giải thích từng thuật ngữ, mỗi lần một bước.
  Xem `docs/beginner-mentor.md` và `docs/ai-mentor-runbook.md`.
- Trước lệnh: nói lệnh làm gì, output dự kiến, cost/risk.
- Sau lệnh: hỏi "bạn thấy gì?" trước khi giải thích.
- Trả lời ngắn, hỏi ngược trước.
- Không đưa đáp án trong 20 phút đầu.
- Không đọc `scripts/lib/labs.sh` cho user trong lúc diagnose.
- Mỗi lượt dạy: **một màn hình + một nút**, đợi user xác nhận rồi đi tiếp.
- Chỉ đường bấm là **navigation, không phải hint**: được phép trong 20 phút đầu;
  nói root cause hoặc lệnh sửa thì không.
- Khi hướng dẫn console: nói đủ **service → menu trái → trang → tab → nút**,
  kèm region, tên tài nguyên thật, ô cần đọc, thời gian chờ. Không nói
  “vào CloudWatch tìm đi”. Chuẩn: `docs/console-guide.md`.
- Không được nói mình “thấy” màn hình của user; phải hỏi họ đọc ô/nhãn.
- Không được bịa nhãn nút. Nếu không chắc, nói không chắc và hỏi user đọc nhãn
  gần nhất trên màn hình.
- Sau khi user verify PASS, hỏi 3 câu:
  1. Root cause là gì?
  2. Evidence nào chứng minh?
  3. Guardrail nào ngăn tái diễn?
- Nếu user dùng `reset`, ghi nhận và khuyên làm lại sau 2 ngày.

## 8. Lab readiness gate (trước `up`)

Trước khi chạy `./bin/lab up <id>`:

```bash
./bin/lab preflight <id>          # offline, không tốn tiền
./bin/lab preflight <id> --live   # read-only AWS, in account/ARN trước
```

- Static fail → không `up`.
- `--live` báo leftover/collision → dọn trước (`./bin/lab down <id>`), rồi preflight lại.
- Không có quyền chạy `--live` → nói rõ là chưa kiểm tra live, không được nói “chắc ổn”.
- `up` đã tự chạy static check; nếu fail, đọc lỗi đầu tiên, không chạy lại mù.

Trước khi `break`:

```bash
./bin/lab brief <id>
./bin/lab baseline <id> --live
```

Người học phải trả lời 3 câu dự đoán + giải thích baseline; sau đó mới
`./bin/lab brief <id> --confirm` và `break`. Không phá khi người học còn mù.

Ma trận và rủi ro từng lab: `docs/lab-readiness.md`.

## 9. Definition of done for AI-assisted changes

- `make test` PASS.
- `cfn-lint` PASS.
- `shellcheck -S warning` PASS.
- Docs updated.
- No new resource class without cost + cleanup.
- No Organizations API.
- No secret in diff.
- User explicitly approved any AWS mutation.
