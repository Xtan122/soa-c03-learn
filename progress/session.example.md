# Session state

> Copy file này thành `progress/session.md` (đã gitignore) và cập nhật mỗi buổi.
> AI đọc file này đầu phiên để biết đang ở đâu.

```text
DATE: 2026-10-24
LAB: 01
LAB_TITLE: CloudWatch metrics, dashboard, alarm, SNS
START: 15:30
TIME_BUDGET: 150m
STATUS: setup          # setup | diagnose | fix | verify | note | done | aborted
CORE_STACK: CREATE_COMPLETE
APP_STACK: down        # up | down
BUDGET_CAP_USD: 2
SPEND_START_USD:
HYPOTHESES:
  - 
  - 
  - 
EVIDENCE:
  - 
HINTS_USED: 0
SOLUTION_USED: no
VERIFY: not-run
NOTE: missing
NEXT_LAB:
END:
SPEND_END_USD:
CLEANUP_DONE: no
```

## Quy tắc cập nhật

- Đầu phiên: DATE, LAB, START, TIME_BUDGET, APP_STACK, STATUS=setup.
- Sau break: STATUS=diagnose.
- Sau hint: HINTS_USED.
- Sau verify: VERIFY=pass/fail.
- Sau note: NOTE=done/missing.
- Cuối phiên: END, SPEND_END, CLEANUP_DONE, NEXT_LAB.
- Không ghi secret/access key vào file này.
