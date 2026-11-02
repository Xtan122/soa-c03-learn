# Lab 11 — CloudFormation update rollback + drift + CDK

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D3 Automation 22% |
| Thời gian | ~150 phút |
| Cần app stack | Không |
| Chi phí | Thấp |
| Lab ID | `11` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học IaC thật: update stack bị lỗi thì CloudFormation rollback thế nào, đọc Stack Events ra sao, drift là gì, CDK synth làm gì.
- **Việc đầu tiên:** Ô **Search** → `CloudFormation` → **Stacks** → bấm `soa-c03-lab11`.
- **Xong khi:** `verify 11` PASS: stack `CREATE_COMPLETE`/`UPDATE_COMPLETE` sau khi bạn sửa template.
- **Nếu lạc:** `./bin/lab console 11` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học IaC thật: update stack bị lỗi thì CloudFormation rollback thế nào, đọc Stack Events ra sao, drift là gì, CDK synth làm gì.

## 2. Hiện tại có gì?

Core stack đủ; không cần app. Lab tạo stack `soa-c03-lab11` gồm SQS, S3 bucket, SSM parameter.

## 3. Kiến trúc

```text
template.yaml
   ├── SQS
   ├── S3 bucket
   └── SSM parameter
        │
        ▼
CloudFormation stack soa-c03-lab11
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Chỉ cần core stack; không cần app stack.

- Đọc `labs/11-*/README.md` (file này) và dòng lab `11` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 11
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 11
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 11
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 11
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 11
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 11
   ```

## 5b. Ghi chú / lệnh riêng

`./bin/lab reset 11` sẽ update lại template gốc. Chỉ dùng sau khi đã đọc Stack Events.

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
| Stack | Một nhóm tài nguyên được quản lý chung. |
| Update rollback | Tự quay về trạng thái trước khi update lỗi. |
| Stack event | Nhật ký từng bước tạo/sửa/xoá resource. |
| Drift | Resource bị sửa ngoài CloudFormation. |
| Change set | Bản nháp cho biết update sẽ thay đổi gì. |

### Khái niệm của lab này

- **Stack** là một tập tài nguyên do CloudFormation quản lý.
- Khi update lỗi, CloudFormation **rollback** về trạng thái trước; **Stack Events** là nơi duy nhất nói chính xác resource nào fail và vì sao.
- **Drift** là khi ai đó sửa tay resource ngoài CloudFormation.

### Đường bấm từng bước

1. Ô **Search** → `CloudFormation` → **Stacks** → bấm `soa-c03-lab11`.
2. Tab **Stack info**: đọc **Status** và **Status reason**.
3. Tab **Events**: danh sách mới nhất ở trên. Tìm event `*_FAILED` **đầu tiên** của lần update (kéo xuống gần cuối nhóm update).
4. Bấm event `*_FAILED` → mở **Resource status reason**; đây là lỗi gốc.
5. Tab **Resources**: xem logical ID, physical ID, status.
6. **Stack actions** → **Detect drift** → chờ → xem cột **Drift status**.
7. (Tuỳ chọn) Terminal: `cd labs/11-cloudformation-cdk/cdk && cdk synth` để xem template sinh ra.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Stack Status | `UPDATE_ROLLBACK_COMPLETE` nghĩa là update lỗi nhưng đã rollback xong. |
| Status reason | Câu lỗi thật, thường ở event `*_FAILED` đầu tiên. |
| Logical ID | Tên resource trong template, dùng để sửa đúng chỗ. |
| Physical ID | Tên thật trên AWS, dùng để tra tiếp. |
| Drift status | `DRIFTED` nghĩa là có người sửa ngoài template. |
| CDK synth | Chỉ tạo template ở máy, không deploy. |

### Link nhanh

- [CloudFormation stacks](https://console.aws.amazon.com/cloudformation/home?region=ap-southeast-1#/stacks)
- [Stack `soa-c03-lab11` events](https://console.aws.amazon.com/cloudformation/home?region=ap-southeast-1#/stacks/events?stackId=soa-c03-lab11)

### Nếu không thấy mục đó

- Không thấy stack: `up 11` chưa chạy; đây là lab không cần app stack.
- `ROLLBACK_COMPLETE` khi **tạo** stack nghĩa là lần tạo đầu lỗi; phải xoá rồi tạo lại, không update tiếp.
- Đừng đọc event cuối cùng; lỗi thật là event `*_FAILED` đầu tiên trong chuỗi.
- Drift chỉ có sau khi bạn sửa tay một resource; lab không tự tạo drift.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học IaC: update stack lỗi thì rollback thế nào, đọc Stack Events, drift là gì.

### Bạn cần biết 4 khái niệm

- **Stack**: Nhóm tài nguyên CloudFormation quản lý.
- **Update rollback**: Tự quay về trạng thái trước khi update lỗi.
- **Stack event**: Nhật ký từng bước tạo/sửa/xoá.
- **Drift**: Resource bị sửa ngoài CloudFormation.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Stack | soa-c03-lab11 | CREATE_COMPLETE | CloudFormation → Stacks |
| SQS | soa-c03-lab11-queue | tồn tại | SQS → Queues |
| S3 | soa-c03-lab11-account-region | tồn tại | S3 → Buckets |
| SSM | /soa-c03/lab11/queue-url | tồn tại | Parameter Store |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Stack status? | CloudFormation → Stack info | Status, reason |
| Lỗi đầu tiên? | CloudFormation → Events | event *_FAILED đầu tiên |
| Resource nào? | CloudFormation → Resources | Logical ID, Physical ID |
| Có drift? | Stack actions → Detect drift | Drift status |

### Trước khi phá, bạn phải trả lời 3 câu

1. ROLLBACK_COMPLETE khác UPDATE_ROLLBACK_COMPLETE ở đâu?
2. Vì sao phải đọc event lỗi đầu tiên, không phải event cuối?
3. Drift khác update lỗi ở đâu?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 11 --live` và `./bin/lab teach 11`.

## 6. Hiện tượng bạn sẽ thấy

Bạn update stack bằng một template lỗi. Update bắt đầu, fail, rồi rollback. Stack có thể ở `UPDATE_ROLLBACK_COMPLETE`.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Resource nào fail đầu tiên? | `aws cloudformation describe-stack-events` — đọc event `*_FAILED` đầu tiên |
| Stack đang ở trạng thái nào? | `aws cloudformation describe-stacks` |
| Có drift không? | `detect-stack-drift` + `describe-stack-resource-drifts` |
| CDK có synth ra template không? | `cd labs/11-cloudformation-cdk/cdk && cdk synth` |

## 8. Thành công trông như thế nào?

`verify 11` PASS: stack `CREATE_COMPLETE`/`UPDATE_COMPLETE` sau khi bạn sửa template.

Nếu FAIL, đọc:

```bash
cat labs/11-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- `ROLLBACK_COMPLETE` vs `UPDATE_ROLLBACK_COMPLETE`.
- Stack Events: đọc từ dưới lên, tìm lỗi đầu tiên.
- CDK synth tạo CloudFormation template; CDK không phải dịch vụ runtime.

## 10. Note mẫu

- 1. Lỗi đầu tiên là gì?
- 2. Rollback đã trả resource về trạng thái cũ chưa?
- 3. Drift khác update lỗi ở đâu?

## 11. Cleanup

```bash
./bin/lab down 11
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
./bin/lab hint 11
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 11. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
