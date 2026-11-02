# Người mới bắt đầu ở đây

> Bạn không cần biết AWS trước. Bạn chỉ cần biết **đang ở đâu** và **bấm gì tiếp**.
> File này dạy bạn cách đọc lab, cách bấm an toàn, và cách nói với AI để được
> chỉ đến từng nút.

---

## 1. Bạn cần chuẩn bị 3 thứ

| Thứ | Lấy ở đâu | Ví dụ |
|---|---|---|
| Account + region | `make doctor` | account lab, `ap-southeast-1` |
| Lab ID | `./bin/lab list` | `01` |
| App stack đang bật hay tắt | `./bin/lab status` | `app : CREATE_COMPLETE` |

Nếu `make doctor` báo lỗi, dừng lại và sửa trước. Không học trên nền gãy.

---

## 2. Đọc lab README theo thứ tự này

Đừng đọc từ trên xuống hết ngay. Đọc theo thứ tự:

1. **Mục 0 — Đọc nhanh (60 giây).** Biết hôm nay làm gì, bấm ở đâu trước, xong khi nào.
2. **Mục 1–3.** Lab này về gì, hiện có gì, luồng đi của dữ liệu.
3. **Mục 5c — Console.** Đường bấm từng bước. Đây là phần quan trọng nhất với người mới.
4. **Mục 6–7.** Hiện tượng bạn sẽ thấy và nơi cần xem.
5. **Mục 8.** Thế nào là thành công.
6. **Mục 10–11.** Câu hỏi note và cleanup.

Mục 9 (exam takeaway) đọc sau khi làm xong. Mục 12 chỉ đọc khi bí.

> Mẹo: `./bin/lab console <id>` in đúng mục 5c ra terminal, không cần mở file.

---

## 3. Thẻ 60 giây

Mỗi README bắt đầu bằng:

```text
## 0. Đọc nhanh (60 giây)
- Bạn sẽ làm gì
- Việc đầu tiên
- Xong khi
- Nếu lạc
```

Nếu chỉ có 1 phút, đọc 4 dòng đó. Nếu vẫn không rõ, mở mục 5c.

## 3b. Trước khi AI phá: brief + baseline

Bạn không cần diagnose khi còn mù. Trước `break`, chạy:

```bash
./bin/lab brief 03          # kiến thức + hệ thống hiện tại + bản đồ + 3 câu hỏi
./bin/lab baseline 03 --live # đọc trạng thái thật, read-only
```

Trả lời 3 câu dự đoán trong brief, rồi:

```bash
./bin/lab brief 03 --confirm
```

Sau đó mới `break`. Nếu AI định phá mà chưa brief, bạn nói:

```text
Dừng. Cho tôi brief + baseline trước. Tôi chưa biết hệ thống đang có gì.
```

---

## 4. Cách bấm an toàn

Trước khi bấm: mở <https://console.aws.amazon.com/>, đăng nhập **đúng account lab**
(không dùng account cá nhân), chọn region **Singapore (ap-southeast-1)**.

AWS Console có 2 loại màn hình:

| Loại | Ví dụ | Có sửa gì không? |
|---|---|---|
| **Xem** (read-only) | Alarms, Metrics, Log groups, Target health, Events | Không sửa, bấm thoải mái |
| **Thay đổi** | `Edit`, `Create`, `Delete`, `Terminate`, `Reboot`, `Restore` | Có, phải hỏi AI trước |

Quy tắc:

1. **Không bấm** `Delete`, `Terminate`, `Reboot`, `Restore`, `Create` khi chưa hỏi AI.
2. Trước khi bấm nút thay đổi, đọc to: nút gì, ở đâu, sẽ đổi gì.
3. Nếu không chắc, **dừng**. Hỏi AI: “Nút này có sửa gì không?”
4. Không sửa 2 thứ cùng lúc. Sửa 1 thứ, rồi verify.
5. Không xoá stack để “fix”. Đó là trốn bài.

### Nút nên tránh trong lúc diagnose

