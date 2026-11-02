# Lab 07 — RDS snapshot, restore, verify dữ liệu

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D2 Reliability 22% |
| Thời gian | ~180 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Trung bình |
| Lab ID | `07` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học backup/restore thật: tạo snapshot, xoá dữ liệu, restore ra DB mới, rồi chứng minh dữ liệu đã quay lại.
- **Việc đầu tiên:** Ô **Search** → `RDS` → menu trái **Snapshots** → tab **Manual**.
- **Xong khi:** `verify 07` PASS: DB `soa-c03-lab07-restored` available và bảng `lab07` có ≥ 5 dòng.
- **Nếu lạc:** `./bin/lab console 07` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học backup/restore thật: tạo snapshot, xoá dữ liệu, restore ra DB mới, rồi chứng minh dữ liệu đã quay lại.

## 2. Hiện tại có gì?

App stack + RDS PostgreSQL chạy. Lab tạo bảng `lab07` 5 dòng và một snapshot thủ công.

## 3. Kiến trúc

```text
App EC2 → RDS PostgreSQL
                 │
                 ├── table lab07 (5 rows)
                 └── manual snapshot
                         │
                         ▼
                 restored DB (bạn tạo)
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/07-*/README.md` (file này) và dòng lab `07` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 07
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 07
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 07
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 07
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 07
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 07
   ```

## 5b. Ghi chú / lệnh riêng

### Lệnh restore gợi ý

```bash
# Lấy subnet group và SG của DB gốc
aws cloudformation describe-stacks --stack-name soa-c03-app   --query "Stacks[0].Outputs[?OutputKey=='DbSubnetGroupName'].OutputValue" --output text
aws cloudformation describe-stacks --stack-name soa-c03-app   --query "Stacks[0].Outputs[?OutputKey=='DbSecurityGroupId'].OutputValue" --output text

aws rds restore-db-instance-from-db-snapshot   --db-instance-identifier soa-c03-lab07-restored   --db-snapshot-identifier soa-c03-lab07-snapshot   --db-instance-class db.t4g.micro   --db-subnet-group-name <DbSubnetGroupName>   --vpc-security-group-ids <DbSecurityGroupId>   --no-publicly-accessible

