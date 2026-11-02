# Lab contract

Một lab chỉ được tính là xong khi thoả các điều sau, **theo đúng thứ tự**:

0. `./bin/lab preflight <id>` PASS (thêm `--live` nếu có quyền) — không `up`
   trên nền bẩn hoặc khi còn resource trùng.
1. `./bin/lab brief <id>` + `./bin/lab baseline <id> --live`: trả lời 3 câu dự
   đoán, rồi `./bin/lab brief <id> --confirm`. **Không break khi còn mù baseline.**
2. `./bin/lab up <id>` chạy không lỗi.
3. `ALLOW_BREAK=yes ./bin/lab break <id>` inject được fault.
4. Bạn **tự chẩn đoán** mà không đọc `scripts/lib/labs.sh`, theo 3 mức
   I do → We do → You do.
5. `./bin/lab verify <id>` PASS.
6. Có `labs/<id>/evidence/note.md` với root cause, baseline trước break, evidence thật.
7. `./bin/lab down <id>` (và `make app-down` nếu hết buổi) sạch.

Nếu bạn mới dùng console: đọc mục **5c. Console — bấm ở đâu, thấy gì** trong
README, hoặc chạy `./bin/lab console <id>`. Không đoán menu.

## Không được làm

- Sửa bằng cách xoá stack rồi deploy lại. Đó là trốn bài, không phải fix.
- Copy output của người khác hoặc của AI mà không chạy lại.
- Đọc `scripts/lib/labs.sh` trước khi thử ít nhất 3 giả thuyết.
- Để `ALLOW_BREAK=yes` sau khi xong.

## Evidence tối thiểu

```text
labs/<id>/evidence/
├── note.md              # 7 câu hỏi
├── verify-last.txt      # output của lần verify PASS
├── DONE                 # marker tự tạo
└── (tuỳ chọn) *.png, *.json, cli-output.txt
```

## Thang tự chấm

| Điểm | Tiêu chí |
|---:|---|
| 1 | Làm theo README, verify PASS, không hiểu vì sao |
| 2 | Tự tìm ra root cause trong 20 phút |
| 3 | Tìm ra trong 10 phút, giải thích được lớp nào sai |
| 4 | Fix + thêm alarm/automation ngăn tái diễn |
| 5 | Dạy lại được cho người khác trong 3 phút, không nhìn note |

Mục tiêu của 30 ngày: **ít nhất 3 điểm/lab**, các lab incident phải 4.

## Khi bí

```bash
./bin/lab hint 05     # hint tăng dần
./bin/lab reset 05    # dùng sau khi đã thử; ghi nhận "solution used"
```

`reset` không xoá DONE. Nếu đã dùng reset, ghi vào note:

```text
SOLUTION_USED: yes — lý do: ...
```

Trung thực với chính mình quan trọng hơn điểm đẹp.
