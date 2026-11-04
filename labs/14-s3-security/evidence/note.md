# LAB 14 — S3 public exposure: detect, contain, fix

```text
LAB: 14 — S3 public exposure: detect, contain, fix
SERVICE: bucket soa-c03-lab14-074478993842 · object secret.txt
         · Block Public Access (4 cờ) · bucket policy · ACL · Access Analyzer soa-c03-lab14
DATE: 2026-11-03
DOMAIN: D4 Security 16%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ]
SOLUTION_USED: no (user tự viết; AI chỉ review + sửa câu từ theo yêu cầu
                "check và sửa câu từ giúp tôi"; bản gốc ở note.draft-2026-11-03.md)
```

## 1. What did I build?

| Thành phần | Giá trị thật | Trạng thái khoẻ |
|---|---|---|
| Bucket | `soa-c03-lab14-074478993842` (ap-southeast-1) | 4 cờ BPA bật, không có bucket policy |
| Object | `secret.txt` — **13 bytes**, mã hoá `AES256` (SSE-S3) | chỉ đọc được bằng credential |
| Object Ownership | `BucketOwnerEnforced` | **ACL bị vô hiệu hoá** ở tầng bucket |
| Bucket ACL | 1 grant duy nhất: `CanonicalUser / FULL_CONTROL` (chủ bucket) | không có `AllUsers` |
| Access Analyzer | `soa-c03-lab14` — `ACTIVE`, type `ACCOUNT` | theo dõi truy cập ngoài account |
| Anonymous | `curl` không ký → **403** | đường public đã đóng |

## 2. What failed? (symptom, not root cause)

Request **không có credential** đọc được nội dung object:

```bash
curl -s -o /dev/null -w '%{http_code}\n' \
  https://soa-c03-lab14-074478993842.s3.ap-southeast-1.amazonaws.com/secret.txt
# 200  (baseline trước khi phá: 403)
# nội dung trả về: lab14-secret
```

Điểm cần nhớ: `200` chứng minh **một** đường public đang mở tại thời điểm đó. Nó **không**
chỉ ra đường nào, và **không** nói còn đường nào khác đang mở.

## 3. How did I detect it? (metric/log/event/CLI)

Kiểm tra **cả 3 lớp**, ghi lại giá trị thật — đây là phần quyết định:

| Lớp | Lệnh | Giá trị đo được sau khi phá | Kết luận |
|---|---|---|---|
| ① Block Public Access | `aws s3api get-public-access-block --bucket ...` | `BlockPublicAcls=false`, `IgnorePublicAcls=false`, `BlockPublicPolicy=false`, `RestrictPublicBuckets=false` | **MỞ** — toàn bộ công tắc bị tắt |
| ② Bucket policy | `aws s3api get-bucket-policy --bucket ...` · `get-bucket-policy-status` | `Sid: PublicRead`, `Effect: Allow`, `Principal: "*"`, `Action: s3:GetObject`, `Resource: arn:aws:s3:::soa-c03-lab14-074478993842/*` · `PolicyStatus.IsPublic = true` | **MỞ** — public thật |
| ③ ACL | `get-bucket-acl` · `get-bucket-ownership-controls` | chỉ 1 grant `CanonicalUser / FULL_CONTROL`; `BucketOwnerEnforced` | **ĐÓNG** — không có `AllUsers`/`AuthenticatedUsers`, và ACL đã bị vô hiệu hoá |
| ④ Access Analyzer | `aws accessanalyzer list-findings --analyzer-arn ...` | finding cho bucket (public external access) | **bằng chứng phụ**, không phải nguyên nhân |

Vì sao loại trừ ACL: (a) grant duy nhất là chủ bucket, không có URI công khai;
(b) `BucketOwnerEnforced` khiến ACL không còn tác dụng — dù có grant `AllUsers` cũng bị bỏ qua.

## 4. Root cause (the actual broken layer)

**Hai lớp mở cùng lúc** — mỗi lớp một mình đã đủ gây rò rỉ:

1. **Block Public Access bị tắt** — cả 4 cờ `false`, nên không còn lớp `Deny` nào chặn phía trên.
2. **Bucket policy public** — statement `PublicRead` cho `Principal: "*"` quyền `s3:GetObject`
   trên `arn:aws:s3:::soa-c03-lab14-074478993842/*`.

ACL **không** phải nguyên nhân (owner-only + `BucketOwnerEnforced`).

Chuỗi nhân quả: `Principal "*"` cho `GetObject` → BPA tắt nên không bị đè → anonymous `200`
→ đọc được `secret.txt`.

## 5. How did I fix it? (exact command or console action)

Thứ tự quan trọng — làm **hai** việc, không chỉ một:

