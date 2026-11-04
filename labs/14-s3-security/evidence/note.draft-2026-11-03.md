# LAB 14 — S3 public exposure: detect, contain, fix

```text
LAB: 14 — S3 public exposure: detect, contain, fix
SERVICE:
DATE: 2026-11-03
DOMAIN: D4 Security 16%
PHASES: Build [x] Break [x] Diagnose [x] Fix [ ] Verify [x] Cleanup [ ]
```

1. What did I build?
bucket soa-c03-lab14-074478993842, object secret.txt 13 bytes AES256, analyzer soa-c03-lab14
2. What failed? (symptom, not root cause)
anonymous curl → 200 + nội dung lab14-secret (baseline là 403)
3. How did I detect it? (metric/log/event/CLI)
3 lớp: BPA 4 cờ false · policy PublicRead Principal "*" s3:GetObject · ACL chỉ CanonicalUser (không public)
4. Root cause (the actual broken layer)
2 lớp mở cùng lúc: BPA tắt và bucket policy public. ACL không phải nguyên nhân (owner-only + BucketOwnerEnforced)
5. How did I fix it? (exact command or console action)
bật 4 cờ BPA → 403, nhưng chưa an toàn; sau đó xoá statement public → verify PASS
6. Prevention / automation
4 cờ BPA ở account level (không chỉ bucket), Access Analyzer + EventBridge alert on PutBucketPolicy, review s3:PutBucketAcl, IaC + validate-policy
7. Exam trap
p	ListBucket ≠ GetObject; BPA override ≠ delete; 403 ≠ an toàn; 3 đường public (policy/ACL/presigned)