- `Delete`, `Terminate instances`, `Delete stack`, `Delete DB instance`
- `Reboot` (trừ lab 08), `Failover`
- `Restore` (trừ lab 07)
- `Create` bất kỳ resource mới

---

## 5. Cách nói với AI để được chỉ từng nút

Copy một trong các câu sau:

### Khi mới bắt đầu

```text
Tôi là người mới. Mỗi lần chỉ cho tôi MỘT màn hình và MỘT nút.
Nói rõ: service → menu trái → trang → tab → nút.
Nói tôi sẽ thấy gì, và hỏi lại trước khi đi tiếp.
Đừng đưa đáp án trong 20 phút đầu.
```

### Khi không thấy mục AI nói

```text
Tôi không thấy mục đó. Đừng lặp lại.
Hỏi tôi đang thấy menu/tab nào, rồi đổi cách chỉ.
```

### Khi không hiểu

```text
Tôi chưa hiểu. Đổi ví dụ khác, vẽ sơ đồ nhỏ hơn, rồi hỏi tôi 1 câu.
Đừng thêm quá 1 thuật ngữ mới.
```

### Khi sợ bấm nhầm

```text
Nút này có sửa gì không? Có tốn tiền không? Undo thế nào?
Nếu chỉ để xem, nói rõ là read-only.
```

### Khi bấm nhầm

```text
Tôi vừa bấm nhầm <nút> ở <màn hình>. Dừng lại.
Hướng dẫn tôi kiểm tra hậu quả bằng read-only trước.
```

---

## 6. Khi bị lạc trong console

Làm đúng thứ tự, mỗi lần một bước:

1. Nhìn góc trên phải: có phải **Singapore (ap-southeast-1)**?
2. Bấm ô **Search** trên cùng, gõ tên service (CloudWatch, EC2, RDS...).
3. Nhìn menu trái: mục bạn cần có thể đổi tên.
4. Hỏi AI: “Tôi đang thấy các mục A, B, C. Mục nào gần nhất?”
5. Nếu vẫn lạc, dùng CLI tương đương; quay lại console sau.

Không bấm bừa để “thử”. Không mở 10 tab.

---

## 7. Cách đọc một màn hình

Mỗi lần mở một trang, tự hỏi 3 câu:

```text
1. Tôi đang ở đâu? (service → trang → tab)
2. Ô quan trọng nhất đang ghi gì? (state, status, count, path, port)
3. Giá trị đó đúng hay sai? Dựa vào đâu? (mục 8 của README)
```

Nếu không trả lời được câu 2, đừng bấm tiếp. Hỏi AI.

---

## 8. Mẹo dùng console

- **Zoom**: `Ctrl` + `+` để chữ to hơn.
- **Search**: `Ctrl` + `F` chỉ tìm trong trang, không tìm resource.
- **Copy tên**: bấm vào tên resource để copy, dán vào chat cho AI.
- **Không mở quá 3 tab**: dễ mất context.
- **Refresh** sau khi sửa: console có thể giữ dữ liệu cũ vài giây.
- **Đọc nhãn tiếng Anh**: AI sẽ giải thích, nhưng bạn có thể hỏi “Edit là gì?”.

---

## 9. Từ điển

- Thuật ngữ cốt lõi: bảng trong [`docs/beginner-mentor.md`](beginner-mentor.md) mục 2.
- Toàn bộ thuật ngữ theo lab: [`docs/glossary.md`](glossary.md).
- Đường bấm và deep link: [`docs/console-guide.md`](console-guide.md).

---

## 10. Checklist buổi đầu

- [ ] `make doctor` không lỗi.
- [ ] Biết account/region đang dùng.
- [ ] Biết lab ID hôm nay.
- [ ] Đọc mục 0 + 5c của README.
- [ ] Nói với AI: “mỗi lần một màn hình, một nút”.
- [ ] Không bấm nút xoá/terminate khi chưa hỏi.
- [ ] Kết thúc: `./bin/lab verify`, `note`, `down`, `make cost`.
