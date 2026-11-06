# LAB 17 — Boss fight: 3 lỗi mạng cùng lúc

```text
LAB: 17 — Boss fight: 3 lỗi mạng cùng lúc
SERVICE: EC2 (target group, security group) · ELB/ALB · VPC (NACL, Flow Logs) · Auto Scaling
DATE: 2026-11-04
DOMAIN: D5 Networking 18%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ]
HINTS_USED: 0 · SOLUTION_USED: no
```

## 1. Tôi đã dựng cái gì?

Đường đi của request (theo đúng thứ tự gói tin):

```text
Client → ALB (port 80, ALB SG)
       → NACL của subnet app (stateless, đánh số rule, xét từ số nhỏ lên)
       → SG của ENI app (stateful, cho TCP 8080 từ ALB SG)
       → EC2 app (port 8080)
```

ALB kiểm tra sức khoẻ target bằng HTTP GET tới **port 8080**, đường dẫn lấy từ
**Health checks** của target group `soa-c03-tg`. VPC Flow Logs ghi lại từng kết nối
vào log group `/aws/vpc/soa-c03/lab17` với trạng thái `ACCEPT`/`REJECT`.

## 2. Triệu chứng (chưa phải nguyên nhân)

Target group `soa-c03-tg` báo **1 Unhealthy / 0 Healthy**. Triệu chứng đổi theo
từng lớp được sửa:

```text
Lần đo 1  → "Request timed out"                        (không có phản hồi nào)
Lần đo 2  → "Health checks failed with these codes: [404]"  (có phản hồi, sai mã)
Lần đo 3  → Healthy, /health = 200
```

Điểm cần nhớ: `Time out` và `404` là **hai triệu chứng khác bản chất**, không phải
cùng một lỗi ở hai thời điểm.

## 3. Tôi phát hiện bằng cách nào?

Kiểm tra từ trong ra ngoài, mỗi lớp một bằng chứng:

| Lớp | Nơi xem | Giá trị đọc được |
|---|---|---|
| Target health | EC2 → Target groups → `soa-c03-tg` → Targets | `Unhealthy`, details `Request timed out` |
| Security group | EC2 → Security groups → `sg-01ccd0e7a27ee4289` → Inbound rules | **0 permission entries** |
| NACL | VPC → Network ACLs → `acl-08f013cbc6f33dbb1` → Inbound rules | rule **50 Deny TCP 8080 0.0.0.0/0** đứng trước rule 100 Allow all |
| Health check path | Target group → Health checks | `Path = /nope`, Success codes `200` |
| Flow Logs | `/aws/vpc/soa-c03/lab17` | cùng cặp IP/port 8080 có `ACCEPT` (trước phá) và `REJECT` (sau phá) trong cửa sổ 07:24:00–07:24:29Z |

Bằng chứng phụ: ASG đã **thay máy** trong lúc diagnose —
`i-0e2b1232866e58069` → `i-096b7f52c1aa1b9fe` (launch 07:37:27Z). Vì vậy mọi số liệu
đo trên IP cũ (10.42.1.97) không còn giá trị; phải đọc lại theo instance ID mới.

## 4. Nguyên nhân gốc — 3 lỗi độc lập ở 3 lớp

1. **Security group** `sg-01ccd0e7a27ee4289` (app): không còn inbound rule nào
   ⇒ không cho TCP 8080 từ ALB SG ⇒ gói bị chặn ngay tại ENI.
2. **Network ACL** `acl-08f013cbc6f33dbb1` (default NACL, gắn **cả 4 subnet**):
   rule **50 Deny TCP 8080** được xét trước rule 100 Allow all ⇒ deny thắng.
3. **Health check path** của `soa-c03-tg`: `/nope` thay vì `/health` ⇒ dù mạng thông,
   app trả 404 ≠ success code 200 ⇒ vẫn unhealthy.

Thứ tự che khuất: lớp **mạng** (SG, NACL) che lớp **ứng dụng** (path). Khi gói tin
chưa tới được app thì lỗi path không thể hiện ra, nên không được sửa cả ba cùng lúc.

## 5. Tôi đã sửa thế nào?

| Thứ tự | Lớp | Hành động trên console | Kết quả đo lại |
|---|---|---|---|
| 1 | SG | `Edit inbound rules` → Add rule: Custom TCP **8080**, Source = **sg-0803990c0818758c2** (ALB SG) → Save | vẫn `Request timed out` (NACL còn chặn) |
| 2 | NACL | `acl-08f013cbc6f33dbb1` → Inbound rules → xoá dòng **rule 50 Deny 8080** → Save | đổi sang `404` (lỗi path lộ ra) |
| 3 | Health check | `soa-c03-tg` → Health checks → Edit → Path `/nope` → `/health` → Save | `Healthy`, `/health` 200 |

Verify: **PASS 2026-11-04T07:48:06Z** — `SG=allow NACL=allow path=/health health=200 targets=1`.

Sửa SG bằng **SG reference** (nguồn là ALB SG) chứ không dùng `0.0.0.0/0`, để chỉ
ALB mới gọi được app. NACL sửa trên default NACL là thao tác rủi ro nhất của bài:
nó ảnh hưởng toàn VPC, không riêng máy app.

## 6. Phòng ngừa / tự động hoá

- Đưa cả 3 thứ vào IaC (target group health check path, SG ingress, NACL) và review
  diff trước khi apply — lỗi path và lỗi SG thường lọt qua review thủ công.
- Bật **AWS Config** rule cho `EC2 security group` và `VPC NACL` để phát hiện SG mở
  quá rộng hoặc NACL có deny che khuất.
- Alarm trên `UnhealthyHostCount` của target group (không chỉ alarm 5xx của ALB), vì
  trường hợp chỉ có 1 target thì ALB có thể vẫn trả 200/502 chứ không 503.
- Tạo NACL riêng cho từng subnet thay vì dùng default NACL chung, để một thay đổi
  không lan ra cả VPC.
- Khi debug: luôn ghi lại **instance ID + launch time** cùng evidence, vì ASG thay
  máy sẽ làm số liệu cũ vô nghĩa.

## 7. Bẫy trong đề thi

- **Mã lỗi chỉ lớp, không chỉ nguyên nhân.** `Request timed out` = gói không tới
  hoặc không về (SG/NACL/route). `Response code mismatch [404]` = đã tới app nhưng
  sai đường dẫn. Nhìn mã trước khi mở policy.
- **NACL là stateless và có số thứ tự**: rule số nhỏ xét trước, deny thắng allow;
  chiều về cần rule ephemeral ports riêng. SG thì stateful, không cần rule chiều về.
- **Một lỗi che lỗi khác**: sửa từng lớp rồi đo lại; sửa cả 3 cùng lúc thì mất khả
  năng quy nhân quả, và verify cũng không chỉ ra được lớp nào đã sai.
- **Đừng tin một lần đọc**: health check và ASG trạng thái thay đổi liên tục; phải
  refresh và đo lại sau mỗi lần sửa.

## Chưa làm

- Chưa thử query Logs Insights nâng cao (`filter dstport = 8080 | stats count() by action`);
  chỉ dùng `filter-log-events` qua CLI.
- Chưa kiểm outbound rules của NACL (chiều về ephemeral ports) — bài này chỉ phá
  inbound nên chưa cần.