**Bước 1 — bật lại Block Public Access** (S3 → bucket → tab `Permissions` → khối
`Block public access (bucket settings)` → `Edit` → tick cả 4 → `Save changes` → `confirm`).

Kết quả đo được: anonymous chuyển **200 → 403**.

> Nhưng **chưa an toàn**: `Principal: "*"` vẫn còn trong bucket policy. BPA chỉ **đè** lên,
> **không xoá**. Ai tắt BPA sau này là bucket public trở lại ngay.

**Bước 2 — gỡ nguồn public** (tab `Permissions` → khối `Bucket policy` → `Edit` → xoá statement
`PublicRead` → `Save changes`).

Kết quả đo được:

```text
get-bucket-policy-status → NoSuchBucketPolicy   (policy đã xoá)
get-public-access-block  → True True True True  (BPA vẫn đủ 4 cờ)
anonymous curl           → 403
```

`./bin/lab verify 14` → **PASS 2026-11-03T02:26:44Z** (`BPA on, policy private, anonymous=403`).

## 6. Prevention / automation

- **BPA ở mức account**, không chỉ từng bucket: `aws s3control put-public-access-block
  --account-id <id>` — chặn mọi bucket hiện tại **và tương lai**. Đây là biện pháp mạnh nhất,
  rẻ nhất và hay xuất hiện trong đề.
- **Cảnh báo khi policy/ACL bị đổi**: EventBridge rule bắt CloudTrail `PutBucketPolicy`,
  `PutBucketAcl`, `DeletePublicAccessBlock` → SNS `soa-c03-alerts`. Đúng pattern đã học ở lab 03/04:
  thay đổi cấu hình bảo mật phải có **alarm**, không chờ người dùng phát hiện.
- **Access Analyzer + review định kỳ** finding `ACTIVE`, và bật **unused access** analyzer.
- **IaC + kiểm tra tự động**: `aws accessanalyzer validate-policy` cho bucket policy trong CI;
  policy as code để review thay đổi trước khi merge.
- **Tắt ACL toàn account** (`Object Ownership = BucketOwnerEnforced`) và coi ACL public là
  finding phải sửa, không phải "cấu hình hợp lệ".
- **Kiểm thử định kỳ**: job anonymous `curl` cho các object nhạy cảm, kỳ vọng `403`;
  nhận `200` là báo động.

## 7. Exam trap

- **`s3:ListBucket` ≠ `s3:GetObject`**: `ListBucket` là quyền trên **bucket** (liệt kê tên),
  `GetObject` là quyền trên **object** (đọc nội dung). Policy ở lab này chỉ cho `GetObject`
  trên `bucket/*`, nên người lạ tải được file nhưng **không** liệt kê được bucket.
- **BPA đè ≠ BPA xoá**: bật BPA làm request `403` nhưng bucket policy/ACL public vẫn còn nguyên
  trong cấu hình. "Đang bị chặn" không phải "đã đóng".
- **`403` không đồng nghĩa an toàn**: nó chỉ chứng minh request đó, object đó, thời điểm đó bị
  từ chối. Muốn chốt phải có thêm `PolicyStatus` không public + ACL không có `AllUsers`
  + analyzer không còn finding `ACTIVE`.
- **Ba đường public**: bucket policy (`Principal "*"`), ACL (`AllUsers`/`AuthenticatedUsers`),
  và **presigned URL** (không phải public thật nhưng vẫn lộ dữ liệu — không thấy trong policy).
- **`BlockPublicPolicy=true` chặn cả việc lưu policy public mới** (`PutBucketPolicy` →
  `AccessDenied`), dễ bị hiểu nhầm là "policy của tôi sai cú pháp".
- Khi điều tra rò rỉ S3 thật: thứ tự đọc là **BPA → bucket policy → ACL → Access Analyzer →
  CloudTrail data events** (nếu đã bật), chứ không phải chỉ nhìn một chỗ.

## Ghi chú tooling (không phải lỗi của người học)

Trong buổi này, một số lệnh S3/CloudFormation bị **treo 40–60s rồi timeout** dù cùng lệnh chạy
lại thì trả về trong ~1s (`get-public-access-block` treo 45s, ngay sau đó 3 lần liên tiếp OK;
`aws s3 ls` trên bucket core treo >60s). Đây là flakiness mạng/CLI của máy, không phải trạng thái
bucket. Cách xử lý tạm: `AWS_MAX_ATTEMPTS=1` và chạy lại; nhớ rằng **timeout ≠ AccessDenied**.

## Chưa làm

- Chưa đọc **CloudTrail data events** cho object (lab không bật data events; muốn thấy
  `GetObject` của người lạ phải bật trước).
- Chưa thử nhánh **presigned URL** và nhánh **ACL public** (bucket đã `BucketOwnerEnforced`).
