# Lab 22 — Production capstone: self-healing + backup

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | All domains |
| Thời gian | ~240 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Trung bình |
| Lab ID | `22` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Bài tổng hợp production-like: chứng minh ASG tự thay instance khi app chết, backup plan tồn tại, dashboard/alarm đủ, app vẫn phục vụ.
- **Việc đầu tiên:** Ô **Search** → `EC2` → **Auto Scaling Groups** → `soa-c03-asg` → tab **Activity**: tìm launch/terminate gần đây.
- **Xong khi:** `verify 22` PASS: instance mới, `/health`/`/db` 200, target healthy, backup plan/dashboard/alarms tồn tại.
- **Nếu lạc:** `./bin/lab console 22` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Bài tổng hợp production-like: chứng minh ASG tự thay instance khi app chết, backup plan tồn tại, dashboard/alarm đủ, app vẫn phục vụ.

## 2. Hiện tại có gì?

App stack chạy, dashboard và alarm đã có. `up 22` tạo backup plan/vault cho RDS. `break 22` stop app service để ASG tự thay instance.

## 3. Kiến trúc

```text
ALB → ASG → EC2 app
          │  app service stopped
          ▼
     target unhealthy → ASG thay instance
RDS ← backup plan/vault
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/22-*/README.md` (file này) và dòng lab `22` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 22
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 22
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 22
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 22
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 22
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 22
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
| Self-healing | Hệ thống tự thay thành phần hỏng. |
| Health check grace | Thời gian ASG chờ app khởi động trước khi đánh unhealthy. |
| Recovery point | Một bản backup. |
| Dashboard | Một trang gom metric/log quan trọng. |
| Runbook | Các bước xử lý khi sự cố. |

### Khái niệm của lab này

- **Self-healing** dựa vào health check của ALB + ASG thay instance khi target unhealthy.
- **Backup plan** chỉ có giá trị khi có recovery point và đã test restore.
- Production readiness = observability (dashboard/alarm) + HA + backup + runbook.

### Đường bấm từng bước

1. Ô **Search** → `EC2` → **Auto Scaling Groups** → `soa-c03-asg` → tab **Activity**: tìm launch/terminate gần đây.
2. Tab **Instance management**: so instance ID với lúc bắt đầu break.
3. **EC2** → **Instances** → instance mới → **Launch time**, **Status checks**.
4. **EC2** → **Target groups** → `soa-c03-tg` → **Targets**: healthy.
5. **CloudWatch** → **Dashboards** → `soa-c03-ops`: xem các widget.
6. **CloudWatch** → **Alarms** → filter `soa-c03`: đếm số alarm.
7. **AWS Backup** → **Backup plans** → `soa-c03-lab22`; **Vaults** → `soa-c03-lab22`.
8. Terminal: `curl -i http://<alb>/health` và `/db`.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| ASG Activity | Có `Terminating` instance cũ và `Launching` instance mới không. |
| Instance ID trước/sau | Khác nhau chứng minh đã thay, không chỉ restart service. |
| Target health | Instance mới phải healthy. |
| Dashboard widgets | Có metric ALB/EC2/RDS/log. |
| Số alarm | Lab yêu cầu ít nhất 4 alarm prefix `soa-c03`. |
| Backup plan + vault | Phải tồn tại; recovery point có thể chưa có ngay. |

### Link nhanh

- [Auto Scaling groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#AutoScalingGroups:)
- [CloudWatch dashboard](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#dashboards:name=soa-c03-ops)
- [CloudWatch alarms](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#alarmsV2:alarms)
- [AWS Backup plans](https://console.aws.amazon.com/backup/home?region=ap-southeast-1#backup/plans)

### Nếu không thấy mục đó

- Instance chưa bị thay: health check grace có thể tới 10 phút; xem **Activity**.
- Instance mới nhưng app chưa lên: đọc `/var/log/cloudops-bootstrap.log` qua SSM.
- Dashboard trống: chạy `make dash` (cần app stack).
- Backup plan có nhưng chưa có recovery point: chờ job hoặc chạy on-demand job.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Production capstone: chứng minh ASG tự thay instance khi app chết, backup plan tồn tại, dashboard/alarm đủ.

### Bạn cần biết 4 khái niệm

- **Self-healing**: Hệ thống tự thay thành phần hỏng.
- **Health check grace**: Thời gian ASG chờ app khởi động.
- **Recovery point**: Một bản backup.
- **Production readiness**: Observability + HA + backup + runbook.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| ASG | soa-c03-asg | desired 1, healthy | EC2 → Auto Scaling groups |
| Dashboard | soa-c03-ops | tồn tại | CloudWatch → Dashboards |
| Alarms | soa-c03-lab22-* | 4 alarm | CloudWatch → Alarms |
| Backup plan | soa-c03-lab22 | tồn tại | AWS Backup → Plans |
| App | soa-c03-app | /health 200, /db 200 | ./bin/lab status |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| ASG thay instance? | ASG → Activity | launch/terminate |
| Target healthy? | Target group → Targets | healthy |
| App/DB? | curl /health /db | 200 |
| Dashboard? | CloudWatch → Dashboards | widgets |
| Alarm đủ? | CloudWatch → Alarms | số alarm |
| Backup? | AWS Backup | plan, vault |

### Trước khi phá, bạn phải trả lời 3 câu

1. ASG biết app chết bằng gì?
2. Instance mới khác instance cũ ở đâu?
3. Backup plan đã test restore chưa?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 22 --live` và `./bin/lab teach 22`.

## 6. Hiện tượng bạn sẽ thấy

App service bị stop. Bạn phải thấy instance mới được tạo, target healthy trở lại, app 200.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| ASG có thay instance không? | `describe-scaling-activities`, instance ID trước/sau |
| Target healthy chưa? | `describe-target-health` |
| App và DB ổn chưa? | `/health`, `/db` |
| Backup plan/dashboard/alarm có đủ? | `aws backup list-backup-plans`, `list-dashboards`, `describe-alarms` |

## 8. Thành công trông như thế nào?

`verify 22` PASS: instance mới, `/health`/`/db` 200, target healthy, backup plan/dashboard/alarms tồn tại.

Nếu FAIL, đọc:

```bash
cat labs/22-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Self-healing dựa vào health check + ASG, không phải reboot tay.
- Backup phải có restore test, không chỉ có plan.
- Production readiness: observability + HA + backup + runbook.

## 10. Note mẫu

- 1. Instance cũ đi đâu?
- 2. ASG biết app chết bằng gì?
- 3. Backup plan đã được test restore chưa?

## 11. Cleanup

```bash
./bin/lab down 22
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
./bin/lab hint 22
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 22. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
