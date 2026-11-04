# LAB 13 — IAM + STS AssumeRole: trust policy vs permissions

```text
LAB: 13 — IAM + STS AssumeRole: trust policy vs permissions
SERVICE: role soa-c03-lab13-target · trust policy · inline policy lab13-s3
         · bucket soa-c03-074478993842-ap-southeast-1-data
DATE: 2026-11-03
DOMAIN: D4 Security 16%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ]
SOLUTION_USED: no (user tự viết; AI chỉ review + sửa lại theo yêu cầu "check và sửa giúp tôi";
                bản gốc giữ ở note.draft-2026-11-03.md)
```

## 1. What did I build?

| Thành phần | Tên thật | Trạng thái khoẻ |
|---|---|---|
| IAM role | `arn:aws:iam::074478993842:role/soa-c03-lab13-target` | tồn tại, session tối đa 1 giờ |
| Trust policy (ai được assume) | `Allow` `sts:AssumeRole` cho Principal `arn:aws:iam::074478993842:root` | Principal = account này, không phải account khác |
| Permission (assume rồi làm gì) | inline `lab13-s3`: `s3:ListBucket` + `s3:GetObject` | chỉ trên bucket core, không có managed policy nào khác |
| Bucket | `soa-c03-074478993842-ap-southeast-1-data` | chứa log CloudTrail |

`arn:aws:iam::...:root` trong trust policy nghĩa là **account này**, không phải user root.
Đây là 2 tầng độc lập: trust quyết định **ai vào được**, permission quyết định **vào rồi làm gì**.

## 2. What failed? (symptom, not root cause)

Chạy `aws sts assume-role` cho role lab thì bị từ chối:

```text
An error occurred (AccessDenied) when calling the AssumeRole operation:
User: arn:aws:iam::074478993842:user/xtan is not authorized to perform:
sts:AssumeRole on resource: arn:aws:iam::074478993842:role/soa-c03-lab13-target
```

Điểm quan trọng của triệu chứng: output **không có** khối `Credentials`, tức là **chưa hề có
credential tạm**. Mọi lỗi S3 (`s3:ListBucket`/`s3:GetObject`) bị loại trừ ngay từ bước này.

## 3. How did I detect it? (metric/log/event/CLI)

- **CLI**: lỗi ở operation `AssumeRole`, không phải `ListObjects` → lỗi thuộc **cửa ngoài**
  (quyền người gọi **hoặc** trust policy), không liên quan permission policy.
- **IAM → Roles → `soa-c03-lab13-target` → tab Trust relationships**: đọc toàn bộ JSON, thấy
  `Principal` và `Action` **đúng**, nhưng có thêm khối `Condition`:

  ```json
  "Condition": { "Bool": { "aws:MultiFactorAuthPresent": "true" } }
  ```

- **IAM → Roles → Last activity**: "19 minutes ago" → role **có** bị gọi nhưng không lần nào
  assume thành công (nếu thành công đã thấy hoạt động đọc S3).
- **Nguồn thứ 2 nên dùng (chưa mở trong buổi này)**: `CloudTrail → Event history`, filter
  `Event name: AssumeRole` → `errorCode: AccessDenied`, `userIdentity.type: IAMUser`, và
  `sessionContext` **không** có `mfaAuthenticated`. Đây là bản ghi do AWS tạo, mạnh hơn suy luận.

## 4. Root cause (the actual broken layer)

Trust policy của role có thêm điều kiện `Condition: Bool aws:MultiFactorAuthPresent = true`.

- `Principal` **đúng**, `Action` **đúng** — chỉ riêng `Condition` sai với cách gọi hiện tại.
- Credential đang dùng là **access key lâu dài** của user `xtan`, không mang ngữ cảnh MFA.
  Khi dùng access key lâu dài, khoá `aws:MultiFactorAuthPresent` **vắng mặt** (không phải `false`),
  nên `Bool ... "true"` không khớp → toàn bộ `Allow` **không áp dụng** → `AccessDenied`.
- Lỗi xảy ra **trước khi** cấp credential, nên không liên quan gì tới quyền S3 của role.

