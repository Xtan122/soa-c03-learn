# Progress

- `events.jsonl` — append-only log do `./bin/lab` ghi: `up`, `break`, `verify`, `reset`, `down`.
- `labs/<id>/evidence/DONE` — marker khi `verify` PASS.
- `labs/<id>/evidence/note.md` — root cause + evidence.
- `labs/<id>/evidence/verify-last.txt` — output lần verify gần nhất.

Xem nhanh:

```bash
./bin/lab progress
./bin/lab list
```

Kiểm tra gian lận với chính mình:

```bash
grep '"action":"reset"' progress/events.jsonl
```

Nếu có nhiều `reset`, bạn đang đọc đáp án quá sớm. Ghi lý do vào note và làm lại lab đó
sau 2 ngày.
