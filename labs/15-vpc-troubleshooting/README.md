# Lab 15 — VPC: SG, NACL, route, Flow Logs, Reachability

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D5 Networking 18% |
| Thời gian | ~150 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Trung bình |
| Lab ID | `15` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học debug mạng theo lớp: SG → NACL → route → target. Không đoán; dùng Flow Logs và Reachability Analyzer để có bằng chứng.
- **Việc đầu tiên:** Ô **Search** → `EC2` → **Target groups** → `soa-c03-tg` → **Targets**: đọc health reason.
- **Xong khi:** `verify 15` PASS: SG rule 8080 có, `/health` 200, Reachability Analyzer `reachable`.
- **Nếu lạc:** `./bin/lab console 15` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học debug mạng theo lớp: SG → NACL → route → target. Không đoán; dùng Flow Logs và Reachability Analyzer để có bằng chứng.

## 2. Hiện tại có gì?

App stack chạy. Lab bật Flow Logs và tạo một Reachability Analyzer path từ ALB ENI đến app ENI.

## 3. Kiến trúc

```text
Client → ALB → SG → NACL → Route → EC2 app
                              │
                              └── Flow Logs ghi ACCEPT/REJECT
Reachability Analyzer kiểm tra path
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/15-*/README.md` (file này) và dòng lab `15` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 15
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 15
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 15
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 15
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 15
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 15
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
| Security group | Tường lửa stateful gắn vào ENI. |
| NACL | Tường lửa stateless gắn vào subnet. |
| Route table | Bảng chỉ đường ra Internet/giữa subnet. |
| Flow Logs | Nhật ký luồng IP, có ACCEPT/REJECT. |
| Reachability Analyzer | Công cụ mô phỏng đường đi và tìm điểm chặn. |
| Ephemeral port | Port tạm cho chiều về, thường 1024–65535. |

### Khái niệm của lab này

- Mạng đi qua nhiều lớp: **Security Group** (stateful, chỉ cần cho chiều vào), **NACL** (stateless, phải cho cả chiều về), **route table**, rồi tới app.
- **Flow Logs** ghi ACCEPT/REJECT; **Reachability Analyzer** chỉ ra lớp nào chặn trên đường đi.

### Đường bấm từng bước

1. Ô **Search** → `EC2` → **Target groups** → `soa-c03-tg` → **Targets**: đọc health reason.
2. **Security groups** → SG của app → tab **Inbound rules**: phải có TCP 8080 từ SG của ALB.
3. Ô **Search** → `VPC` → **Network ACLs** → bấm NACL gắn với subnet của app → **Inbound rules** + **Outbound rules**.
4. **Route tables** → bấm route table của subnet → tab **Routes** và **Subnet associations**.
5. **Flow logs** → bấm flow log của VPC → link tới log group `/aws/vpc/soa-c03/lab15`.
6. Trong log group → **Logs Insights**, chạy:
   ```sql
   fields @timestamp, srcaddr, dstaddr, srcport, dstport, action
   | filter dstport = 8080
   | sort @timestamp desc
   | limit 20
   ```
7. **Reachability Analyzer** → **Create and analyze path** → chọn source ALB ENI, destination app ENI, port 8080 → **Create path** → **Run analysis**.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Target health reason | Cho biết health check fail vì timeout, response code, hay connection. |
| SG inbound | Chỉ cần cho chiều vào; stateful tự cho chiều về. |
| NACL inbound/outbound | Phải cho cả 8080 và ephemeral ports; deny theo số thứ tự thấp hơn sẽ thắng. |
| Route | `local` cho nội bộ VPC; `0.0.0.0/0` qua IGW/NAT cho Internet. |
| Flow log action | `REJECT` chỉ ra lớp chặn; `ACCEPT` chứng minh đã qua. |
| Analyzer path | Chỉ ra từng hop `ACCEPT`/`BLOCKED` và lý do. |

### Link nhanh

- [Target groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#TargetGroups:)
- [Security groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#SecurityGroups:)
- [VPC console](https://console.aws.amazon.com/vpcconsole/home?region=ap-southeast-1)
- [Flow logs](https://console.aws.amazon.com/vpcconsole/home?region=ap-southeast-1#FlowLogs:)
- [Reachability Analyzer](https://console.aws.amazon.com/vpcconsole/home?region=ap-southeast-1#ReachabilityAnalyzer:)

### Nếu không thấy mục đó

- Flow Logs có thể trễ 5–10 phút; đừng kết luận “không có traffic” quá sớm.
- Analyzer chỉ kiểm tra cấu hình, không chứng minh app trả 200.
- NACL là stateless: thiếu outbound ephemeral ports là lỗi rất hay gặp.
- Sửa một lớp rồi kiểm tra lại; đừng sửa SG + NACL + route cùng lúc.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học debug mạng theo lớp: target health → SG → NACL → route; dùng Flow Logs và Reachability Analyzer.

### Bạn cần biết 4 khái niệm

- **Security group**: Tường lửa stateful gắn vào ENI.
- **NACL**: Tường lửa stateless gắn vào subnet.
- **Flow Logs**: Nhật ký luồng IP, có ACCEPT/REJECT.
- **Reachability Analyzer**: Mô phỏng đường đi và tìm điểm chặn.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Target group | soa-c03-tg | 1 healthy | EC2 → Target groups |
| App SG | soa-c03-app-... | cho 8080 từ ALB SG | EC2 → Security groups |
| Flow log | /aws/vpc/soa-c03/lab15 | tồn tại | CloudWatch → Log groups |
| Reachability path | tag soa-c03-lab15-path | available | VPC → Reachability Analyzer |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Target lỗi gì? | Target group → Targets | Health status details |
| SG cho 8080? | Security groups → Inbound | port, source |
| NACL cho 8080? | VPC → Network ACLs | rule number, allow/deny |
| Route đúng? | VPC → Route tables | local, IGW |
| Flow nói gì? | Flow Logs → Insights | action ACCEPT/REJECT |
| Analyzer? | Reachability Analyzer | path found, blocked layer |

### Trước khi phá, bạn phải trả lời 3 câu

1. SG khác NACL ở đâu?
2. Nếu SG đúng mà vẫn timeout, bạn xem gì?
3. Flow Logs REJECT chứng minh điều gì?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 15 --live` và `./bin/lab teach 15`.

## 6. Hiện tượng bạn sẽ thấy

App không truy cập được từ ALB; target unhealthy hoặc 503. Bạn phải tìm lớp nào chặn.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Target health nói gì? | Target Group → Targets |
| SG app có cho ALB SG vào 8080? | EC2 → Security Groups → Inbound |
| NACL có deny không? | VPC → Network ACLs → Inbound/Outbound |
| Route có đúng không? | VPC → Route tables |
| Flow Logs nói ACCEPT hay REJECT? | CloudWatch Logs `/aws/vpc/soa-c03/flow` |

## 8. Thành công trông như thế nào?

`verify 15` PASS: SG rule 8080 có, `/health` 200, Reachability Analyzer `reachable`.

Nếu FAIL, đọc:

```bash
cat labs/15-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- SG stateful, NACL stateless; NACL cần ephemeral ports.
- Đọc Flow Logs: srcaddr/dstaddr/port/action.
- Reachability Analyzer chỉ ra lớp chặn.

## 10. Note mẫu

- 1. Lớp nào chặn?
- 2. Flow Logs chứng minh gì?
- 3. NACL khác SG ở đâu?

## 11. Cleanup

```bash
./bin/lab down 15
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
./bin/lab hint 15
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 15. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
