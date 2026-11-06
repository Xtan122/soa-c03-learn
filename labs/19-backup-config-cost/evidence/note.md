# LAB 19 — AWS Backup, Config, Cost Explorer, Budgets

```text
LAB: 19 — AWS Backup, Config, Cost Explorer, Budgets
SERVICE: AWS Backup, AWS Config, CloudTrail, Budgets, Cost Explorer
DATE: 2026-11-06
DOMAIN: D2 Reliability / D3 Automation
ACCOUNT: 074478993842 · REGION: ap-southeast-1
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [x]
HINTS_USED: 0 · SOLUTION_USED: no
```

## 1. What did I build?

Lab này không sửa app — nó dựng lớp **backup / compliance / cost** quanh app stack.

- **App stack** (`soa-c03-app`): ALB + ASG/EC2 + RDS `soa-c03-db` — RDS là mục tiêu backup.
- **AWS Backup**
  - vault `soa-c03-lab19`
  - plan `soa-c03-lab19-plan`, rule `daily` = `cron(0 5 ? * * *)`, `DeleteAfterDays: 7`
  - resource assignment `tagged` → chọn mọi resource có tag `Backup=lab19` (đã gắn lên `soa-c03-db`)
  - on-demand job `58913990-dd29-46f8-b832-98f4ef3bc574` → `COMPLETED` 15:08:54 (+07)
  - recovery point `awsbackup:job-58913990-…` — `Status = Completed`, `Backup type = Snapshot`,
    `BackupSizeInBytes = 0` (DB lab gần như rỗng, nên size 0 là hợp lý, không phải lỗi)
- **IAM**: role `soa-c03-lab19-backup` (cho Backup), role `soa-c03-lab19-config` (cho Config)
- **AWS Config**
  - bucket delivery `soa-c03-lab19-config-074478993842` (Block Public Access 4 cờ true)
  - delivery channel `soa-c03-lab19` (snapshot 24h)
  - recorder `soa-c03-lab19` — `allSupported=true`, ghi cả global resource types
  - rule `soa-c03-lab19-encrypted-volumes` (AWS managed `ENCRYPTED_VOLUMES`)
- **Cost**: budget `soa-c03-lab19`, limit **$5/month**, type COST, **không có alert threshold**

Baseline đo trước khi phá:

| Hạng mục | Giá trị |
|---|---|
| CI đã ghi | 37 |
| Rule compliance | 1 `Noncompliant` — `vol-064ff578745476df1` (EC2 Volume, chưa mã hoá) |
| Recorder | Recording **on**, `lastStatus = SUCCESS` |
| Backup | 1 recovery point `Completed` |
| App | `/health` 200, healthy targets = 1 |

## 2. What failed? (symptom, not root cause)

- AWS Config → **Settings**: dòng trạng thái đổi từ `Recording is on` sang **`Recording is off`**
  (kèm nút `Start recording`).
- Rule `soa-c03-lab19-encrypted-volumes` **vẫn hiện `1 Noncompliant`** với đúng volume cũ
  → nhìn màu thì không phân biệt được "vẫn lỗi" với "không còn ai kiểm".
- Không có email/thông báo nào. Backup và app không có triệu chứng gì.

## 3. How did I detect it?

1. So **baseline đã chụp trước `break`** với trạng thái hiện tại ở đúng ô đã đọc
   (`Config → Settings → Recording`): `on` → `off`.
2. **CloudTrail → Event history** lọc theo thời điểm, mở event `StopConfigurationRecorder`:

   | Trường | Giá trị |
   |---|---|
   | `eventTime` | `2026-11-06T08:36:53Z` = **15:36:53 +07** (mốc `break`: 15:36:54) |
   | `userIdentity.arn` | `arn:aws:iam::074478993842:user/xtan` |
   | `sourceIPAddress` | `14.238.24.130` |
   | `userAgent` | `aws-cli/2.38.0 … command#configservice.stop-configuration-recorder` |
   | `requestParameters` | `configurationRecorderName = soa-c03-lab19` |

3. **Rule detail**: `Last successful evaluation time = Nov 6, 2026, 3:06 PM` (15:06) — **trước**
   mốc phá khoảng 30 phút ⇒ kết quả `Noncompliant` đang hiển thị là dữ liệu **cũ**, không phải
   lần đánh giá mới.
4. **Đối chứng để loại trừ**: backup job vẫn `COMPLETED` (15:08:54), recovery point vẫn `Completed`,
   app `/health` vẫn 200 ⇒ lỗi nằm ở **lớp Config**, không phải backup/app/RDS.

## 4. Root cause (the actual broken layer)

