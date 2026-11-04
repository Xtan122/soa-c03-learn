# LAB 16 — Private subnet → S3 qua Gateway Endpoint, SSM qua Interface

```text
LAB: 16 — Private subnet → S3 qua Gateway Endpoint, SSM qua Interface
SERVICE: VPC Endpoints (Gateway + Interface), EC2, Systems Manager
DATE: 2026-11-04
DOMAIN: D5 Networking 18%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [x]
SOLUTION_USED: no
HINTS_USED: 0
```

## 1. What did I build?

Một EC2 nằm hoàn toàn trong private subnet, **không có public IP** và **không có NAT
Gateway**, kèm 4 VPC endpoint:

| Endpoint | Type | Dùng cho |
|---|---|---|
| `ssm`, `ssmmessages`, `ec2messages` | Interface | SSM Session Manager / Run Command |
| `s3` | Gateway | `aws s3` |

Instance: `i-087365e5485b4f76f`. Interface endpoint tốn **$0.013/giờ/AZ**
(Price List `ap-southeast-1`, hiệu lực 2026-11-01), gateway endpoint **miễn phí**.

## 2. What failed? (symptom, not root cause)

Chạy `aws s3 ls` **từ bên trong** instance (qua Session Manager): lệnh **treo**,
không trả về kết quả và cũng **không báo lỗi** trong nhiều phút.

Trong khi đó SSM vẫn hoạt động bình thường — tôi mở được Session Manager và gõ
lệnh trên chính máy đó.

## 3. How did I detect it? (metric/log/event/CLI)

Console → **VPC** → **Endpoints**, lọc theo VPC `soa-c03-vpc`
(`vpc-03a3584329e94b60e`): chỉ còn **3 endpoint Interface**, **không còn endpoint
Gateway nào** (baseline trước khi phá là 4).

Hai chi tiết định hướng chẩn đoán:

- **Treo, không lỗi** ⇒ gói tin bị **nuốt** trên đường đi (không có route), chứ
  không phải bị từ chối quyền — nếu sai quyền sẽ thấy `AccessDenied` ngay.
- **SSM vẫn sống** ⇒ lớp mạng cơ bản và interface endpoint không hỏng, khoanh vùng
  được vào đúng đường S3.

## 4. Root cause (the actual broken layer)

Endpoint **Gateway** cho S3 **bị xoá hẳn**, không phải chỉ bị gỡ khỏi route table.

- Gỡ khỏi route table (`detach`): endpoint còn tồn tại, chỉ mất route ⇒ sửa bằng
  cách gắn lại route table.
- Xoá endpoint (`delete`): endpoint biến mất, route do endpoint tự sinh cũng mất
  theo ⇒ **không có route nào** trong route table private trỏ tới S3.

Không có route ⇒ gói tin tới `s3.ap-southeast-1.amazonaws.com` bị drop im lặng ⇒
TCP không bao giờ bắt tay xong ⇒ `aws s3 ls` treo tới timeout. Đây là lý do lỗi
**không** phải 4xx/5xx.

## 5. How did I fix it? (exact command or console action)

Console → **VPC** → **Endpoints** → **Create endpoint**:

1. **Name tag**: để trống (không bắt buộc).
2. **Type**: `AWS services`.
3. **Services**: lọc `s3`, chọn **`com.amazonaws.ap-southeast-1.s3`** có cột
   **Type = `Gateway`** — có một dòng cùng tên nhưng **`Interface`**, chọn nhầm là
   phát sinh phí.
4. **VPC**: `soa-c03-vpc (vpc-03a3584329e94b60e)`.
5. **Route tables**: `soa-c03-private-rt-1 (rtb-0b3d093af04385d70)` — route table
   của subnet `soa-c03-private-1` (`subnet-08e6ba6d560f0afac`), đúng subnet chứa
   instance. Không chọn route table `Main` và không chọn route table của subnet
   public hay subnet private còn lại.
6. **Policy**: `Full access` (mặc định).
7. **Create endpoint**.

Endpoint mới: `vpce-0f31e589da3f9f3e6`, state `available`, route table
`rtb-0b3d093af04385d70`.

## 6. Prevention / automation

- Quản lý VPC endpoint bằng **IaC** (CloudFormation/CDK) để endpoint không thể
  "biến mất" ngoài ý muốn; thay đổi phải qua change set.
- `verify` phải kiểm **hành vi thật** (`aws s3 ls` chạy từ trong instance qua SSM),
  không chỉ `describe-vpc-endpoints` — endpoint có thể tồn tại mà route table vẫn sai.
- Giám sát: alarm trên số lượng endpoint Gateway của VPC, hoặc AWS Config rule cho
  `vpc-endpoint` bị xoá.
- Nhắc chi phí: mỗi interface endpoint tính tiền theo giờ, phải `down` ngay sau lab.

## 7. Exam trap

- **Cùng một service `s3` có 2 loại endpoint**: Gateway (miễn phí, gắn vào route
  table, chỉ S3 và DynamoDB) và Interface (ENI + private DNS, tính tiền theo giờ,
  dùng cho phần lớn service khác). Nhìn tên service là chưa đủ, phải nhìn **Type**.
- Gateway endpoint phải associate với **route table của đúng subnet** đang chứa
  resource; chọn sai route table thì endpoint "available" nhưng vẫn không đi được.
- Interface endpoint **không** gắn route table — nó hoạt động nhờ ENI trong subnet
  và private DNS.
- Xoá Gateway endpoint S3 **không** làm SSM mất kết nối: hai đường độc lập.
- Triệu chứng "treo rồi timeout" khác "lỗi ngay": treo = không có đường đi;
  lỗi ngay (4xx/`AccessDenied`) = có đường nhưng bị từ chối.
