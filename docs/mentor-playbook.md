# Mentor playbook

> Tôi sẽ mentor bạn như một senior CloudOps: ngắn, thẳng, không ru ngủ.
> Mục tiêu không phải "học hết", mà là **phản xạ đúng khi hệ thống chết**.
>
> **Người mới:** đọc [`docs/learner-quickstart.md`](learner-quickstart.md) và
> [`docs/console-guide.md`](console-guide.md) trước. File này là tầng chiến lược,
> không phải hướng dẫn bấm từng nút.

---

## 1. Ba nguyên tắc

### 1. Tay phải chạm trước khi não tin

Bạn chỉ biết một thứ khi đã:

- dựng nó,
- phá nó,
- tìm ra nó hỏng ở đâu,
- sửa nó,
- và chứng minh bằng output.

Đọc docs 10 phút trước lab là đủ. Xem video 60 phút là trốn việc.

### 2. Symptom không phải root cause

`CPU 95%` là symptom. `ALB 503` là symptom. `AccessDenied` là symptom.

Câu hỏi của CloudOps là: **lớp nào trong chuỗi đang chặn?**
Identity → network → compute → data → config → observability.

### 3. Không sửa bằng cách xoá

Xoá stack rồi deploy lại là trốn bài. Bạn phải sửa đúng lớp đang hỏng,
rồi chứng minh bằng `verify`.

---

## 2. Daily ritual (2.5–3.5h)

```text
10'  Đọc task statement trong exam guide
10'  Vẽ luồng: user → ALB → app → DB → log/metric
5'   Viết 3 giả thuyết hỏng
90'  ./bin/lab up <id> → break → diagnose mù → fix
20'  ./bin/lab verify <id>; lưu evidence
10'  ./bin/lab note <id>
10'  ./bin/lab down <id>; make cost
```

Quy tắc 20 phút:

- 20 phút đầu **không** xem hint, không AI, không docs.
- Viết ra giấy: "Tôi nghi X vì Y. Nếu X sai, evidence nào sẽ nói vậy?"
- Hết 20 phút mới dùng hint 1. Hint 2 sau 10 phút nữa. Reset chỉ sau khi đã thử.

---

## 3. Khung chẩn đoán 6 bước

### Bước 1 — Chốt symptom

- Ai bị ảnh hưởng? 1 user, 1 AZ, cả fleet?
- Bắt đầu khi nào? Trước đó thay đổi gì?
- 200 hay 500? Timeout hay connection refused?

### Bước 2 — Vẽ chuỗi

Ví dụ ALB:

```text
DNS → ALB listener → target group → health check → SG → app :8080 → DB
```

### Bước 3 — Chọn evidence rẻ nhất

| Câu hỏi | Evidence |
|---|---|
| App có sống? | `/health`, target health |
| App có vào DB? | `/db`, RDS connections |
| Request có tới app? | ALB access logs, VPC Flow Logs |
| App có lỗi gì? | Logs Insights, journalctl |
| Ai đổi gì? | CloudTrail |
| Quyền có chặn? | IAM policy simulator, Access Analyzer |

### Bước 4 — Loại trừ

Đừng "kiểm tra hết". Chọn evidence **chia đôi không gian giả thuyết**.

Ví dụ: target unhealthy + SG đúng → nhìn health check path/port/app listen,
không đi soi NACL.

### Bước 5 — Fix nhỏ nhất

Sửa 1 thứ, chạy verify, quan sát. Không sửa 3 thứ cùng lúc.

### Bước 6 — Viết lại

3 dòng:

- Root cause là gì.
- Evidence nào chứng minh.
- Guardrail nào ngăn tái diễn.

---

## 4. Hợp đồng dùng AI

AI là **junior rất nhanh** và **senior rất khó tính**, không phải người làm hộ.

### Được dùng

