# LAB 10 — Secrets Manager + KMS: có quyền S3 vẫn AccessDenied

```text
LAB: 10 — Secrets Manager + KMS: có quyền S3 vẫn AccessDenied
SERVICE: S3 (lab10/secret.txt, SSE-KMS) · KMS alias/soa-c03-lab · Secrets Manager /soa-c03/lab10/api-key · role soa-c03-lab10-reader
DATE: 2026-11-02
DOMAIN: D4 Security 16%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ]
SOLUTION_USED: no (tự assume-role để tái hiện, tự bấm Edit key policy trên console)
```

1. What did I build?

Secret `/soa-c03/lab10/api-key` (ARN `…-h85Vr7`), object `s3://soa-c03-074478993842-ap-southeast-1-data/lab10/secret.txt`
mã hoá **SSE-KMS** bằng key `alias/soa-c03-lab`, và role `soa-c03-lab10-reader` có `s3:GetObject`
+ `secretsmanager:GetSecretValue` nhưng **chưa** có quyền KMS.
(`lab10-diag` chỉ là tên role-session mình dùng khi assume-role, không phải tài nguyên.)

2. What failed? (symptom, not root cause)

Đứng dưới danh tính role reader, `GetObject` bị `AccessDenied`. Đứng dưới user admin thì **không**
thấy lỗi, vì quyền gắn theo **principal** chứ không theo người đang ngồi trước máy.

3. How did I detect it? (metric/log/event/CLI)

- CLI (assume-role rồi `s3 cp`), nguyên văn:
  `not authorized to perform: kms:Decrypt on resource: arn:aws:kms:ap-southeast-1:074478993842:key/93bf48f4-… with an explicit deny in a resource-based policy`
- KMS → `alias/soa-c03-lab` → **Key state = Enabled** → loại trừ giả thuyết "key bị disable".
- KMS → tab **Key policy** → đọc 4 statement để tìm cái khớp với role reader.

4. Root cause (the actual broken layer)

Lớp từ chối là **KMS key policy**, không phải IAM và không phải quan hệ role/S3.
Statement `Lab10Deny` có `Effect: Deny`, `Principal: role soa-c03-lab10-reader`, `Action: kms:*`,
`Resource: *` — tức chặn **mọi** thao tác KMS của role này, kể cả `kms:Decrypt`.

Role có **2** statement cùng khớp: `Lab10Reader` (Allow) và `Lab10Deny` (Deny) → **explicit deny
thắng**, nên `s3:GetObject` đúng vẫn không đọc được nội dung.

5. How did I fix it? (exact command or console action)

Console: **KMS → Customer managed keys → `alias/soa-c03-lab` → tab Key policy → Edit** → xoá
statement `Lab10Deny` (kèm dấu phẩy thừa) → **Save**. Giữ nguyên `EnableRoot`, `AllowCloudTrail`,
`Lab10Reader`.
Kiểm chứng: CLI assume-role + `s3 cp` trả `kms-lab-object`; `./bin/lab verify 10` PASS
(2026-11-02T08:09:53Z).

6. Prevention / automation

- Dùng **CloudTrail** để biết **ai** đã sửa key policy và **ai** bị từ chối (`Decrypt` + `errorCode`).
- Giới hạn `kms:PutKeyPolicy` bằng IAM: chỉ role vận hành được sửa key policy, có điều kiện rõ ràng.
- Trong deny nên dùng `Action` hẹp (`kms:Decrypt`) thay vì `kms:*`, tránh tự khoá mình khỏi mọi
  thao tác KMS kể cả khi cần điều tra.
- Thêm test tự động: chạy assume-role + đọc object sau mỗi lần đổi key policy (đúng cách `verify` làm).

7. Exam trap

- **Quyền S3 ≠ quyền KMS**: object SSE-KMS cần **cả** `s3:GetObject` **và** `kms:Decrypt`.
- **Explicit deny luôn thắng Allow**, bất kể Allow đến từ IAM hay key policy.
- **Tài khoản admin không tái hiện được lỗi của role** — phải `AssumeRole` mới thấy `AccessDenied`.
- Trong key policy, `"Resource": "*"` nghĩa là **chính key đó**; `Principal: root` là câu **uỷ quyền
  cho IAM**, không phải "cho root user".
