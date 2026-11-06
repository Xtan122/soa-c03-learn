# LAB 19 — AWS Backup, Config, Cost Explorer, Budgets

```text
LAB: 19 — AWS Backup, Config, Cost Explorer, Budgets
SERVICE:
DATE: 2026-11-06
DOMAIN: D2/D3
PHASES: Build [x] Break [x] Diagnose [x] Fix [ ] Verify [x] Cleanup [ ]
```

1. What did I build?
vault soa-c03-lab19, plan daily → tag Backup=lab19, on-demand job cho soa-c03-db, recorder + rule encrypted-volumes, budget $5
2. What failed? (symptom, not root cause)
symptom: Config Recording is off, compliance không cập nhật 
3. How did I detect it? (metric/log/event/CLI)
so baseline (Recording is on) với hiện tại; CloudTrail StopConfigurationRecorder 08:36:53Z, user/xtan, IP, userAgent CLI
4. Root cause (the actual broken layer)
Recorder soa-c03-lab19 bị dừng bằng API StopConfigurationRecorder, gọi bằng access key của IAM user xtan qua AWS CLI lúc 15:36:53 +07. Từ mốc đó Config không ghi configuration item mới và rule encrypted-volumes không được đánh giá lại (lần đánh giá cuối: 15:06). Vì vậy dữ liệu compliance trở thành ảnh chụp cũ — sai lệch mới không bị phát hiện, tạo compliance gap, dù trên console rule vẫn hiện đỏ như cũ.
5. How did I fix it? (exact command or console action)
AWS Config → Settings → Start recording; verify 19 PASS 08:46:27Z
6. Prevention / automation
IAM tách quyền / deny config:StopConfigurationRecorder; EventBridge (eventName) → SNS; SCP chỉ ở mức lý thuyết
7. Exam trap
Completed ≠ restore được; budget không chặn + không alert; Config (state) vs CloudTrail (API); compliance cũ vẫn hiện đỏ; Cost Explorer trễ 24h