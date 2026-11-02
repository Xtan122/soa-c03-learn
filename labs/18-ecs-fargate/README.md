# Lab 18 — ECS Fargate + Container Insights + ECR

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D3 Automation 22% |
| Thời gian | ~180 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Trung bình |
| Lab ID | `18` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học container cơ bản: task vs service, Fargate, execution role, logs, ECR, Container Insights. Đây là phần mới của SOA-C03.
- **Việc đầu tiên:** Ô **Search** → `ECS` → **Clusters** → `soa-c03-lab18`.
- **Xong khi:** `verify 18` PASS: service running 1, task HTTP 200.
- **Nếu lạc:** `./bin/lab console 18` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học container cơ bản: task vs service, Fargate, execution role, logs, ECR, Container Insights. Đây là phần mới của SOA-C03.

## 2. Hiện tại có gì?

App stack chạy. Lab tạo ECS cluster, service Fargate chạy nginx public image, ECR repo, log group, Container Insights.

## 3. Kiến trúc

```text
Internet → Fargate task (nginx :80)
                 │
                 ├── awslogs → CloudWatch
                 └── Container Insights → ECS metrics
ECR repo (image registry)
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/18-*/README.md` (file này) và dòng lab `18` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 18
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 18
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 18
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 18
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 18
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 18
   ```

## 5b. Ghi chú / lệnh riêng

Image dùng `public.ecr.aws/nginx/nginx:latest`; nếu public registry bị chặn, push image lên ECR.

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
| Task definition | Bản thiết kế container: image, CPU, memory, log. |
| Task | Một container đang chạy. |
| Service | Bộ quản lý giữ số task đúng desired count. |
| Fargate | Chạy container không cần quản lý EC2. |
| Execution role | Role để ECS agent pull image/ghi log. |
| Container Insights | Metric/log nâng cao cho cluster. |

### Khái niệm của lab này

- **Task definition** là bản thiết kế container; **task** là một lần chạy; **service** giữ số task luôn đủ.
- Fargate cần **execution role** để pull image và ghi log.
- **Container Insights** là metric bổ sung ở cluster, có thể trễ vài phút.

### Đường bấm từng bước

1. Ô **Search** → `ECS` → **Clusters** → `soa-c03-lab18`.
2. Tab **Services** → bấm `soa-c03-lab18-web`.
3. Tab **Health** / **Events**: đọc deployment events và lý do task bị thay.
4. Tab **Tasks** → bấm task đang chạy → **Configuration**: xem **Last status**, **Stopped reason**.
5. Tab **Logs** của task → mở stream để đọc log nginx.
6. Tab **Monitoring** → xem Container Insights (CPU/memory) — có thể trễ.
7. Task **Networking** → lấy **Public IP** → mở `http://<ip>` trên browser.
8. Ô **Search** → `ECR` → **Repositories** → `soa-c03-lab18-nginx` → xem lifecycle policy.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Running / Desired count | Service phải giữ 1 task running. |
| Deployment events | Nói vì sao task bị stop và service có stabilize không. |
| Stopped reason | `Essential container exited`, image pull error, OOM... |
| Container log | Lỗi thật từ bên trong container. |
| Public IP + HTTP | `200` chứng minh task phục vụ được. |
| Execution role | Thiếu quyền pull/ghi log thì task không start. |

### Link nhanh

- [ECS cluster `soa-c03-lab18`](https://console.aws.amazon.com/ecs/v2/clusters/soa-c03-lab18/services?region=ap-southeast-1)
- [ECS service](https://console.aws.amazon.com/ecs/v2/clusters/soa-c03-lab18/services/soa-c03-lab18-web/health?region=ap-southeast-1)
- [CloudWatch log group](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#logsV2:log-groups/log-group/%2Faws%2Fecs%2Fsoa-c03%2Flab18)
- [ECR repositories](https://console.aws.amazon.com/ecr/repositories?region=ap-southeast-1)

### Nếu không thấy mục đó

- Task `STOPPED` ngay: đọc **Stopped reason** và log, thường là image pull hoặc execution role.
- Service không stabilize: xem **Events**; có thể subnet không public IP hoặc SG thiếu egress.
- Container Insights trống: mới bật, chờ vài phút.
- `public.ecr.aws` bị chặn: push image lên ECR rồi sửa task definition.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học container cơ bản: task definition, task, service, Fargate, execution role, logs, ECR.

### Bạn cần biết 4 khái niệm

- **Task definition**: Bản thiết kế container: image, CPU, memory, log.
- **Task**: Một container đang chạy.
- **Service**: Bộ quản lý giữ số task đúng desired count.
- **Execution role**: Role để ECS pull image và ghi log.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Cluster | soa-c03-lab18 | Active | ECS → Clusters |
| Service | soa-c03-lab18-web | running 1 | ECS → cluster → Services |
| Task definition | soa-c03-lab18 | ACTIVE | ECS → Task definitions |
| Log group | /aws/ecs/soa-c03/lab18 | tồn tại | CloudWatch → Log groups |
| ECR | soa-c03-lab18-nginx | tồn tại | ECR → Repositories |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Service khoẻ? | ECS → Service → Health | running/desired |
| Task stop lý do? | ECS → Tasks → Configuration | Stopped reason |
| Log nói gì? | CloudWatch log group | nginx log |
| HTTP được không? | curl task public IP | 200 |
| Execution role? | IAM / task definition | quyền pull+log |

### Trước khi phá, bạn phải trả lời 3 câu

1. Task khác service ở đâu?
2. Fargate cần role nào để pull image?
3. Nếu task stop, service làm gì?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 18 --live` và `./bin/lab teach 18`.

## 6. Hiện tượng bạn sẽ thấy

Task bị stop. ECS service phải tự tạo task mới; bạn kiểm tra service events và task stopped reason.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Service running count? | `aws ecs describe-services` |
| Task stop reason? | `aws ecs describe-tasks` |
| Container log nói gì? | `aws logs tail /aws/ecs/soa-c03/lab18` |
| Task có public IP và HTTP 200? | `curl http://<task-public-ip>` |

## 8. Thành công trông như thế nào?

`verify 18` PASS: service running 1, task HTTP 200.

Nếu FAIL, đọc:

```bash
cat labs/18-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Task definition vs service vs task.
- Fargate cần execution role để pull image/ghi log.
- Container Insights cần bật ở cluster; metric có thể trễ.

## 10. Note mẫu

- 1. Task có chạy không?
- 2. Nếu stop, lý do là gì?
- 3. Service khác task ở đâu?

## 11. Cleanup

```bash
./bin/lab down 18
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
./bin/lab hint 18
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 18. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
