# Lab readiness — rà soát 24 lab

> Ngày rà static: **2026-10-25**, cập nhật brief 24 lab: **2026-10-26**. Phạm vi: `up` path, idempotency, cleanup,
> console guidance, manifest.
>
> **Chưa chạy `up` thật cho cả 24 lab** vì mỗi lần `up` tạo tài nguyên và tốn
> tiền. Vì vậy tài liệu này tách rõ:
> - **Static**: đã kiểm tra bằng tool, không tốn tiền.
> - **Live**: chỉ chạy read-only, không tạo tài nguyên.
> - **Runtime**: phải chạy khi có approval và có cleanup.

---

## 1. Cách tự kiểm tra trước khi `up`

```bash
# Offline: manifest, function, console guide, tên tài nguyên
./bin/lab preflight 05

# Read-only AWS: account, core/app, leftover resource, NAT/EIP/EKS/Multi-AZ
./bin/lab preflight 05 --live

# Audit cả 24 lab, offline
make audit
```

`preflight --live` **không tạo/sửa/xoá gì**. Nó chỉ gọi `describe-*`/`list-*`
sau khi in account/ARN. Nếu account khác `LAB_ACCOUNT_ID`, nó dừng.

`bin/lab up` cũng tự chạy static check trước khi build. Nếu static fail, `up`
dừng trước khi gọi AWS.

---

## 2. Ma trận readiness

| Lab | App? | `up` idempotent? | Điều kiện chính | Rủi ro còn lại |
|---:|---|---|---|---|
| 00 | Không | Có (chỉ kiểm tra core) | core healthy | Chưa bootstrap thì `up` sẽ chạy bootstrap (tạo tài nguyên) |
| 01 | Có | Có (SQS/alarm/subscription tái sử dụng) | app healthy, SSM để xem process | CPU load 30', ASG suspend; verify cần alarm còn ALARM |
| 02 | Có | Có (metric filter/alarm là put) | app healthy, agent online | log/metric trễ 30–90s |
| 03 | **Không** | Có (canary rebuild) | core + CloudTrail | CloudTrail có thể trễ vài phút; canary t4g.nano |
| 04 | Có | Có | app healthy | EventBridge chỉ bắt state **change** |
| 05 | Có | Có | app healthy | health check cần ~45s mới unhealthy |
| 06 | Có | Có (giữ version gốc khi `up` lại) | app healthy | scale lên 2 instance (tốn thêm); ASG activity cần thời gian |
| 07 | Có | Có (snapshot cũ được thay) | app healthy, RDS available | snapshot/restore có thể vài phút; restore là thao tác tay |
| 08 | Có | Có (bỏ qua nếu đã Multi-AZ) | app healthy | 10–12 phút; Multi-AZ tốn gấp đôi, phải `down` |
| 09 | Có | Có | app healthy, SSM online | agent/role/endpoint |
| 10 | Có | Có (key policy gốc được giữ) | app healthy, `sts:AssumeRole` | quyền AssumeRole của user; key policy áp dụng chậm vài giây |
| 11 | Không | Có (`deploy --no-fail-on-empty-changeset`) | core | stack `ROLLBACK_COMPLETE` phải xoá, không update tiếp |
| 12 | Có | Có (Lambda xoá/tạo lại, permission reset) | app healthy, core Lambda role | role/permission propagation; canary rebuild |
| 13 | **Không** | Có (role tái sử dụng) | core, `sts:AssumeRole` | trust policy sai; user thiếu quyền assume |
| 14 | **Không** | Có (bucket/analyzer tái sử dụng) | core | Access Analyzer finding có thể trễ |
| 15 | Có | Có (flow log/path được thay) | app healthy | Flow Logs trễ 5–10 phút; Reachability Analyzer chỉ kiểm tra config |
| 16 | **Không** | Có (instance/endpoint được dọn trước) | core, private subnet | Interface endpoint tốn phí; private DNS |
| 17 | Có | Có (flow log được thay) | app healthy | 3 lỗi cùng lúc; NACL stateless |
| 18 | Có | Có (cluster/service tái sử dụng) | app healthy, Fargate | pull `public.ecr.aws`; execution role |
| 19 | Có | Có (plan/job tái sử dụng) | app healthy, RDS | Backup/Config chậm; Cost Explorer trễ 24h |
| 20 | Có | Có (không tạo resource riêng) | app healthy | CPU load; ASG có thể scale |
| 21 | Có | Có (SG/policy là put) | app healthy | DB SG + IAM deny; policy propagation |
| 22 | Có | Có (plan tái sử dụng, alarm/dashboard tạo lại) | app healthy, dashboard | ASG thay instance có thể tới 10 phút |
| 23 | Có | Có (SG/policy là put) | app healthy | 5 lỗi; verify từng lớp |

**Thay đổi quan trọng so với audit cũ:**

- Lab 03 và 16 **không còn cần app stack**. Trước đây chúng gọi `require_app`
  dù chỉ dùng core; nay dùng `require_core`, giảm một dependency tốn tiền.
- Lab 13 và 14 trước đây khai `NEEDS_APP=yes` nhưng code chỉ dùng core; nay
  `NEEDS_APP=no`, khớp với thực tế.
- Lab 22 trước đây verify đòi dashboard + ≥4 alarm nhưng `up 22` không tạo;
  nay `up 22` tạo dashboard và 4 alarm baseline.
