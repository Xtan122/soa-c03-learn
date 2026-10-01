# 📒 Lab Note Template

> Copy block dưới vào cuối mỗi lab. Chỉ 5 dòng — ngắn, đủ để ôn lại.

```text
LAB:
SERVICE:
DATE:
PHASES: Build [ ] Break [ ] Diagnose [ ] Fix [ ] Verify [ ] Cleanup [ ]

1. What did I build?
2. What failed?
3. How did I detect it?
4. How did I fix it?
5. What exam trap did I learn?
```

---

## Ví dụ đã điền

```text
LAB: VPC Troubleshooting
SERVICE: VPC / NAT Gateway

1. Private EC2 → NAT → Internet
2. Route table missing 0.0.0.0/0
3. Checked route table + connectivity
4. Added route to NAT
5. SG allows traffic ≠ route exists
```

## Mẹo ghi
- Dòng 5 là **giá trị nhất** cho kỳ thi — ghi "trap" dạng: *"SG allows traffic ≠ route exists"*.
- Nếu lab có nhiều lỗi, thêm dòng con `2a`, `2b`…
- Cuối tuần, đọc lại 5 dòng × 6–7 lab để ôn nhanh.

---

⬅️ [README](../README.md)
