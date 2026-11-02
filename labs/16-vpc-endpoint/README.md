# Lab 16 — Private subnet → S3 endpoint + SSM endpoint

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D5 Networking 18% |
| Thời gian | ~180 phút |
| Cần app stack | Không |
| Chi phí | Trung bình |
| Lab ID | `16` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học private subnet không NAT: dùng Gateway Endpoint cho S3 (miễn phí) và Interface Endpoint cho SSM. Đây là kiến trúc tiết kiệm chi phí.
- **Việc đầu tiên:** Ô **Search** → `VPC` → **Endpoints** → lọc theo VPC của core.
- **Xong khi:** `verify 16` PASS: S3 gateway endpoint tồn tại và private instance `aws s3 ls` thành công.
- **Nếu lạc:** `./bin/lab console 16` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học private subnet không NAT: dùng Gateway Endpoint cho S3 (miễn phí) và Interface Endpoint cho SSM. Đây là kiến trúc tiết kiệm chi phí.

## 2. Hiện tại có gì?

Core VPC có private subnet. Lab tạo EC2 private (không public IP), interface endpoints cho SSM/SSM Messages/EC2 Messages, gateway endpoint cho S3.

## 3. Kiến trúc

```text
Private EC2 (no public IP)
   ├── SSM interface endpoint ──► SSM
   ├── SSM Messages endpoint
   ├── EC2 Messages endpoint
   └── S3 gateway endpoint ──► S3
   (không có NAT)
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Chỉ cần core stack; không cần app stack.

- Đọc `labs/16-*/README.md` (file này) và dòng lab `16` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 16
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 16
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 16
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 16
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 16
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 16
   ```

## 5b. Ghi chú / lệnh riêng

Interface endpoint tốn ~$0.01/giờ/AZ. `down 16` dọn hết. Không bật NAT cho lab này.

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
| Gateway endpoint | Cửa vào S3/DynamoDB qua route table, miễn phí. |
| Interface endpoint | ENI riêng trong subnet cho phần lớn service khác, có phí. |
| Private DNS | Phân giải tên service thành IP nội bộ. |
| Route table association | Gắn endpoint với route table của subnet. |
| ENI | Card mạng ảo của instance/endpoint. |

### Khái niệm của lab này

- Private subnet không có NAT thì không ra Internet.
- **Gateway endpoint** (S3, DynamoDB) gắn vào route table và miễn phí.
- **Interface endpoint** tạo ENI + security group trong subnet, tốn phí theo giờ.
- **Private DNS** giúp tên service phân giải thành IP nội bộ.

### Đường bấm từng bước

1. Ô **Search** → `VPC` → **Endpoints** → lọc theo VPC của core.
2. Bấm endpoint S3 (type **Gateway**) → tab **Route tables**: phải có route table của private subnet.
3. Bấm một interface endpoint (SSM) → tab **Subnets** và **Security groups**.
4. Ô **Search** → `EC2` → **Instances** → `soa-c03-lab16-private` → tab **Networking**: không có **Public IPv4**.
5. Ô **Search** → `Systems Manager` → **Fleet Manager**: instance private phải **Online**.
6. **Session Manager** → **Start session** → chạy `aws s3 ls s3://<bucket-core>`.
7. Nếu cần xem DNS: trong session chạy `getent hosts ssm.ap-southeast-1.amazonaws.com`.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Endpoint type | `Gateway` cho S3; `Interface` cho SSM/SSM Messages/EC2 Messages. |
| Endpoint state | `available` mới dùng được; `pending` thì chờ. |
| Route tables | Gateway endpoint phải gắn đúng route table của subnet private. |
| Security group của endpoint | Phải cho private SG vào 443. |
| Public IPv4 | Phải trống; có public IP là không còn “private”. |
| S3 result | `aws s3 ls` thành công chứng minh đường S3 đi qua endpoint. |

### Link nhanh

- [VPC endpoints](https://console.aws.amazon.com/vpcconsole/home?region=ap-southeast-1#Endpoints:)
- [EC2 instances](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#Instances:)
- [Fleet Manager](https://console.aws.amazon.com/systems-manager/managed-instances?region=ap-southeast-1)
- [Session Manager](https://console.aws.amazon.com/systems-manager/session-manager/start-session?region=ap-southeast-1)

### Nếu không thấy mục đó

- Instance không Online: kiểm tra 3 interface endpoint và private DNS.
- `aws s3 ls` timeout: gateway endpoint thiếu route table association, hoặc SG endpoint chặn 443.
- Endpoint `pending` vài phút là bình thường.
- Interface endpoint tốn phí; `./bin/lab down 16` ngay sau lab.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học private subnet không NAT: Gateway Endpoint cho S3, Interface Endpoint cho SSM.

### Bạn cần biết 4 khái niệm

- **Gateway endpoint**: Cửa vào S3/DynamoDB qua route table, miễn phí.
- **Interface endpoint**: ENI riêng trong subnet, có phí.
- **Private DNS**: Phân giải tên service thành IP nội bộ.
- **Route table association**: Gắn endpoint với route table.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Private EC2 | soa-c03-lab16-private | running, không public IP | EC2 → Instances |
| Interface endpoints | ssm, ssmmessages, ec2messages | available | VPC → Endpoints |
| Gateway endpoint | s3 | available, gắn route table | VPC → Endpoints |
| SSM | private instance | Online | Fleet Manager |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Endpoint có? | VPC → Endpoints | type, state |
| Route association? | Endpoint → Route tables | private route table |
| SG endpoint? | Endpoint → Security groups | 443 từ private SG |
| Public IP? | EC2 → Networking | không có |
| SSM online? | Fleet Manager | Ping status |
| S3 được không? | Session Manager → aws s3 ls | kết quả |

### Trước khi phá, bạn phải trả lời 3 câu

1. Gateway endpoint khác Interface endpoint ở đâu?
2. Vì sao private instance vẫn vào được SSM?
3. Thiếu route table association thì sao?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 16 --live` và `./bin/lab teach 16`.

## 6. Hiện tượng bạn sẽ thấy

Private EC2 không truy cập được S3. SSM vẫn có thể online nếu endpoint SSM đúng.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Instance có public IP không? | EC2 → Networking (phải không có) |
| SSM có online không? | `aws ssm describe-instance-information` |
| S3 endpoint có route chưa? | VPC → Endpoints → Route tables |
| Từ private instance, `aws s3 ls` có được không? | SSM Session Manager |

## 8. Thành công trông như thế nào?

`verify 16` PASS: S3 gateway endpoint tồn tại và private instance `aws s3 ls` thành công.

Nếu FAIL, đọc:

```bash
cat labs/16-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Gateway endpoint (S3/DynamoDB) vs Interface endpoint (phần lớn service khác).
- Private DNS cần `enableDnsSupport`/`enableDnsHostnames`.
- Endpoint phải được associate với đúng route table.

## 10. Note mẫu

- 1. SSM online nhờ đâu?
- 2. S3 đi đường nào?
- 3. Nếu thiếu route table association thì sao?

## 11. Cleanup

```bash
./bin/lab down 16
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
./bin/lab hint 16
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 16. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
