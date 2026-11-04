# LAB 15 — VPC: SG, NACL, route, Flow Logs, Reachability

```text
LAB: 15 — VPC: SG, NACL, route, Flow Logs, Reachability
SERVICE:
DATE: 2026-11-03
DOMAIN: D5 Networking 18%
PHASES: Build [x] Break [x] Diagnose [x] Fix [ ] Verify [x] Cleanup [ ]
```

1. What did I build?
app stack + flow log /aws/vpc/soa-c03/lab15 + path nip-0612e4f79491088b6
2. What failed? (symptom, not root cause)
curl /health → 504, target unhealthy sau ~2–3 phút
3. How did I detect it? (metric/log/event/CLI)
SG inbound trống; NACL acl-08f013cbc6f33dbb1 rule 100 Allow all; ASG Activity
4. Root cause (the actual brokenchặn layer)
SG chặn
5. How did I fix it? (exact command or console action)
đúng 4 ô: Custom TCP · 8080 · Source = sg-0440b96a1db12a2ea (ALB SG) · Save rules
6. Prevention / automation
Dùng AWS Config
7. Exam trap
SG stateful vs NACL stateless; 504 (drop im lặng) ≠ 502 (refused) ≠ 503 (no healthy target); ASG thay máy khi health check fail