- Sinh IaC/script/boilerplate.
- Review reasoning của bạn sau khi đã tự chẩn đoán.
- Tạo thêm 5 câu hỏi trắc nghiệm từ lab vừa làm.
- Giải thích một service khó bằng 5 dòng.
- Chỉ từng màn hình, từng nút trên console (AI phải theo
  [`docs/ai-mentor-runbook.md`](ai-mentor-runbook.md)).

### Không được dùng

- Trong 20 phút diagnose đầu tiên.
- Để AI đọc `scripts/lib/labs.sh` rồi nói đáp án.
- Để AI viết postmortem thay bạn.
- Copy output AI mà không chạy lại.
- Để AI đưa 5 bước console một lúc rồi bảo “làm đi”.

### Prompt mẫu sau lab

```text
Tôi vừa làm lab 05 (ALB 503). Đây là evidence:
<paste>
Đừng nói đáp án. Hãy đặt 5 câu hỏi để kiểm tra xem tôi có thật sự hiểu
lớp nào hỏng và tại sao các giả thuyết khác bị loại.
```

---

## 5. Weekly review (Chủ nhật, 45 phút)

Trả lời bằng giấy:

1. Lab nào tôi phải dùng reset? Vì sao?
2. Root cause nào tôi tìm trong < 10 phút?
3. Domain nào tôi vẫn mơ hồ?
4. Resource nào còn chạy ngoài giờ lab?
5. Tuần sau tôi cắt gì nếu thiếu thời gian?

Chạy:

```bash
make doctor
make inventory
make cost
./bin/lab progress
```

---

## 6. Thang điểm incident

| Điểm | Biểu hiện |
|---:|---|
| 1 | Sửa được sau khi xem đáp án |
| 2 | Tự tìm root cause trong 20 phút |
| 3 | Tìm trong 10 phút, giải thích được evidence |
| 4 | Fix + thêm alarm/automation |
| 5 | Dạy lại 3 phút, không nhìn note |

Mục tiêu: lab thường ≥ 3, incident labs (20–23) ≥ 4.

---

## 7. Nếu chỉ còn 2 tuần

Cắt còn 12 lab:

```text
00, 01, 03, 05, 06, 07, 09, 10, 13, 14, 15, 17
```

Bỏ qua ECS, Backup/Config, capstone. Mỗi ngày 1 lab + 30 câu hỏi.
Tuần cuối: 2 đề full + review.

## 8. Nếu chỉ còn 1 tuần

```text
Ngày 1-2: 01, 03, 05, 06
Ngày 3-4: 07, 09, 13, 14
Ngày 5:   15, 17 + cheat sheet
Ngày 6:   đề full #1 + review
Ngày 7:   đề full #2 + review; nghỉ sớm
```

Không học service mới. Chỉ vá domain yếu.

---

## 9. Ngày thi

- 65 câu / 130 phút. Đọc đáp án trước, tìm keyword.
- Câu nào > 2 phút: flag, chuyển.
- Keyword: *MOST cost-effective*, *LEAST operational overhead*, *MOST secure*,
  *real-time*, *HA across AZs*.
- Managed/automation thường thắng manual.
- Không bỏ trống.
- Trước khi thi: `make app-down`, `make cost`, ngủ đủ.

## 10. Ngày 01/12

```bash
DRY_RUN=yes make cleanup
CONFIRM_DESTROY=yes make cleanup
make inventory
make cost
```

Mục tiêu: `make inventory` rỗng, Cost Explorer về 0. Nếu còn ENI/SG/EIP, xử lý ngay
trước khi credit hết hạn 03/12.

---

## 11. Câu hỏi mentor hỏi bạn mỗi ngày

1. Hôm nay bạn **tự** tìm ra gì mà hôm qua chưa biết?
2. Evidence nào bạn đã bỏ qua lúc đầu?
3. Nếu gặp lại lúc 2h sáng, 3 bước đầu là gì?
4. Guardrail nào bạn thêm để không phải gặp lại?
5. Bạn đã dọn sạch chưa?
