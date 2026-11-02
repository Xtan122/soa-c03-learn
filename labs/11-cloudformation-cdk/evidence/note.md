# LAB 11 — CloudFormation update rollback + drift + CDK

```text
LAB: 11 — CloudFormation update rollback + drift + CDK
SERVICE: CloudFormation stack soa-c03-lab11 (SQS LabQueue · S3 LabBucket · SSM QueueUrlParameter · EC2 BrokenSecurityGroup)
DATE: 2026-11-02
DOMAIN: D3 Automation 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ]
SOLUTION_USED: no (tự đọc Stack Events, tự sửa YAML, tự chạy update-stack)
SCOPE: mục "drift" và "cdk synth" CHƯA làm (user chọn bỏ qua) — lab này mới hoàn thành phần rollback
```

1. What did I build?

Stack `soa-c03-lab11` (CREATE_COMPLETE 08:25:33Z) gồm 3 resource:

| Logical ID | Loại | Physical ID |
|---|---|---|
| `LabQueue` | `AWS::SQS::Queue` | `.../soa-c03-lab11-queue` |
| `LabBucket` | `AWS::S3::Bucket` | `soa-c03-lab11-074478993842-ap-southeast-1` |
| `QueueUrlParameter` | `AWS::SSM::Parameter` | `/soa-c03/lab11/queue-url` |

`break` đưa vào template một resource thứ 4: `BrokenSecurityGroup` (`AWS::EC2::SecurityGroup`).

2. What failed? (symptom, not root cause)

`update-stack` fail ở resource `BrokenSecurityGroup` → CloudFormation rollback → stack về
`UPDATE_ROLLBACK_COMPLETE`. **3 resource cũ không bị ảnh hưởng**; chỉ resource mới bị gỡ.
Đây là hành vi đúng: update lỗi thì quay về bản cũ, không phá hệ thống đang chạy.

3. How did I detect it? (metric/log/event/CLI)

**CloudFormation → stack `soa-c03-lab11` → tab Events**, event `*_FAILED` **đầu tiên**:

```text
2026-11-02 15:37:17 +07   BrokenSecurityGroup   CREATE_FAILED
Resource handler returned message: "The vpc ID 'vpc-00000000000000000' does not exist
(Service: Ec2, Status Code: 400, Request ID: db275fa8-...) (HandlerErrorCode: InvalidRequest)"
```

Các event phía trên (`UPDATE_ROLLBACK_IN_PROGRESS`, `..._CLEANUP_IN_PROGRESS`) chỉ là **hệ quả**.
Trạng thái cuối: `UPDATE_ROLLBACK_COMPLETE`.

4. Root cause (the actual broken layer)

Lớp hỏng là **property tham chiếu trong template**, không phải IAM và không phải cú pháp YAML
(template qua được bước validate): property `VpcId` bị hardcode thành `vpc-00000000000000000`
— 17 số 0, một VPC **không tồn tại**. EC2 API trả `InvalidRequest` khi tạo Security Group
trong VPC đó.

5. How did I fix it? (exact command or console action)

1. Lấy VPC thật: **CloudFormation → stack `soa-c03-core` → tab Outputs → `VpcId`**
   = `vpc-03a3584329e94b60e`.
2. Sửa `labs/11-cloudformation-cdk/template-broken.yaml`:
   `VpcId: vpc-00000000000000000` → `VpcId: vpc-03a3584329e94b60e`.
3. Update lại:

   ```bash
   aws cloudformation update-stack --stack-name soa-c03-lab11 \
     --template-body file://labs/11-cloudformation-cdk/template-broken.yaml
   aws cloudformation wait stack-update-complete --stack-name soa-c03-lab11
   ```

4. Kết quả: `UPDATE_COMPLETE`, **4 resource**; `./bin/lab verify 11` PASS (08:45:34Z).

6. Prevention / automation

- **Không hardcode ID** trong template: dùng `Parameters:` (truyền vào lúc deploy) hoặc
  `!ImportValue` lấy từ Output/Export của core stack.
- Chạy **change set** trước khi update để thấy trước resource nào sẽ `Add/Modify/Replace`.
- Giới hạn quyền `cloudformation:UpdateStack` cho role vận hành; mọi thay đổi template đi qua review.
- Coi `UPDATE_ROLLBACK_COMPLETE` là **cảnh báo**, không phải "xong": stack đã về bản cũ nhưng
  thay đổi bạn muốn vẫn **chưa** được áp dụng.

7. Exam trap

- `ROLLBACK_COMPLETE` = **tạo lần đầu** thất bại → stack rỗng, **không update tiếp được**,
  phải `Delete stack` rồi tạo lại.
- `UPDATE_ROLLBACK_COMPLETE` = **update** thất bại nhưng đã quay về bản cũ → stack **vẫn dùng được**,
  update lại bình thường.
- Đọc **event `*_FAILED` đầu tiên**; event phía trên là cascade (`cancelled`), đọc event cuối là
  đọc triệu chứng, không phải nguyên nhân.
- `HandlerErrorCode: InvalidRequest` + lỗi "does not exist" = **tham chiếu sai**;
  `AccessDenied` mới là thiếu quyền. Đừng sửa IAM khi lỗi là tham chiếu.
- `cdk synth` chỉ **dịch ra template ở máy**, không deploy, không tạo resource nào.

## Chưa làm (ghi lại để lần sau)

- **Drift**: chưa thử sửa tay một resource rồi `Detect drift` → `DRIFTED` → sửa lại.
- **CDK synth**: máy chưa cài `cdk` / `aws-cdk-lib`; chưa chạy `cdk synth` trong `labs/11-cloudformation-cdk/cdk`.