- Lab 06 trước đây `up` lại sau `break` sẽ lưu nhầm launch template version
  hỏng làm "bản gốc"; nay giữ version gốc.
- Lab 10 trước đây `up` lại sau `break` có thể lưu key policy đang chứa deny
  làm "bản gốc"; nay giữ bản sạch và xoá statement `Lab10*`.
- Lab 16 trước đây `up` lại tạo thêm endpoint/instance; nay dọn theo
  `var/lab16.env` + tag `Lab=lab16`.
- Lab 07/19/22 trước đây tạo snapshot/backup plan trùng; nay tái sử dụng hoặc
  thay thế có kiểm soát.
- Lab 15/17 trước đây tạo thêm flow log; nay dọn flow log cũ của chính lab.

---

## 3. Lỗi đã tìm thấy và đã sửa

| Lab | Lỗi | Hậu quả nếu không sửa | Sửa |
|---:|---|---|---|
| 03, 12 | `create_canary` tạo SG trùng | `up` lần 2 fail `InvalidGroup.Duplicate` | rebuild canary: dọn cũ, tạo lại, fallback describe SG |
| 12 | `lambda add-permission` không idempotent | `up` lần 2 fail `ResourceConflictException` | `remove-permission` trước `add-permission` |
| 07 | `create-db-snapshot` trùng tên | `up` lần 2 fail `DBSnapshotAlreadyExists` | xoá snapshot cũ, chờ deleted, tạo lại |
| 08 | modify Multi-AZ khi đã bật | có thể lỗi/không cần thiết | kiểm tra `MultiAZ`, bỏ qua nếu đã bật |
| 10 | key policy "gốc" bị nhiễm deny | `down 10` không gỡ được deny | lưu bản sạch một lần, xoá statement `Lab10*` |
| 15 | Reachability path trùng | tạo path mới mỗi `up`, tốn/khó dọn | xoá path cũ theo var + tag |
| 16 | endpoint/instance trùng | tạo thêm ENI/endpoint tốn phí | dọn theo var + tag trước khi tạo |
| 17 | flow log trùng | log group/flow log thừa | `enable_lab_flow_logs` dọn suffix cũ trước |
| 19, 22 | backup plan trùng | nhiều plan, khó cleanup | tái sử dụng plan theo tên; selection/job có kiểm tra |
| 22 | verify đòi alarm/dashboard không được tạo | verify fail dù làm đúng | `up 22` tạo dashboard + 4 alarm |
| 01 | biến `qarn` không `local` | rò biến, shellcheck warning | thêm `local` |
| 13, 14 | manifest `NEEDS_APP=yes` sai | `down` chờ app không cần thiết | đổi `no` |
| 03, 16 | `require_app` không cần | buộc bật app stack tốn tiền | đổi `require_core` |

---

## 4. Điều static check **không** chứng minh

- CloudFormation có deploy được không (IAM, quota, AMI, package).
- RDS restore có kịp thời gian trong buổi lab không.
- Fargate pull được `public.ecr.aws` trong account này không.
- Backup/Config có đủ quyền service role không.
- AWS có đổi console/API sau ngày rà không.

Vì vậy trước mỗi buổi:

```bash
make doctor
./bin/lab preflight <id> --live
```

Nếu `preflight --live` báo warn/fail, xử lý trước khi `up`. Nếu `up` fail,
đọc lỗi đầu tiên, không chạy lại mù.

---

## 5. Definition of ready cho một lab

- [ ] `./bin/lab preflight <id>` PASS (static).
- [ ] `./bin/lab preflight <id> --live` không còn FAIL/WARN về leftover.
- [ ] Core stack `CREATE_COMPLETE`/`UPDATE_COMPLETE`.
- [ ] Nếu `NEEDS_APP=yes`: app `CREATE_COMPLETE`, `/health` 200, target healthy.
- [ ] Không có NAT/EKS/Multi-AZ RDS ngoài kế hoạch.
- [ ] Đã đọc mục **0** và **5c** của lab.
- [ ] Nếu lab tốn tiền theo giờ (07, 08, 15, 16, 18, 19, 22, 23): đã thống nhất
      thời gian và lệnh cleanup.

## 6. Teaching readiness (chất lượng hướng dẫn)

- [ ] README có mục **0. Đọc nhanh** và **5c. Console** (static check bắt buộc).
- [ ] Mục 5c có từ vựng trước khái niệm; khái niệm là bullet ngắn.
- [ ] Mỗi bước có màn hình + nút + ô cần đọc; không có placeholder.
- [ ] Có checkpoint trước khi bấm tiếp.
- [ ] AI đã đọc `docs/ai-mentor-runbook.md` và dùng mẫu 6 dòng mỗi lượt.
- [ ] Đã chạy `./bin/lab brief <id>` + `./bin/lab baseline <id> --live` trước break.
- [ ] Người học trả lời được 3 câu dự đoán và giải thích baseline; đã `brief --confirm`.
- [ ] Dùng `./bin/lab teach <id>` cho I do → We do → You do.
- [ ] Người học đã đọc `docs/learner-quickstart.md` (5 phút).
- [ ] AI chỉ một màn hình + một nút mỗi lượt, chờ “xong” rồi đi tiếp.
- [ ] Không paste cả mục 5c; không nói “vào ... tìm đi”.
- [ ] Trong 20 phút đầu: chỉ đường bấm (navigation) nhưng không nói root cause.
