# LAB 12 — Event-driven remediation: EC2 stopped → Lambda start

```text
LAB: 12 — Event-driven remediation: EC2 stopped → Lambda start
SERVICE: EventBridge rule soa-c03-lab12-remediate · Lambda soa-c03-lab12-remediate (python3.12)
         · SQS soa-c03-lab12-events · canary EC2 i-0c75b3c98bb889039 (t4g.nano)
DATE: 2026-11-02
DOMAIN: D3 Automation 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] (không cần sửa) Verify [x] Cleanup [ ]
SOLUTION_USED: yes (note do AI viết hộ theo yêu cầu "viết hộ tôi")
```

1. What did I build?

| Thành phần | Tên thật | Trạng thái khoẻ |
|---|---|---|
| Lambda | `soa-c03-lab12-remediate` (python3.12, Active) | được rule gọi, chạy xong |
| EventBridge rule | `soa-c03-lab12-remediate` (ENABLED) | pattern khớp event |
| SQS | `soa-c03-lab12-events` | nhận event |
| Canary EC2 | `i-0c75b3c98bb889039` (t4g.nano) | running, tag `auto-remediate=true` |

Event pattern của rule:

```json
{"source":["aws.ec2"],
 "detail-type":["EC2 Instance State-change Notification"],
 "detail":{"state":["stopped"]}}
```

Rule có **2 target**: Lambda (để start lại) và SQS (để lưu/thông báo event).

2. What failed? (symptom, not root cause)

Canary bị **stop** lúc `09:04:59Z`. Nhưng khi mở EC2 console thì nó **đang running** — vì hệ thống đã
tự start lại trước khi mình kịp xem.

Đây là bẫy của lab này: **trạng thái hiện tại "running" che mất sự kiện đã xảy ra**. Nếu chỉ nhìn
`Instance state` thì không thấy gì bất thường; phải đọc **dòng thời gian** (log, event, SQS).

3. How did I detect it? (metric/log/event/CLI)

Ba bằng chứng, đúng 3 mắt của chuỗi:

- **EC2**: `i-0c75b3c98bb889039` `running`, `LaunchTime = 09:05:22Z` → muộn hơn mốc stop 09:04:59Z.
- **CloudWatch Logs** `/aws/lambda/soa-c03-lab12-remediate`, stream
  `2026/11/02/[$LATEST]ed24b13264864430b22e252e0c0b36b1`:

  ```text
  09:05:20.978Z  INIT_START Runtime Version: python:3.12
  09:05:22.862Z  started i-0c75b3c98bb889039
  09:05:22.871Z  END RequestId: e3aee2a2-4abf-49da-853d-5a803487a7b6  Duration: 1342.92 ms
  ```

- **SQS** `soa-c03-lab12-events`: 1 message là **event gốc**:
  `{"detail-type":"EC2 Instance State-change Notification","source":"aws.ec2","time":"2026-11-02T09:05:20Z","detail":{"instance-id":"i-0c75b3c98bb889039","state":"stopped"}}`

4. Root cause (the actual broken layer)

**Không có lớp nào hỏng.** Chuỗi remediation chạy đúng hoàn toàn:

```text
09:04:59Z  canary bị stop
09:05:20Z  EventBridge giao event (SQS nhận cùng event)
09:05:22Z  Lambda "started i-0c75b3c98bb889039" (1342 ms)
09:05:22Z  canary running lại — tổng 23 giây
```

Kết luận đúng của một ca như thế này là **"hệ thống hoạt động như thiết kế, đây là bằng chứng"** —
không phải ca nào cũng có root cause để sửa. Ghi sai thành "tôi đã sửa X" là làm hỏng evidence.

5. How did I fix it? (exact command or console action)

**Không sửa gì.** Chỉ xác minh:

```bash
./bin/lab verify 12
# OK  canary=running lambda=started event=delivered
# PASS 2026-11-02T09:12:52Z
```

6. Prevention / automation

- **2 loại quyền, 2 nơi khác nhau** (bẫy lớn nhất):
  - *resource-based policy* **trên Lambda**: cho `events.amazonaws.com` được **gọi** function;
  - *execution role* của Lambda: cho code **làm** `ec2:StartInstances`, `sqs:SendMessage`.
  Thiếu cái đầu → Lambda **không chạy lần nào** (log trống). Thiếu cái sau → chạy nhưng **lỗi giữa chừng**.
- **Idempotent**: EventBridge/Lambda là *at-least-once*, cùng event có thể tới 2 lần. Code phải kiểm
  trạng thái trước khi start và kiểm tag `auto-remediate=true`, để lần 2 không gây lỗi hay gửi trùng.
- **Guardrail phát hiện**: alarm trên `Invocations = 0` khi có event (rule không match), và alarm khi
  canary `stopped` quá 2 phút (remediation thất bại). Không có 2 alarm này thì hệ thống im lặng khi hỏng.
- **Đừng `Poll for messages` trên console** khi còn phải verify: nó ẩn message theo visibility timeout.
  Dùng `aws sqs receive-message --visibility-timeout 0` để đọc mà không giấu message.

7. Exam trap

- Rule gọi Lambda cần **resource-based policy** với principal `events.amazonaws.com` (+ `SourceArn`);
  **execution role không thay thế được** quyền này.
- Event pattern so khớp theo `source` + `detail-type` + `detail.*`; sai một field là `Invocations = 0`.
- `Invocations` / `Failed invocations` trễ **1–2 phút** — vừa bấm xong mà thấy 0 thì chưa kết luận được.
- Remediation tự động phải **idempotent** và **có giới hạn** (chỉ máy có tag), nếu không sẽ start cả
  những instance bị stop có chủ đích.
- Trạng thái cuối "running" **không** chứng minh là chưa từng bị stop — phải đọc log/event.
