# Lab 09 — SSM Session Manager, Run Command, Parameter Store

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D3 Automation 22% |
| Thời gian | ~120 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Thấp |
| Lab ID | `09` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học vận hành EC2 không cần SSH, không public IP: vào máy bằng Session Manager, chạy lệnh bằng Run Command, đọc config bằng Parameter Store.
- **Việc đầu tiên:** Ô **Search** → `Systems Manager` → menu trái **Fleet Manager**.
- **Xong khi:** `verify 09` PASS: service `active`, `/health` 200, parameter đúng giá trị.
- **Nếu lạc:** `./bin/lab console 09` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học vận hành EC2 không cần SSH, không public IP: vào máy bằng Session Manager, chạy lệnh bằng Run Command, đọc config bằng Parameter Store.

## 2. Hiện tại có gì?

App stack chạy, SSM agent online. Lab tạo một parameter `/soa-c03/lab09/message`; `break 09` stop app service từ xa.

## 3. Kiến trúc

```text
Bạn → SSM
        ├── Session Manager → shell trên EC2
        ├── Run Command → chạy lệnh hàng loạt
        └── Parameter Store → config
EC2 → SSM agent → IAM role → SSM endpoint
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/09-*/README.md` (file này) và dòng lab `09` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 09
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 09
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 09
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 09
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 09
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 09
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
| SSM Agent | Bot trên EC2 nói chuyện với Systems Manager. |
| Fleet Manager | Màn hình quản lý instance và trạng thái agent. |
| Run Command | Chạy script trên nhiều instance, có lịch sử output. |
| Session Manager | Shell từ xa không cần SSH hay public IP. |
| Parameter Store | Kho key/value cho cấu hình. |
| Instance profile | Thẻ IAM gắn vào EC2. |

### Khái niệm của lab này

- **SSM Agent** là con bot chạy trên EC2, kết nối ra ngoài tới Systems Manager.
- **Run Command** chạy lệnh hàng loạt không cần SSH; **Session Manager** mở shell tương tác; **Parameter Store** lưu cấu hình.
- Cả ba cần IAM role đúng và đường mạng ra endpoint SSM.

### Đường bấm từng bước

1. Ô **Search** → `Systems Manager` → menu trái **Fleet Manager**.
2. Tìm instance đang chạy (lấy ID bằng `./bin/lab status`); cột **Ping status** phải là **Online**.
3. Menu trái **Run Command** → **Run a command**.
4. Command document: `AWS-RunShellScript`; **Command parameters**: `commands` = `systemctl is-active cloudops-app`.
5. **Targets** → **Choose instances manually** → tick instance → **Run**.
6. Ở **Command history**, bấm command vừa chạy → đọc **Output** và **Status**.
7. Menu trái **Session Manager** → **Start session** → chọn instance → mở terminal.
8. Menu trái **Parameter Store** → search `/soa-c03/lab09/message` → bấm để xem **Value**.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Ping status | `Online` mới điều khiển được; `ConnectionLost` là agent/mạng/role. |
| Command Status | `Success`, `Failed`, `TimedOut`. |
| Command output | Kết quả thật của lệnh, không phải suy đoán. |
| Parameter value | Phải khớp giá trị lab tạo. |
| Session | Nếu mở được shell, chứng minh agent + role + endpoint đều đúng. |
| App service | `active` và `/health` 200 là tiêu chí cuối. |

### Link nhanh

- [Fleet Manager](https://console.aws.amazon.com/systems-manager/managed-instances?region=ap-southeast-1)
- [Run Command](https://console.aws.amazon.com/systems-manager/run-command/execute-command?region=ap-southeast-1)
- [Session Manager](https://console.aws.amazon.com/systems-manager/session-manager/start-session?region=ap-southeast-1)
- [Parameter Store](https://console.aws.amazon.com/systems-manager/parameters/?region=ap-southeast-1)

### Nếu không thấy mục đó

- Instance không xuất hiện trong Fleet Manager: agent chưa chạy, instance profile thiếu quyền, hoặc không có đường ra `ssm.ap-southeast-1.amazonaws.com`.
- Run Command `Failed`: bấm command → **Output** đọc stderr; đừng đoán.
- Session Manager báo lỗi: kiểm tra IAM role có `ssm:StartSession` và instance có agent mới.
- Private subnet không NAT cần interface endpoint cho `ssm`, `ssmmessages`, `ec2messages`.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học vận hành EC2 không SSH: Session Manager, Run Command, Parameter Store.

### Bạn cần biết 4 khái niệm

- **SSM Agent**: Bot trên EC2 nói chuyện với Systems Manager.
- **Run Command**: Chạy script từ xa, có lịch sử output.
- **Session Manager**: Shell từ xa không cần SSH/public IP.
- **Parameter Store**: Kho key/value cho cấu hình.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Instance | instance trong ASG | SSM Online | Systems Manager → Fleet Manager |
| Service | cloudops-app | active | Run Command: systemctl is-active |
| Parameter | /soa-c03/lab09/message | hello-from-parameter-store | Parameter Store |
| App | soa-c03-app | /health 200 | ./bin/lab status |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Agent online? | Fleet Manager | Ping status |
| Service chạy? | Run Command | Status, Output |
| Vào shell được? | Session Manager | terminal |
| Parameter đúng? | Parameter Store | Value |

### Trước khi phá, bạn phải trả lời 3 câu

1. Không SSH thì vào máy bằng gì?
2. Run Command khác Session Manager ở đâu?
3. Nếu agent offline, bạn kiểm tra gì trước?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 09 --live` và `./bin/lab teach 09`.

## 6. Hiện tượng bạn sẽ thấy

App service bị stop từ xa. Bạn không SSH; mọi thứ đi qua SSM.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Agent có online không? | `aws ssm describe-instance-information` |
| Service có chạy không? | Run Command: `systemctl is-active cloudops-app` |
| Parameter có đúng không? | `aws ssm get-parameter --name /soa-c03/lab09/message` |
| App có health không? | `curl http://<alb>/health` |

## 8. Thành công trông như thế nào?

`verify 09` PASS: service `active`, `/health` 200, parameter đúng giá trị.

Nếu FAIL, đọc:

```bash
cat labs/09-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Session Manager vs Run Command vs Automation.
- SSM cần IAM role + outbound 443; private subnet cần interface endpoint.
- Parameter Store vs Secrets Manager.

## 10. Note mẫu

- 1. Không SSH thì vào máy bằng gì?
- 2. Agent thiếu quyền sẽ thế nào?
- 3. Parameter Store lưu secret có an toàn không?

## 11. Cleanup

```bash
./bin/lab down 09
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
./bin/lab hint 09
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 09. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
