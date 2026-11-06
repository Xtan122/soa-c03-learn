# LAB 18 — ECS Fargate + Container Insights + ECR

```text
LAB: 18 — ECS Fargate + Container Insights + ECR
SERVICE: ECS Fargate (service soa-c03-lab18-web, desired 1 task)
DATE: 2026-11-05
DOMAIN: D3 Automation 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [x]
```

## 1. What did I build?

- **ECS cluster** `soa-c03-lab18` (Container Insights = enabled).
- **Task definition** `soa-c03-lab18:1`: Fargate, **0.25 vCPU / 0.5 GB**,
  image `public.ecr.aws/nginx/nginx:latest`, log driver `awslogs` →
  `/aws/ecs/soa-c03/lab18`.
- **Service** `soa-c03-lab18-web`, **desired = 1**, launch type Fargate,
  network `awsvpc` trong subnet public, `assignPublicIp=ENABLED`.
- **Execution role** `soa-c03-lab18-exec` + `AmazonECSTaskExecutionRolePolicy`
  (quyền ECS agent pull image từ ECR và ghi log CloudWatch).
- **ECR repository** `soa-c03-lab18-nginx` (rỗng — lab chỉ xem cấu trúc +
  lifecycle policy).
- **Security group** `soa-c03-lab18-ecs` (mở TCP 80 cho client).

Baseline khoẻ: task `3aa5a3ce9337475dadf2e379f0e0f048` RUNNING,
public IP `18.143.173.184`, `http://18.143.173.184` = **200**.

## 2. What failed? (symptom, not root cause)

- Task đang chạy bị **STOPPED đột ngột**.
- Client dùng **IP cũ** `18.143.173.184` → **timeout** (không phải 5xx).
- Khoảng **44 giây** sau, một task mới xuất hiện với **IP khác**
  (`56.10.139.29`) và trả **200** — service **không hề báo lỗi**.

## 3. How did I detect it? (metric/log/event/CLI)

| Bằng chứng | Nơi đọc | Giá trị thật |
|---|---|---|
| Số task | ECS → service → **Tasks** | 2 task: 1 `Running`, 1 `Stopped` |
| Task cũ | Task → **Configuration** | STOPPED `2026-11-05T16:27:43.071Z`, **exit code 0**, chạy 11m24s |
| Log cuối task cũ | Service → **Logs** | nginx shutdown êm: `signal 17 (SIGCHLD)`, `worker process exited with code 0`; không có error/stack trace |
| Service quyết định gì | Service → **Events** | `23:27 has started 1 tasks: 1002e12e…` → `23:28 reached a steady state` |
| Ai gọi lệnh dừng | **CloudTrail → Event history** | `StopTask` @ `23:27:08 (+07)`, `IAMUser xtan`, `eventSource=ecs.amazonaws.com`, `sourceIP=42.118.52.197`, `readOnly=false` |
| Địa chỉ truy cập | `curl` | IP cũ `18.143.173.184` = **000/timeout**; IP mới `56.10.139.29` = **200** |
| Container Insights | Service → **Health and metrics** | CPU ~0.27%, Memory ~0.59% (metric trễ vài phút sau khi tạo cluster) |

## 4. Root cause (the actual broken layer)

**Không phải app.** Một **lệnh API `ecs:StopTask` từ bên ngoài** (IAM user
`xtan`) dừng task đang chạy:

- App không crash: `exit code 0` + log nginx đóng êm ⇒ bị **SIGTERM**, không
  phải lỗi code/OOM.
- **ECS service** (desired = 1) tự tạo task mới ⇒ đây là **self-healing**, không
  phải "app tự khỏi".
- Vì lab **không có ALB/DNS** trước task, client gõ thẳng IP ⇒ task mới = **ENI
  mới = IP mới**, nên **IP cũ chết**. Đây là tác hại thật của sự cố: *địa chỉ
  truy cập không ổn định*.

## 5. How did I fix it? (exact command or console action)

**Không sửa gì** — không đổi code, image, CPU, memory hay task definition
(vẫn `:1`). Việc cần làm là **chứng minh** service đã tự chữa:

```bash
./bin/lab verify 18
# OK service running=1 task=56.10.139.29 http=200
```

## 6. Prevention / automation

- **IAM least privilege**: hạn chế ai được gọi `ecs:StopTask`
  (đây là bề mặt tấn công thật của sự cố này).
- **CloudTrail + metric filter/alarm** trên `StopTask`, hoặc alarm
  `RunningTaskCount < DesiredCount` để biết ngay khi task biến mất.
- Đặt **ALB/NLB** (hoặc ECS Service Discovery / Cloud Map) trước service để
  client dùng **DNS ổn định**, không hardcode IP ephemeral.
- Giữ `desired count` + bật **deployment circuit breaker** và health check.
- **Container Insights** + alarm CPU/memory để thấy bất thường sớm.

## 7. Exam trap

- **Task ≠ service**: task là một lần chạy (ephemeral, IP đổi); service là bộ
  giữ đúng `desired count` và **thay task hỏng**.
- `exit code 0` + log đóng êm ⇒ **bị dừng từ ngoài**, không phải crash.
- `Stopped reason` chỉ là **chuỗi người gọi truyền vào**; muốn biết **ai** phải
  đọc **CloudTrail** (`StopTask`).
- **Execution role** (ECS agent: pull image + ghi log) **khác task role**
  (quyền cho code trong container).
- `describe-clusters` phải có `--include SETTINGS` mới thấy Container Insights;
  metric CI **trễ vài phút** sau khi bật.
- Fargate không có "server để SSH": muốn vào container phải dùng
  `ecs execute-command` (cần SSM + task role).

## Chưa làm

- Chưa push image riêng lên ECR (lab dùng public image).
- Chưa thử `ecs execute-command`, task role riêng, service auto scaling.
- Chưa dựng ALB trước ECS (đó là lab 22/23 — production capstone).