Recorder `soa-c03-lab19` bị dừng bằng API `StopConfigurationRecorder`, gọi bằng **access key của
IAM user `xtan` qua AWS CLI** lúc **15:36:53 +07**. Từ mốc đó AWS Config **không ghi configuration
item mới** và rule `soa-c03-lab19-encrypted-volumes` **không được đánh giá lại** (lần cuối 15:06).
Vì vậy dữ liệu compliance trở thành **ảnh chụp cũ**: vi phạm mới không bị phát hiện, tạo
**compliance gap**, trong khi console vẫn hiện đỏ như trước — nhìn tưởng "hệ thống vẫn đang kiểm".

Ghi chú điều tra: CloudTrail ghi **principal** (`user/xtan`), không ghi "ai là con người". Một script
chạy bằng access key của user trông **giống hệt** user; phân biệt bằng `userAgent` (aws-cli) và
`sourceIPAddress`.

## 5. How did I fix it? (exact command or console action)

1. Console: **AWS Config → Settings → tab “Customer managed recorder” → nút `Start recording`**.
2. Xác nhận read-only: `describe-configuration-recorder-status` → `recording=True`,
   `lastStatus=SUCCESS`.
3. `./bin/lab verify 19`:

```text
verify 2026-11-06T08:46:27Z lab=19
 OK  backup=COMPLETED recoveryPoints=1 config=recording budget=soa-c03-lab19 costExplorer=7
 OK  PASS. DONE marker written to labs/19-backup-config-cost/evidence/DONE
```

## 6. Prevention / automation

- **IAM tách quyền**: role/credential dùng cho automation không có `config:StopConfigurationRecorder`;
  nếu buộc phải giữ, thêm policy `Deny` cho hành động này và bắt buộc MFA cho thao tác admin.
- **Phát hiện trong phút, không phải mở console**: CloudTrail → **EventBridge rule**
  (`eventName = StopConfigurationRecorder`, `eventSource = config.amazonaws.com`) → **SNS/email**;
  cùng kiểu rule cho `DeleteConfigurationRecorder`, `DeleteDeliveryChannel`, `DeleteBackupVault`.
- **Đo "còn tươi" chứ không đo màu**: alarm theo `Last successful evaluation time` /
  metric `ConfigurationItemsRecorded` tụt về 0 khi recorder tắt.
- **Restore testing** cho backup: `Completed` chưa chứng minh khôi phục được.
- Ở mức organization: SCP/Control Tower là cách chặn thật — repo này **chỉ học lý thuyết**,
  không gọi API Organizations/SCP/Control Tower.

## 7. Exam trap

- **`Completed` ≠ restore được.** Recovery point `Completed` chỉ nói đã ghi xong bản sao; muốn
  chứng minh dùng được phải **restore test**.
- **Budget không chặn chi phí.** Nó chỉ là thước đo + (nếu có alert) thông báo. Budget
  `soa-c03-lab19` còn **không có threshold** ⇒ dù `Forecasted vs. budget = 229%` đỏ vẫn **không báo**.
- **`Amount used $0.00` không có nghĩa miễn phí** — Cost Explorer/Budgets trễ tới ~24h; trong ngày
  phải đối chiếu bằng cách liệt kê tài nguyên (`make cost`), không tin số 0.
- **Config vs CloudTrail**: Config = *tài nguyên đang có cấu hình gì, có tuân luật không, thay đổi
  theo thời gian*; CloudTrail = *ai gọi API nào, lúc nào, từ IP nào*. Config không nói ai tắt recorder.
- **Recorder off ⇒ compliance cũ vẫn hiện đỏ/xanh**: không phân biệt được "không đổi" với
  "không biết". Đọc `Last successful evaluation time`, đừng chỉ đọc màu.
- **On-demand backup ≠ backup theo plan**: job on-demand không xuất hiện trong tab Backup jobs của
  plan; `Last runtime = –` nghĩa là plan chưa từng tự chạy.
- **Rule `ENCRYPTED_VOLUMES` chỉ chấm volume đang tồn tại**: bật "EBS encryption by default" chỉ áp
  cho volume **tạo mới**, không hồi tố; muốn sửa volume cũ phải snapshot → copy snapshot có mã hoá →
  tạo volume mới.
- **Resource assignment theo tag**: xoá tag `Backup=lab19` khỏi RDS là plan "daily" không còn gì để
  backup, dù plan vẫn xanh.

## 8. Chưa làm

- Chưa **restore thật** từ recovery point (mới đọc `Status = Completed`).
- Chưa cấu hình **Budget alert threshold** + SNS (budget hiện không có alert).
- Chưa dựng **EventBridge rule** cho `StopConfigurationRecorder`.
- Chưa đọc lại **Cost Explorer sau 24h** để đối chiếu giá Config/Backup thực tế.
- Giá AWS Backup warm storage cho **RDS**: chưa xác minh được bằng Price List API
  (API không trả dòng cho RDS) — chỉ đối chiếu bằng `make cost` cuối buổi.