aws rds wait db-instance-available   --db-instance-identifier soa-c03-lab07-restored
```

Đây là lab duy nhất bạn phải tạo DB mới bằng tay.

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
| Snapshot | Ảnh chụp dữ liệu tại một thời điểm. |
| Restore | Tạo DB mới từ snapshot. |
| DB subnet group | Tập subnet mà RDS được phép đặt DB. |
| Endpoint | Địa chỉ DNS + port để kết nối DB. |
| RPO | Mất tối đa bao nhiêu dữ liệu tính từ lần backup gần nhất. |
| RTO | Mất bao lâu để dịch vụ chạy lại. |

### Khái niệm của lab này

- **Snapshot** là ảnh chụp storage tại một thời điểm.
- **Restore** luôn tạo một DB **mới** từ snapshot, không ghi đè DB đang chạy.
- DB mới phải nằm trong subnet group và security group đúng thì app mới kết nối được.

### Đường bấm từng bước

1. Ô **Search** → `RDS` → menu trái **Snapshots** → tab **Manual**.
2. Bấm snapshot `soa-c03-lab07-snapshot`; xem **Status**, **Snapshot creation time**, **Engine**.
3. **Actions** → **Restore snapshot**.
4. Trang restore: **DB instance identifier** = `soa-c03-lab07-restored`; **DB instance class** = `db.t4g.micro`.
5. Mục **Connectivity**: chọn đúng **VPC**, **DB subnet group** và **Existing VPC security groups** của DB gốc.
6. **Public access** = **No** → bấm **Restore DB instance**.
7. Menu trái **Databases** → bấm `soa-c03-lab07-restored` → chờ **Status = Available**.
8. Tab **Connectivity & security**: ghi **Endpoint** và **Port**.
9. Từ app instance qua SSM, chạy `psql` và `SELECT count(*) FROM lab07;` (lệnh mẫu ở mục 5b của README).

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Snapshot Status | `available` mới restore được. |
| Snapshot time | Dữ liệu trong snapshot dừng ở thời điểm này. |
| DB Status | `creating` → `backing-up` → `available`. |
| Subnet group | Sai subnet group có thể đặt DB ra subnet không kết nối được. |
| Security group | Phải cho app SG vào port 5432. |
| Row count | `5` chứng minh dữ liệu đã quay lại, không chỉ DB bật. |

### Link nhanh

- [RDS snapshots](https://console.aws.amazon.com/rds/home?region=ap-southeast-1#snapshots:)
- [RDS databases](https://console.aws.amazon.com/rds/home?region=ap-southeast-1#databases:)

### Nếu không thấy mục đó

- Không thấy snapshot: `./bin/lab up 07` chưa xong; snapshot RDS có thể mất vài phút.
- Restore báo lỗi subnet/SG: copy đúng giá trị từ DB gốc (tab **Configuration** / **Connectivity & security**).
- DB `available` nhưng `psql` timeout: kiểm tra SG 5432, subnet route, và endpoint có đúng DB mới không.
- Đừng restore đè lên DB gốc; RDS không cho làm vậy.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học backup/restore thật: tạo snapshot, xoá dữ liệu, restore ra DB mới, chứng minh dữ liệu quay lại.

### Bạn cần biết 4 khái niệm

- **Snapshot**: Ảnh chụp dữ liệu tại một thời điểm.
- **Restore**: Tạo DB mới từ snapshot.
- **DB subnet group**: Tập subnet RDS được phép dùng.
- **RPO/RTO**: Mất tối đa bao nhiêu dữ liệu / mất bao lâu để chạy lại.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| RDS | soa-c03-db | available | RDS → Databases |
| Table lab07 | lab07 | 5 dòng | psql qua SSM |
| Snapshot | soa-c03-lab07-snapshot | available | RDS → Snapshots → Manual |
| Restored DB | soa-c03-lab07-restored | chưa tồn tại trước break | RDS → Databases |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Snapshot có? | RDS → Snapshots | Status, creation time |
| Restore ra đâu? | RDS → Snapshots → Restore | DB identifier, class |
| Subnet/SG? | RDS → DB → Connectivity | subnet group, SG |
| Dữ liệu về chưa? | psql SELECT count(*) | số dòng lab07 |

### Trước khi phá, bạn phải trả lời 3 câu

1. Snapshot khác automated backup ở đâu?
2. Restore tạo endpoint mới hay dùng lại endpoint cũ?
3. Vì sao DB restored phải cùng subnet/SG?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 07 --live` và `./bin/lab teach 07`.

## 6. Hiện tượng bạn sẽ thấy

Dữ liệu trong bảng `lab07` bị xoá. Bạn phải restore snapshot ra một DB mới tên `soa-c03-lab07-restored`.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Snapshot có tồn tại? | `aws rds describe-db-snapshots --db-snapshot-identifier soa-c03-lab07-snapshot` |
| Restore ra DB nào? | RDS → Snapshots → Restore snapshot |
| DB restored có cùng subnet/SG? | Phải cùng private subnet group và DB SG |
| Dữ liệu đã về chưa? | `SELECT count(*) FROM lab07;` trên DB restored |

## 8. Thành công trông như thế nào?

`verify 07` PASS: DB `soa-c03-lab07-restored` available và bảng `lab07` có ≥ 5 dòng.

Nếu FAIL, đọc:

```bash
cat labs/07-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Automated backup vs manual snapshot vs restore.
- Restore tạo endpoint mới; app phải đổi DNS/parameter nếu muốn dùng.
- RTO/RPO: đo thời gian restore và mất bao nhiêu dữ liệu.

## 10. Note mẫu

- 1. Snapshot tạo lúc nào?
- 2. Restore mất bao lâu?
- 3. Vì sao DB restored phải cùng subnet/SG?

## 11. Cleanup

```bash
./bin/lab down 07
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
./bin/lab hint 07
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 07. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
