# LAB 06 — ASG scale-out thất bại

```text
LAB: 06 — ASG scale-out thất bại
SERVICE: ALB, EC2, ASG, Target group
DATE: 2026-10-29
DOMAIN: D2 Reliability 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ] SOLUTION_USED: no, TIME_TO_ROOT_CAUSE: 15
```

1. What did I build?
ALB -> ASG -> Target Group -> Instance

2. What failed? (symptom, not root cause)
ASG desired 2, máy mới running nhưng target unhealthy; máy cũ vẫn healthy

3. How did I detect it? (metric/log/event/CLI)
(a) dòng activity increasing the capacity from 1 to 2 + Successful; (b) 2 dòng user-data v1 vs v3 (exit 1); (c) target health Unhealthy / Health checks failed

4. Root cause (the actual broken layer)
config of version 3 launch template
5. How did I fix it? (exact command or console action)dòng
 aws autoscaling update-auto-scaling-group --auto-scaling-group-name soa-c03-asg \
  --launch-template "LaunchTemplateId=lt-0a52c915b6f544935,Version=1"

6. Prevention / automation
Alarm (UnHealthyHostCount / target unhealthy), Guardrail (cấm $Latest ở prod, pin version), Process (test version mới trước khi set default)

7. Exam trap
$Latest tự lấy bản mới nhất → version hỏng ảnh hưởng mọi instance mới; pin version cụ thể để kiểm soát