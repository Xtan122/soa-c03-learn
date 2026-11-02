# Lab 05 — ALB health check → 503

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D2 Reliability 22% |
| Thời gian | ~120 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Thấp |
| Lab ID | `05` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học vì sao ALB trả 503. 503 thường không phải app chết, mà là ALB không có target khoẻ.
- **Việc đầu tiên:** Ô **Search** → `EC2` → menu trái **Load Balancers** → bấm `soa-c03-alb`.
- **Xong khi:** `verify 05` PASS: health check path `/health`, target healthy, `curl /health` = 200.
- **Nếu lạc:** `./bin/lab console 05` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học vì sao ALB trả 503. 503 thường không phải app chết, mà là ALB không có target khoẻ.

## 2. Hiện tại có gì?

App stack chạy, ALB đang healthy, health check path là `/health`. Lab sẽ làm health check trỏ sai.

## 3. Kiến trúc

```text
Client → ALB :80 → Target Group
                         │ health check /health :8080
                         ▼
                       EC2 app
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/05-*/README.md` (file này) và dòng lab `05` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 05
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 05
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 05
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 05
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 05
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 05
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
| Listener | Cửa của ALB, ví dụ HTTP:80. |
| Target group | Danh sách instance/container nhận traffic. |
| Health check | Lễ tân gọi vào phòng xem app còn trả lời. |
| Healthy / Unhealthy | Target có vượt qua health check hay không. |
| 503 | ALB không có target khoẻ để chuyển request. |
| 502 / 504 | Target trả lỗi / target trả lời quá chậm. |

### Khái niệm của lab này

- **ALB** nhận request, **listener** quyết định chuyển tới **target group** nào.
- Target group chỉ chuyển traffic tới target đang **healthy**.
- Health check là request định kỳ của ALB vào target; sai path/port/protocol thì target bị đánh `unhealthy` và ALB trả 503 dù app vẫn sống.

### Đường bấm từng bước

1. Ô **Search** → `EC2` → menu trái **Load Balancers** → bấm `soa-c03-alb`.
2. Tab **Listeners**: bấm listener HTTP:80 → xem **Default action** trỏ tới target group nào.
3. Menu trái **Target groups** → bấm `soa-c03-tg`.
4. Tab **Targets**: đọc cột **Health status** và **Health status details**.
5. Tab **Health checks** → **Edit**: đọc path, port, protocol, interval, timeout, healthy/unhealthy threshold.
6. Terminal: `curl -i http://<alb-dns>/health`; so sánh status code.
7. Ô **Search** → `EC2` → **Instances** → bấm instance đang chạy → tab **Security** → xem security group.
8. Mở security group của app → **Inbound rules**: phải có TCP 8080 từ SG của ALB.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Target Health status | `healthy`, `unhealthy`, `initial`, `draining`, `unused`. |
| Health status details | Ví dụ `Target.FailedHealthChecks`, `Target.Timeout`, `Target.ResponseCodeMismatch`. |
| Health check path/port | Phải trùng route và port app thật sự nghe. |
| Matcher | Mặc định chỉ chấp nhận HTTP 200. |
| ALB response code | 503 = không có target khoẻ; 502 = target trả lỗi. |
| SG inbound 8080 | Thiếu rule này thì health check không bao giờ tới app. |

### Link nhanh

- [Load balancers](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#LoadBalancers:)
- [Target groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#TargetGroups:)
- [Instances](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#Instances:)
- [Security groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#SecurityGroups:)

### Nếu không thấy mục đó

- Target group không có target: ASG chưa đăng ký instance; xem **ASG → Activity**.
- Target `unhealthy` nhưng app `/health` vẫn 200 từ ngoài: health check có thể dùng port/path khác, hoặc SG chỉ mở cho IP của bạn.
- Sửa xong phải đợi ít nhất `healthy threshold × interval` trước khi thấy healthy.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học vì sao ALB trả 503: target group không có target khoẻ, thường do health check path/port/protocol.

### Bạn cần biết 4 khái niệm

- **Listener**: Cửa của ALB, ví dụ HTTP:80.
- **Target group**: Danh sách instance nhận traffic.
- **Health check**: ALB gọi định kỳ vào target để kiểm tra.
- **503**: ALB không có target khoẻ để chuyển request.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| ALB | soa-c03-alb | active | EC2 → Load balancers |
| Target group | soa-c03-tg | 1 target healthy | EC2 → Target groups |
| Health check | path /health, port traffic-port | 200 | Target group → Health checks |
| App | soa-c03-app | /health 200 | ./bin/lab status |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Target có healthy? | Target group → Targets | Health status, reason |
| Health check dùng gì? | Target group → Health checks | path, port, matcher |
| App có trả 200? | curl /health | HTTP status |
| SG có mở 8080? | EC2 → Security groups | Inbound từ ALB SG |

### Trước khi phá, bạn phải trả lời 3 câu

1. 503 khác 502 và 504 ở đâu?
2. Target healthy cần những điều kiện gì?
3. Nếu app vẫn chạy mà ALB 503, bạn xem gì trước?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 05 --live` và `./bin/lab teach 05`.

## 6. Hiện tượng bạn sẽ thấy

Trình duyệt/curl nhận 503. Target có thể vẫn `running` nhưng `unhealthy`.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Target có healthy không? | `aws elbv2 describe-target-health` |
| Lý do unhealthy? | Target health reason: `Target.FailedHealthChecks`, timeout, port... |
| Health check path/port? | Target Group → Health checks |
| App có nghe đúng port? | SSM: `ss -lntp | grep 8080` |

## 8. Thành công trông như thế nào?

`verify 05` PASS: health check path `/health`, target healthy, `curl /health` = 200.

Nếu FAIL, đọc:

```bash
cat labs/05-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- 503 do ALB không có healthy target; 502 do target trả lỗi; 504 do timeout.
- Health check interval × unhealthy threshold quyết định thời gian chuyển unhealthy.
- SG của target phải cho phép ALB SG trên đúng port.

## 10. Note mẫu

- 1. 503 hay 502/504?
- 2. Target health reason là gì?
- 3. Health check dùng path/port nào?

## 11. Cleanup

```bash
./bin/lab down 05
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
./bin/lab hint 05
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 05. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
