# LAB 16 — Private subnet → S3 qua Gateway Endpoint, SSM qua Interface

```text
LAB: 16 — Private subnet → S3 qua Gateway Endpoint, SSM qua Interface
SERVICE:
DATE: 2026-11-03
DOMAIN: D5 Networking 18%
PHASES: Build [x] Break [x] Diagnose [x] Fix [ ] Verify [x] Cleanup [ ]
```

1. What did I build?
1 EC2 private i-087365e5485b4f76f + 4 endpoint (3 Interface + 1 Gateway S3)
2. What failed? (symptom, not root cause)
aws s3 ls treo, không trả lỗi — SSM vẫn vào bình thường
3. How did I detect it? (metric/log/event/CLI)
VPC → Endpoints lọc theo soa-c03-vpc: không còn endpoint Gateway nào
4. Root cause (the actual broken layer)
endpoint Gateway S3 bị xoá hẳn (không phải chỉ detach route table) ⇒ không có route tới S3 trong route table private
5. How did I fix it? (exact command or console action)
Create endpoint: AWS services → com.amazonaws.ap-southeast-1.s3 · Type = Gateway → VPC soa-c03-vpc → Route table soa-c03-private-rt-1 (rtb-0b3d093af04385d70) → Full access
6. Prevention / automation
Gateway endpoint phải được quản lý bằng IaC; cảnh báo khi endpoint biến mất; verify phải chạy aws s3 ls từ trong instance chứ không chỉ describe-vpc-endpoints
7. Exam trap
Cùng tên service s3 có 2 loại endpoint (Gateway miễn phí vs Interface $0.013/h); Gateway phải gắn route table của đúng subnet; xoá Gateway không làm SSM mất kết nối