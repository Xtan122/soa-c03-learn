# Lab 06 — ASG scale-out thất bại

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D2 Reliability 22% |
| Thời gian | ~150 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Thấp |
| Lab ID | `06` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học vì sao ASG không scale được: launch template, user-data, security group, subnet, health check. Đây là lỗi rất hay gặp khi vận hành.
- **Việc đầu tiên:** Ô **Search** → `EC2` → **Auto Scaling Groups** → bấm `soa-c03-asg`.
- **Xong khi:** `verify 06` PASS: desired 2, 2 target healthy, launch template về version gốc, có ít nhất 1 bằng chứng scale-out thất bại (scaling activity `Failed`, hoặc instance bị thay vì không qua ELB health check).
- **Nếu lạc:** `./bin/lab console 06` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học vì sao ASG không scale được: launch template, user-data, security group, subnet, health check. Đây là lỗi rất hay gặp khi vận hành.

## 2. Hiện tại có gì?

App stack chạy với 1 instance. Lab tạo một launch template version có user-data lỗi, đưa ASG dùng version đó, rồi tăng desired capacity lên 2.

## 3. Kiến trúc

```text
ALB → Target Group → ASG (desired 1)
                         │ scale out
                         ▼
                 Launch Template (bad user-data)
                         ▼
                 Instance mới không healthy
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/06-*/README.md` (file này) và dòng lab `06` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 06
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 06
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 06
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 06
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 06
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 06
   ```

## 5b. Ghi chú / lệnh riêng

Sau khi sửa, nhớ đưa ASG về launch template version gốc và desired 1 nếu không làm tiếp lab scale.

Trong lúc làm bài, lab tạm `suspend-processes AlarmNotification` của ASG để policy CPU TargetTracking không kéo desired về 1 sau ~9 phút. Đây là **chủ ý của lab**, không phải lỗi; `./bin/lab down 06` sẽ `resume-processes` lại.

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
| Launch template | Bản thiết kế EC2: AMI, instance type, user-data, SG. |
| Version | Một bản snapshot của template; `$Latest` là bản mới nhất. |
| Desired capacity | Số instance ASG muốn có. |
| Scaling activity | Nhật ký ASG thử thêm/bớt máy và kết quả. |
| Health check type | ASG kiểm tra EC2 hay kiểm tra qua ELB. |
| Cooldown | Thời gian ASG chờ trước khi scale tiếp. |

### Khái niệm của lab này

- **Launch template** là bản thiết kế máy; **version** là từng bản sửa.
- ASG có thể dùng một version cụ thể hoặc `$Latest`.
- Mỗi lần ASG muốn thêm máy, nó gọi template; nếu template hỏng (user-data lỗi), máy có thể vẫn `running` nhưng app không chạy, và **scaling activity** ghi lại lý do.

### Đường bấm từng bước

1. Ô **Search** → `EC2` → **Auto Scaling Groups** → bấm `soa-c03-asg`.
2. Tab **Details**: đọc **Desired capacity**, **Min/Max**, **Launch template** (tên + version).
3. Tab **Activity**: đọc các dòng mới nhất, cột **Status** và **Status message**.
4. Tab **Instance management**: xem instance nào đang InService.
5. Menu trái **Launch templates** → bấm `soa-c03-app` → tab **Versions**.
6. Bấm version mới nhất → tab **Launch template contents** → mở **User data** và so với version gốc.
7. Menu trái **Instances** → search instance mới → tab **Status checks**, **Monitoring**, **Tags**.
8. Target group `soa-c03-tg` → **Targets** → xem instance mới có healthy không.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Desired capacity | 2 nghĩa là ASG đang cố tạo thêm một máy. |
| Launch template version | Nếu là `$Latest` hoặc version mới, đó là bản đang được dùng. |
| Scaling activity Status | `Failed`, `Successful`, `InProgress`. |
| Status message | Nói lý do: hết capacity, user-data lỗi, không qua health check... |
| Instance status checks | `2/2 checks passed` mới là máy khoẻ. |
| User data | Script chạy lần đầu; lỗi ở đây làm app không start. |

### Link nhanh

- [Auto Scaling groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#AutoScalingGroups:)
- [Launch templates](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#LaunchTemplates:)
- [Instances](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#Instances:)
- [Target groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#TargetGroups:)

### Nếu không thấy mục đó

- Activity trống: ASG chưa thực sự scale; kiểm tra **Desired** và suspended processes.
- Instance mới `running` nhưng target `unhealthy`: đọc user-data và `/var/log/cloudops-bootstrap.log` qua SSM.
- Đừng sửa template gốc; tạo version mới rồi trỏ ASG về version đúng.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học vì sao ASG scale out thất bại: launch template, user-data, health check, desired capacity.

### Bạn cần biết 4 khái niệm

- **Launch template**: Bản thiết kế EC2: AMI, instance type, user-data, SG.
- **Version**: Một bản sửa của template; $Latest là bản mới nhất.
- **Desired capacity**: Số instance ASG muốn có.
- **Scaling activity**: Nhật ký ASG thử thêm/bớt máy.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| ASG | soa-c03-asg | desired 1, 1 healthy | EC2 → Auto Scaling groups |
| Launch template | soa-c03-app | version gốc | EC2 → Launch templates |
| Instance | 1 instance InService | running, 2/2 checks | EC2 → Instances |
| Target group | soa-c03-tg | 1 healthy | EC2 → Target groups |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| ASG đang dùng version nào? | ASG → Details | Launch template name/version |
| Scale có thành công? | ASG → Activity | Status, Status message |
| Instance mới khoẻ? | EC2 → Status checks | 2/2 checks |
| App boot lỗi? | SSM → Run Command | /var/log/cloudops-bootstrap.log |

### Trước khi phá, bạn phải trả lời 3 câu

1. ASG hiện có desired bao nhiêu?
2. Nếu instance mới không qua health check, target group thấy gì?
3. Bạn xem Activity hay Launch template trước? Vì sao?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 06 --live` và `./bin/lab teach 06`.

## 6. Hiện tượng bạn sẽ thấy

ASG nhận desired 2 nhưng instance mới không vào được target; Scaling Activity có thể báo `Failed`.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| ASG đang dùng launch template version nào? | ASG → Launch template |
| Scaling activity nói gì? | `aws autoscaling describe-scaling-activities` |
| Instance mới có health check không? | EC2 status + target health |
| User-data có lỗi không? | SSM: `/var/log/cloudops-bootstrap.log` |

## 8. Thành công trông như thế nào?

`verify 06` PASS: desired 2, 2 target healthy, launch template về version gốc, có ít nhất 1 bằng chứng scale-out thất bại (scaling activity `Failed`, hoặc instance bị thay vì không qua ELB health check).

Nếu FAIL, đọc:

```bash
cat labs/06-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Health check type `ELB` vs `EC2`.
- Launch template version và `$Latest`.
- Cooldown, warmup, termination policy.

## 10. Note mẫu

- 1. ASG có launch được instance không?
- 2. Instance có healthy không?
- 3. Lỗi nằm ở template, user-data, SG hay subnet?

## 11. Cleanup

```bash
./bin/lab down 06
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
./bin/lab hint 06
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 06. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
