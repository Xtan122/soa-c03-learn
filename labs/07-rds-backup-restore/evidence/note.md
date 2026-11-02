# LAB 07 — RDS snapshot, restore, verify dữ liệu

```text
LAB: 07 — RDS snapshot, restore, verify dữ liệu
SERVICE: RDS PostgreSQL (db.t4g.micro) + SSM Session Manager + Secrets Manager
DATE: 2026-10-31 (+07)  |  UTC 2026-10-30T17:41Z (snapshot) → 18:35:40Z (verify PASS)
DOMAIN: D2 Reliability 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ] SOLUTION_USED: yes, HINTS_USED: 0.
```

> Ghi chú: note này do AI viết hộ theo yêu cầu rõ ràng của người học ("viết hộ tôi").
> Người học tự bấm restore trên console, tự chạy `psql`, tự trả lời brief gate trước khi break.

## Baseline trước khi phá (bắt buộc)

```text
soa-c03-db            : available, db.t4g.micro, Multi-AZ = False
                        endpoint soa-c03-db.ch8q4oyqg4cb.ap-southeast-1.rds.amazonaws.com
snapshot (manual)     : soa-c03-lab07-snapshot, available, 2026-10-30T17:41:35Z, 20 GB, postgres
bảng lab07            : 5 dòng
Restored DB           : soa-c03-lab07-restored chưa tồn tại
App                   : /health 200, healthy targets = 1
Core                  : CloudTrail logging, S3 BPA 4/4 true, KMS Enabled, Budget soa-c03-monthly
```

```text
Thay đổi (fault)      : 2026-10-30T17:54:50Z — dữ liệu bảng lab07 bị xoá; snapshot vẫn còn
```

1. What did I build?

```text
App EC2 (i-075cdb54106c20c0c, private 10.42.0.190) → RDS PostgreSQL:5432 (private subnet, Public access = No)
Manual snapshot soa-c03-lab07-snapshot của DB gốc.
```

2. What failed? (symptom, not root cause)

```text
Dữ liệu bảng lab07 biến mất. DB instance vẫn available, app /health vẫn 200 → "hệ thống khoẻ" nhưng dữ liệu sai/thiếu.
```

3. How did I detect it? (metric/log/event/CLI)

```text
Từ app instance qua SSM (sudo -i; source /etc/cloudops.env), chạy psql:

DB gốc  $DB_HOST  → select count(*) from lab07;  ⇒  0
DB mới  $NEW_HOST → select count(*) from lab07;  ⇒  5

Endpoint gốc : soa-c03-db.ch8q4oyqg4cb.ap-southeast-1.rds.amazonaws.com
Endpoint mới : soa-c03-lab07-restored.ch8q4oyqg4cb.ap-southeast-1.rds.amazonaws.com
```

Cặp số **0 vs 5** trên **hai endpoint khác nhau** là evidence mạnh nhất: nó loại trừ khả năng
"kết nối nhầm DB/sai bảng". Một mình số 0 không đủ.

4. Root cause (the actual broken layer)

```text
Các dòng của bảng lab07 bị xoá khỏi DB đang chạy — mất dữ liệu, KHÔNG phải DB instance hỏng
(instance vẫn available, kết nối được).
Dữ liệu vẫn cứu được vì snapshot manual 2026-10-30T17:41:35Z giữ bản sao storage trước khi xoá.
RDS không cho restore đè instance đang chạy: restore luôn tạo instance MỚI với endpoint MỚI,
nên dữ liệu chỉ "về" khi trỏ app sang endpoint mới.
```

5. How did I fix it? (exact command or console action)

```text
RDS → Snapshots → Manual → soa-c03-lab07-snapshot → Actions → Restore snapshot
  DB instance identifier : soa-c03-lab07-restored
  DB instance class      : db.t4g.micro
  VPC                    : soa-c03-vpc (vpc-03a3584329e94b60e)
  DB subnet group        : soa-c03-app-dbsubnetgroup-9hfxaljuldfz
  VPC security group     : soa-c03-app-DbSecurityGroup (sg-0132573fc39e9080c)
  Public access          : No
→ Restore DB instance  (không tạo backup mới; dùng snapshot có sẵn)

Chờ Status creating → backing-up → available, rồi:
  export NEW_HOST=soa-c03-lab07-restored.ch8q4oyqg4cb.ap-southeast-1.rds.amazonaws.com
  psql -h "$NEW_HOST" -U "$DB_USER" -d "$DB_NAME" -c 'select count(*) from lab07;'   ⇒ 5
```

```text
RTO thực đo : bấm Restore 01:12 (+07) → available 01:28 (+07) ≈ 16 phút
RPO         : dữ liệu mất tính từ mốc snapshot 17:41:35Z (mọi thay đổi sau mốc đó mất)
```

Lưu ý vận hành: `aws rds describe-db-instances` **không chạy được từ app instance**
(role `soa-c03-app-instance` không có `rds:DescribeDBInstances` — least privilege).
Endpoint phải lấy từ console (RDS → Databases → Connectivity & security) hoặc từ máy có quyền.

6. Prevention / automation

```text
- Automated backup retention 7–35 ngày (mặc định 7 quá ngắn với dữ liệu quan trọng) + bật PITR
  để restore tới từng giây trong retention window.
- Test restore định kỳ (mỗi quý) vào DB tạm rồi verify row count — backup chưa test = backup không tồn tại.
- Deletion protection trên DB production; hạn chế rds:DeleteDBInstance / rds:DeleteDBSnapshot bằng IAM.
- Với xoá dữ liệu do người dùng: soft delete hoặc audit log (CloudTrail data events, log_statement)
  để biết ai xoá, lúc nào.
- Runbook cutover: verify trên DB mới TRƯỚC, rồi mới đổi DNS/parameter trỏ app sang endpoint mới.
```

7. Exam trap

```text
DB "available" + app /health 200 KHÔNG có nghĩa hệ thống đang phục vụ dữ liệu đúng.
Health check chỉ đo tiến trình, không đo tính toàn vẹn dữ liệu.
Phải kiểm tra row count trên ĐÚNG endpoint (restore tạo endpoint mới, không dùng lại endpoint cũ).
```
