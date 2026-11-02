# Lab 17 — Boss fight: 3 lỗi mạng cùng lúc

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D5 Networking 18% |
| Thời gian | ~180 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Trung bình |
| Lab ID | `17` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Đây là bài tổng hợp D5: 3 lỗi cùng lúc ở target health, SG và NACL. Bạn phải tách lớp, không sửa mù.
- **Việc đầu tiên:** **EC2** → **Target groups** → `soa-c03-tg` → **Targets**: đọc health reason.
- **Xong khi:** `verify 17` PASS: path `/health`, SG allow, NACL không deny 8080, target healthy, `/health` 200.
- **Nếu lạc:** `./bin/lab console 17` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Đây là bài tổng hợp D5: 3 lỗi cùng lúc ở target health, SG và NACL. Bạn phải tách lớp, không sửa mù.

## 2. Hiện tại có gì?

App stack chạy. Lab bật Flow Logs và inject 3 lỗi: health check path sai, SG chặn 8080, NACL deny 8080.

## 3. Kiến trúc

```text
Client → ALB → Target Group (sai path)
                    │
                    ├── SG chặn 8080
                    └── NACL deny 8080
                         ▼
                       EC2 app
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/17-*/README.md` (file này) và dòng lab `17` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 17
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 17
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 17
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 17
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 17
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 17
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
| Health check path | Đường dẫn ALB gọi để kiểm tra app. |
| Security group | Tường lửa stateful ở ENI. |
| NACL | Tường lửa stateless ở subnet, có số thứ tự. |
| Flow Logs | Bằng chứng ACCEPT/REJECT. |
| Layered fix | Sửa một lớp, verify, rồi mới sang lớp tiếp. |

### Khái niệm của lab này

- Ba lỗi cùng lúc ở ba lớp: **health check path**, **security group**, **NACL**.
- Một lỗi có thể che lỗi khác, nên phải sửa từng lớp và chứng minh bằng target health + Flow Logs.
- NACL là stateless: deny inbound 8080 là đủ làm app chết dù SG đúng.

### Đường bấm từng bước

1. **EC2** → **Target groups** → `soa-c03-tg` → **Targets**: đọc health reason.
2. Cùng target group → **Health checks**: đọc path hiện tại.
3. **EC2** → **Security groups** → SG app → **Inbound rules**: tìm TCP 8080.
4. **VPC** → **Network ACLs** → NACL của subnet app → **Inbound rules**: tìm rule deny port 8080 và số rule.
5. **VPC** → **Flow logs** → log group `/aws/vpc/soa-c03/lab17` → **Logs Insights** query `filter dstport = 8080`.
6. Sửa path trước → đợi health check → xem target.
7. Sửa SG → xem target.
8. Sửa NACL → xem target + `/health` 200.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Health check path | Phải là `/health`, không phải đường dẫn không tồn tại. |
| SG inbound 8080 | Phải cho SG của ALB, không phải `0.0.0.0/0`. |
| NACL rule number | Rule số nhỏ hơn được đánh giá trước; deny thắng allow. |
| Flow log REJECT | Chứng minh gói bị chặn ở lớp nào. |
| Target health sau mỗi fix | Chỉ một lớp thay đổi mỗi lần để biết nhân quả. |
| HTTP `/health` | 200 là tiêu chí cuối, không phải target `healthy` đơn thuần. |

### Link nhanh

- [Target groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#TargetGroups:)
- [Security groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#SecurityGroups:)
- [Network ACLs](https://console.aws.amazon.com/vpcconsole/home?region=ap-southeast-1#NetworkAcls:)
- [Flow logs](https://console.aws.amazon.com/vpcconsole/home?region=ap-southeast-1#FlowLogs:)

### Nếu không thấy mục đó

- Target vẫn unhealthy sau khi sửa path: chờ ít nhất 3 × interval.
- Flow Logs chưa có dữ liệu: có thể trễ 5–10 phút.
- NACL có nhiều rule: đọc theo số thứ tự từ thấp lên, không chỉ nhìn rule bạn vừa sửa.
- Đừng sửa cả ba lớp cùng lúc; bạn sẽ không biết lớp nào thật sự chặn.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Boss fight D5: ba lỗi cùng lúc ở health check, security group và NACL. Sửa từng lớp, verify từng lần.

### Bạn cần biết 4 khái niệm

- **Health check path**: Đường dẫn ALB gọi để kiểm tra app.
- **Security group**: Tường lửa stateful ở ENI.
- **NACL**: Tường lửa stateless ở subnet, có số thứ tự.
- **Flow Logs**: Bằng chứng ACCEPT/REJECT.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Target group | soa-c03-tg | path /health, 1 healthy | EC2 → Target groups |
| App SG | soa-c03-app-... | cho 8080 | EC2 → Security groups |
| NACL | NACL của subnet app | không deny 8080 | VPC → Network ACLs |
| Flow log | /aws/vpc/soa-c03/lab17 | tồn tại | CloudWatch → Log groups |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Target lỗi gì? | Target group → Targets | health reason |
| Path đúng? | Target group → Health checks | HealthCheckPath |
| SG cho 8080? | Security groups → Inbound | port, source |
| NACL deny? | Network ACLs → Inbound | rule number, deny |
| Flow nói gì? | Flow Logs → Insights | REJECT/ACCEPT |

### Trước khi phá, bạn phải trả lời 3 câu

1. Vì sao phải sửa từng lớp, không sửa cả ba?
2. NACL stateless khác SG ở đâu?
3. Lỗi nào có thể che lỗi nào?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 17 --live` và `./bin/lab teach 17`.

## 6. Hiện tượng bạn sẽ thấy

ALB 503, target unhealthy, app có thể vẫn chạy. Một lỗi có thể che lỗi khác.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Target healthy không? | Target Group → Targets |
| Health check path đúng chưa? | Target Group → Health checks |
| SG có cho 8080 không? | EC2 → Security Groups |
| NACL có deny 8080 không? | VPC → Network ACLs |

## 8. Thành công trông như thế nào?

`verify 17` PASS: path `/health`, SG allow, NACL không deny 8080, target healthy, `/health` 200.

Nếu FAIL, đọc:

```bash
cat labs/17-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Sửa từng lớp, verify sau mỗi lần.
- NACL là stateless; deny inbound 8080 đủ làm app chết.
- Một fix có thể che symptom nhưng chưa hết root cause.

## 10. Note mẫu

- 1. Lỗi nào lộ ra trước?
- 2. Lỗi nào bị che?
- 3. Bạn chứng minh từng lớp bằng gì?

## 11. Cleanup

```bash
./bin/lab down 17
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
./bin/lab hint 17
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 17. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