## 5. How did I fix it? (exact command or console action)

Console — **IAM → Roles → `soa-c03-lab13-target` → tab Trust relationships → nút `Edit trust policy`**:
xoá khối `Condition` (và dấu `,` ở cuối `"Action": "sts:AssumeRole"`) → **Update policy**.

Trust policy sau khi sửa:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::074478993842:root" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Kiểm chứng (phải **đợi ~15 giây**: IAM eventually consistent, đo được 5–13 giây):

```bash
aws sts assume-role --role-arn arn:aws:iam::074478993842:role/soa-c03-lab13-target \
  --role-session-name my-test --query 'AssumedRoleUser.Arn' --output text
# arn:aws:sts::074478993842:assumed-role/soa-c03-lab13-target/my-test
```

`./bin/lab verify 13` → **PASS 2026-11-03T01:29:21Z** (`AssumeRole works and role can list S3`).

## 6. Prevention / automation

- **Alarm trên CloudTrail** (đúng pattern lab 03/04): EventBridge rule bắt `sts:AssumeRole` với
  `errorCode = AccessDenied` → SNS `soa-c03-alerts`. Trust policy bị sửa sẽ lộ trong ~1 phút,
  không phải chờ người dùng báo.
- **Synthetic canary**: Lambda/EventBridge mỗi 5 phút thử assume-role bằng một phiên riêng;
  fail → báo động. Phát hiện trước cả người dùng.
- **Validate trước khi deploy**: chạy `aws accessanalyzer validate-policy` trên file trust policy
  trong CI, chặn ở bước review thay vì chặn ở production.
- **IAM Access Analyzer**: bật analyzer, review định kỳ các finding về policy.
- **Quy ước**: `Condition` MFA chỉ dùng cho role của **người dùng**; role cho **workload/CLI**
  dùng `ExternalId` hoặc `aws:PrincipalArn` thay vì MFA.

## 7. Exam trap

- Trust policy và permission policy là **2 tài liệu khác nhau, gắn lên 2 đối tượng khác nhau**
  (trust → role; identity policy → user). Cả hai đều có thể sinh ra **cùng một** thông báo
  `AccessDenied ... sts:AssumeRole`, nên không thể phân biệt bằng cách đọc câu lỗi.
- Câu hỏi tách bạch: **"đã có credential tạm chưa?"** — chưa có ⇒ lỗi ở cửa ngoài (quyền người
  gọi hoặc trust); có rồi mà vẫn lỗi ⇒ lỗi ở cửa trong (permission policy).
- `aws:MultiFactorAuthPresent` với access key lâu dài là **vắng mặt**, không phải `false`;
  điều kiện `Bool ... "true"` vì thế **luôn** fail. Đây là bẫy kinh điển của trust policy.
- AssumeRole được **không** có nghĩa là truy cập được tài nguyên: phải đủ 3 tầng — có quyền gọi
  `sts:AssumeRole`, được trust policy cho vào, và permission policy cho phép action cụ thể.
- Chứng minh "role đọc được S3" cần **2 bằng chứng S3 riêng biệt** (`ListBucket` và `GetObject`)
  cộng với `get-caller-identity` cho thấy ARN `assumed-role/...`.

## Ghi chú tooling (không phải lỗi của người học)

Buổi này `break 13` lần đầu **không phá được** (AWS từ chối trust policy trỏ tới account không
tồn tại `111122223333`, script lại không kiểm tra mã lỗi). Đã sửa trong `scripts/lib/labs.sh`:
dùng `Condition` thay cho account bịa, chờ tới khi denial thật sự quan sát được, `assume_role_env`
trả non-zero, và `verify 13` đọc tên bucket **trước** khi đổi sang quyền role. Chi tiết:
`docs/audit-report.md` #19 và #20. `make test` PASS 24/24.

## Chưa làm

- Chưa mở CloudTrail event cho `AssumeRole` trong buổi này (đọc trust policy là đủ để chốt);
  nên làm lại để có evidence do AWS ghi.
- Chưa thử nhánh "giữ `Condition` + dùng phiên có MFA" (cách đúng cho production).
