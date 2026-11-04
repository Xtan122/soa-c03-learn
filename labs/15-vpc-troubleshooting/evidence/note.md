# LAB 15 — VPC: SG, NACL, route, Flow Logs, Reachability

```text
LAB: 15 — VPC: SG, NACL, route, Flow Logs, Reachability
SERVICE: VPC (Security Group, Network ACL) + ELB/ASG
DATE: 2026-11-03
DOMAIN: D5 Networking 18%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ]
SOLUTION_USED: no
```

## 1. What did I build?

App stack `soa-c03-app` (ALB + ASG + 1 EC2 + RDS) ở nền sạch: `/health` 200, `/db` 200,
target `1/1 healthy` (`i-08bfc909cb20e6770`:8080). Lab 15 bật thêm flow log
`/aws/vpc/soa-c03/lab15` và tạo 1 Reachability Analyzer path `nip-0612e4f79491088b6`
(ALB ENI `eni-0a0e3de20024acc2c` → app ENI, TCP 8080).

## 2. What failed?

`curl http://soa-c03-alb-62652118.ap-southeast-1.elb.amazonaws.com/health` trả **504**
(Gateway Timeout). Sau khoảng 2–3 phút, target group chuyển target sang **unhealthy**.

## 3. How did I detect it?

- `curl /health` = **504** ⇒ kết nối client ↔ ALB vẫn thông, lỗi nằm **sau** ALB
  (loại IGW/route phía client).
- EC2 → Security groups → SG của app `sg-053f810da2e593afa` → tab **Inbound rules**:
  danh sách **trống**.
- VPC → Network ACLs → `acl-08f013cbc6f33dbb1` (default NACL của `soa-c03-vpc`):
  **rule 100 All traffic 0.0.0.0/0 Allow** (rule `* Deny` chỉ là mặc định cuối)
  ⇒ NACL **không** phải lớp chặn.
- ASG → **Activity**: `i-08bfc909cb20e6770` bị **terminate 08:43:23Z**
  (cause "ELB system health check failure"), `i-0281b45c982e49406` **launch 08:43:25Z**.

## 4. Root cause

SG của app (`sg-053f810da2e593afa`) **không còn inbound rule TCP 8080** từ SG của ALB
(`soa-c03-app-AlbSecurityGroup-05BW7kUqSZa9` = `sg-0440b96a1db12a2ea`). Vì vậy gói SYN
từ ALB tới app:8080 bị **DROP im lặng**, ALB chờ hết timeout rồi trả **504**; health check
fail liên tiếp (interval 15s) nên target bị đánh **unhealthy**, và ASG **thay instance**
trong lúc sự cố. NACL và route không tham gia vào lỗi này.

## 5. How did I fix it?

Console: EC2 → **Security groups** → `sg-053f810da2e593afa` → tab **Inbound rules** →
**Edit inbound rules** → **Add rule**: `Custom TCP`, port range `8080`,
Source type `Custom`, Source = `sg-0440b96a1db12a2ea` (SG của ALB) → **Save rules**.

Kết quả: target về **Healthy lúc 15:54:20** (dự đoán trước khi bấm ~30s, khớp).
`./bin/lab verify 15` **PASS** lúc `2026-11-03T09:03:47Z`
(`SG rule present, app=200, reachability=reachable`).

## 6. Prevention / automation

- Bật **AWS Config** (managed rule/custom rule) để phát hiện SG drift — cụ thể là rule
  8080 từ ALB SG bị xoá — và gửi cảnh báo qua SNS.
- Alarm trên `UnHealthyHostCount` của target group và `TargetResponseTime`/`5XX` của ALB
  để biết sớm hơn thay vì đợi người dùng báo.
- Quy ước: SG chỉ mở port cho **SG nguồn** (không `0.0.0.0/0`), và mọi thay đổi SG phải
  đi qua CloudFormation/IaC, không sửa tay trên console.

## 7. Exam trap

- **SG stateful** (chỉ cần rule chiều vào) ≠ **NACL stateless** (phải cho cả ephemeral port
  chiều về). Thiếu chiều về thì kết nối vẫn chết dù inbound đúng.
- Mã lỗi: **504** = gói bị drop im lặng nên ALB chờ hết timeout; **502** = target từ chối
  kết nối (gói đã tới được máy); **503** = không còn target khoẻ nào. Stack này chỉ có
  1 target nên ALB fail-open ⇒ gặp 504 chứ không phải 503.
- Health check fail không chỉ làm target unhealthy mà còn khiến **ASG terminate/launch**.
  Trạng thái cuối "healthy" có thể là **một máy khác** ⇒ phải đọc ASG Activity, đừng chỉ
  nhìn `/health` = 200.

## Chưa làm

- Chưa tự chạy **Flow Logs Insights** để đọc `action=REJECT` (verify có chạy Reachability
  Analyzer nhưng mình chưa tự xem từng hop ACCEPT/BLOCKED trên console).
