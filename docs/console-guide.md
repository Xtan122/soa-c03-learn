# Console guide — nói “bấm ở đâu”, không nói “vào CloudWatch tìm đi”

> File này là chuẩn cho AI mentor khi hướng dẫn trên AWS Console.
> Mỗi lab có mục **5c. Console — bấm ở đâu, thấy gì** trong README.
> Xem nhanh trong terminal: `./bin/lab console <id>`.
>
> Người mới: đọc [`docs/learner-quickstart.md`](learner-quickstart.md) trước.
> AI mentor: làm theo [`docs/ai-mentor-runbook.md`](ai-mentor-runbook.md) —
> mỗi lượt một màn hình, một nút, hỏi lại trước khi đi tiếp.
>
> Lab 01 và 02 cho thấy lỗi phổ biến: AI nói “vào CloudWatch → Alarms” nhưng
> người mới vẫn không biết bấm menu nào, tab nào, đọc ô nào. File này sửa đúng
> khoảng trống đó.

---

## 1. Một câu trả lời console đủ tốt phải có 5 phần

| Phần | Ví dụ | Nếu thiếu |
|---|---|---|
| **Khái niệm** | “Alarm là quy tắc đọc metric, không phải đồng hồ.” | Người học làm đúng nhưng không hiểu. |
| **Vị trí** | “CloudWatch → menu trái **Alarms** → **All alarms**.” | Người học lạc menu. |
| **Hành động** | “Bấm `soa-c03-lab01-cpu-high` → tab **History**.” | Người học dừng lại. |
| **Bạn sẽ thấy** | “State = ALARM; dòng `OK -> ALARM` lúc 10:12.” | Người học không biết đúng/sai. |
| **Ý nghĩa + câu hỏi** | “Vì sao alarm chậm 1 phút? Bạn thấy period nào?” | Người học không nối được kiến thức. |

Không được rút gọn còn “vào console xem đi”. Đó là lỗi của lab 01/02.

---

## 2. Quy tắc viết đường bấm

1. **Bắt đầu từ tên service**, không bắt đầu từ “console”.
   Đúng: `CloudWatch → Metrics → All metrics → EC2`.
   Sai: “Vào phần monitoring”.
2. **Ghi rõ menu trái / tab / nút**, dùng đúng nhãn tiếng Anh trên console.
3. **Nêu region** ở đầu câu trả lời: `ap-southeast-1 (Singapore)`.
4. **Nêu tên tài nguyên thật** để search: `soa-c03-lab01-cpu-high`, không nói “cái alarm của lab”.
5. **Nêu ô cần đọc** và **giá trị bình thường** nếu biết.
6. **Nêu thời gian chờ** (metric/log/alarm thường trễ 30–90 giây; CloudTrail có thể vài phút).
7. **Không bịa ID runtime** (`i-...`, `vpc-...`) trong link. Dùng trang danh sách + hướng dẫn search.
8. **Không đưa deep link mà không có đường bấm** đi kèm. AWS đổi URL thường xuyên.

### Mẫu câu

```text
Mở CloudWatch (ô Search trên cùng) → menu trái Alarms → All alarms
→ bấm soa-c03-lab01-cpu-high → tab History.
Bạn sẽ thấy một dòng OK -> ALARM kèm giờ. Đọc giờ đó rồi trả lời:
alarm chuyển sau bao lâu kể từ lúc CPU tăng?
```

> Đây là **bản đồ rút gọn** để tra. Khi AI dạy, AI phải tách thành **từng nút**
> theo mục 2b. Không đọc nguyên câu trên cho người mới rồi bảo “làm đi”.

---

## 2b. Chế độ từng nút (AI dùng khi dạy)

Mục 5c trong README gộp vài lần bấm vào một dòng cho gọn. Khi dạy người mới,
AI phải mở từng dòng thành các lượt riêng:

| Lượt | Một màn hình | Một nút | Hỏi lại |
|---:|---|---|---|
| 1 | AWS Console | ô **Search** → gõ `CloudWatch` → chọn dịch vụ | “Bạn thấy menu trái có gì?” |
| 2 | CloudWatch | menu trái **Metrics** | “Bạn thấy Metrics không?” |
| 3 | Metrics | **All metrics** | “Bạn thấy namespace nào?” |
| 4 | All metrics | **EC2** → **Per-Instance Metrics** | “Bạn thấy CPUUtilization không?” |
| 5 | Per-Instance Metrics | dán instance ID vào ô search | “Bạn thấy metric nào?” |

Quy tắc:

- Mỗi lượt chỉ **một** màn hình đích và **một** nút.
- Nói rõ nút đó **read-only** hay **thay đổi** gì.
- Nói **bạn sẽ thấy gì** để người học đối chiếu.
- Chờ người học nói “xong” + mô tả màn hình rồi mới sang lượt sau.
- Không paste cả mục 5c.
- Không nói “bấm nút chỉnh sửa”; nói đúng nhãn `Edit`.
- Nếu không chắc nhãn, hỏi người học đọc nhãn trên màn hình.

Quy trình đầy đủ: [`docs/ai-mentor-runbook.md`](ai-mentor-runbook.md).

---

## 2c. An toàn khi bấm

| Loại | Ví dụ | AI phải nói |
|---|---|---|
| **Xem** | Alarms, Metrics, Log groups, Targets, Events, History | “Chỉ mở xem, không sửa, bấm được.” |
| **Sửa** | `Edit`, `Modify`, `Update`, `Run query`, `Poll for messages` | “Sửa gì, có tốn tiền không, undo thế nào.” |
| **Tạo** | `Create`, `Restore DB instance`, `Create path` | “Tạo resource gì, cost bao nhiêu, cleanup lệnh nào.” |
| **Xoá / nguy hiểm** | `Delete`, `Terminate`, `Reboot`, `Failover` | Không hướng dẫn trong lúc diagnose; dừng và hỏi. |

Không bao giờ nói “bấm đi” với nút xoá/terminate. Không tự bấm thay người học.

---

## 2d. Màn hình mẫu (để đối chiếu)

Ví dụ trang chi tiết alarm trên CloudWatch:

```text
┌─────────────────────────────────────────────────────────────┐
│ CloudWatch > Alarms > soa-c03-lab01-cpu-high                │
│ State:  [ ALARM ]        Actions: Edit / Delete / ...       │
├─────────────────────────────────────────────────────────────┤
│ Details | History | Notifications | ...                     │
│                                                             │
│ Metric:      CPUUtilization                                 │
│ Threshold:   > 50                                           │
│ Period:      1 minute                                       │
│ Evaluation:  1                                              │
└─────────────────────────────────────────────────────────────┘
```

Khi người học mô tả màn hình, so với khung này để biết họ đang đúng trang.
Nhãn có thể khác đôi chút; **State**, **Threshold**, **Period** là các ô cần đọc.

---

## 2e. Từ điển nút thường gặp

| Nhãn trên console | Nghĩa | Sửa gì? |
|---|---|---|
| `Search` (ô trên cùng) | Tìm dịch vụ/resource | Không |
| `Edit` / `Modify` / `Update` | Mở form sửa | Có, sau khi `Save` |
| `Save` / `Save changes` | Ghi thay đổi | Có |
| `Create` / `Create ...` | Tạo resource mới | Có, có thể tốn tiền |
| `Delete` / `Terminate` | Xoá resource | Có, không undo |
| `Actions` | Menu hành động phụ | Tuỳ mục bên trong |
| `Refresh` | Tải lại dữ liệu | Không |
| `Run query` / `Run` | Chạy query/lệnh | Không (nhưng có thể tốn log query) |
| `Poll for messages` | Lấy message từ SQS | Có (message bị ẩn tạm thời) |
| `Start session` | Mở shell qua SSM | Không sửa resource |
| `Restore DB instance` | Tạo DB mới từ snapshot | Có, tốn tiền |
| `Detect drift` | Kiểm tra CloudFormation drift | Không |
| `Run analysis` | Chạy Reachability Analyzer | Không |
| `Retrieve secret value` | Đọc secret | Không sửa, nhưng là dữ liệu nhạy cảm |
| `Edit trust policy` | Sửa trust policy của role | Có |
| `Switch to policy view` | Đổi JSON ↔ editor | Không |
| `Reboot` / `Failover` | Khởi động lại DB | Có, downtime |

Nếu nhãn trên màn hình khác bảng này: **hỏi người học đọc nhãn**, đừng đoán.

---

## 3. Link nhanh (deep link)

Region mặc định: `ap-southeast-1`. Thay `{region}` nếu bạn đổi region.
Các link dưới đây chỉ là shortcut; **đường bấm trong README mới là nguồn chính**.

| Service | Link nhanh | Ghi chú |
|---|---|---|
| CloudWatch metrics | `https://console.aws.amazon.com/cloudwatch/home?region={region}#metricsV2:` | Trang browse metric |
| CloudWatch alarms | `https://console.aws.amazon.com/cloudwatch/home?region={region}#alarmsV2:alarms` | Danh sách alarm |
| Một alarm cụ thể | `...#alarmsV2:alarm/<tên-alarm>` | Tên alarm không có dấu cách |
| CloudWatch log groups | `https://console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups` | Tên group được URL-encode (`%2F` cho `/`) |
| Logs Insights | `https://console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:logs-insights` | Chọn log group ở dropdown |
| CloudWatch dashboard | `...#dashboards:name/<tên>` | Ví dụ `soa-c03-ops` |
| EC2 instances | `https://console.aws.amazon.com/ec2/home?region={region}#Instances:` | Search theo Name tag |
| EC2 security groups | `https://console.aws.amazon.com/ec2/home?region={region}#SecurityGroups:` | Vào chi tiết để xem inbound |
| EC2 target groups | `https://console.aws.amazon.com/ec2/home?region={region}#TargetGroups:` | Tab Targets + Health checks |
| EC2 load balancers | `https://console.aws.amazon.com/ec2/home?region={region}#LoadBalancers:` | Tab Listeners |
| Auto Scaling groups | `https://console.aws.amazon.com/ec2/home?region={region}#AutoScalingGroups:` | Tab Activity |
| Launch templates | `https://console.aws.amazon.com/ec2/home?region={region}#LaunchTemplates:` | Tab Versions |
| RDS databases | `https://console.aws.amazon.com/rds/home?region={region}#databases:` | Tab Configuration/Monitoring |
| RDS snapshots | `https://console.aws.amazon.com/rds/home?region={region}#snapshots:` | Tab Manual |
| Systems Manager | `https://console.aws.amazon.com/systems-manager/home?region={region}` | Fleet/Run Command/Session/Parameters |
| Run Command | `https://console.aws.amazon.com/systems-manager/run-command/execute-command?region={region}` | Chọn document + target |
| Session Manager | `https://console.aws.amazon.com/systems-manager/session-manager/start-session?region={region}` | Chọn instance |
| Parameter Store | `https://console.aws.amazon.com/systems-manager/parameters/?region={region}` | Search theo tên |
| IAM roles | `https://console.aws.amazon.com/iam/home#/roles` | IAM là global, không cần region |
| S3 buckets | `https://console.aws.amazon.com/s3/buckets?region={region}` | Tab Permissions |
| VPC console | `https://console.aws.amazon.com/vpcconsole/home?region={region}` | NACL/Route/Endpoints/Flow logs |
| ECS clusters | `https://console.aws.amazon.com/ecs/v2/clusters?region={region}` | Service → Health/Events |
| Lambda functions | `https://console.aws.amazon.com/lambda/home?region={region}#/functions` | Monitor → View logs |
| EventBridge rules | `https://console.aws.amazon.com/events/home?region={region}#/eventbus/default/rules` | Tab Monitoring |
| CloudTrail events | `https://console.aws.amazon.com/cloudtrail/home?region={region}#/events` | Filter Event name |
| AWS Backup | `https://console.aws.amazon.com/backup/home?region={region}#backup/vaults` | Vault/Plan/Jobs |
| AWS Config | `https://console.aws.amazon.com/config/home?region={region}#/dashboard` | Recorder + Rules |
| Budgets | `https://console.aws.amazon.com/billing/home?region={region}#/budgets` | Budget không chặn chi phí |
| Cost Explorer | `https://console.aws.amazon.com/costmanagement/home?region={region}#/cost-explorer` | Có thể trễ 24h |
| KMS keys | `https://console.aws.amazon.com/kms/home?region={region}#/kms/keys` | Tab Key policy |
| Secrets Manager | `https://console.aws.amazon.com/secretsmanager/landing?region={region}` | Secret + encryption key |
| SQS queues | `https://console.aws.amazon.com/sqs/v3/home?region={region}#/queues` | Send and receive messages |
| SNS topics | `https://console.aws.amazon.com/sns/v3/home?region={region}#/topics` | Subscriptions |
| CloudFormation stacks | `https://console.aws.amazon.com/cloudformation/home?region={region}#/stacks` | Tab Events/Resources |
| ECR repositories | `https://console.aws.amazon.com/ecr/repositories?region={region}` | Lifecycle policy |
| Access Analyzer | `https://console.aws.amazon.com/access-analyzer/home?region={region}#/analyzer` | Findings |

Nếu link 404 hoặc mở sai trang: **bỏ link, đi theo đường bấm**. Không sửa link
bằng cách đoán; ghi lại để cập nhật `tools/lab_console.py`.

---

## 4. Console hay CLI?

| Tình huống | Nên dùng |
|---|---|
| Người mới, lần đầu thấy service | **Console** — thấy cấu trúc, tab, trạng thái |
| Cần chứng minh nhanh, lặp lại | **CLI** — copy được vào evidence |
| Cần so sánh nhiều resource | CLI + `--query`, hoặc console filter |
| Cần thao tác một resource cụ thể | Console cho an toàn, CLI cho nhanh |

Cách học tốt nhất: **làm trên console một lần, rồi chạy lệnh CLI tương đương**
và so output. Lab README có cả hai.

---

## 5. Khi console khác ảnh hướng dẫn

AWS đổi giao diện vài lần mỗi năm. Thứ tự xử lý:

1. Kiểm tra region góc trên phải.
2. Dùng ô **Search** trên cùng, gõ tên service.
3. Nếu menu trái đổi tên, tìm từ khóa gần nghĩa (Alarms/Alarm, Log groups/Logs).
4. Nếu tab đổi tên, tìm chức năng tương đương trong trang chi tiết.
5. Ghi lại điểm lệch vào `notes/` để cập nhật `tools/lab_console.py`.
6. Không đoán bừa; nếu không tìm thấy, quay lại CLI và hỏi AI.

---

## 6. Checklist trước khi AI nói “bấm vào…”

- [ ] Có tên service và đường đi từ menu trái.
- [ ] Chỉ **một màn hình** và **một nút** trong lượt này.
- [ ] Có region.
- [ ] Có tên tài nguyên thật để search.
- [ ] Có tab/nút cụ thể, đúng nhãn tiếng Anh.
- [ ] Có nói nút đó read-only hay thay đổi gì.
- [ ] Có ô/giá trị cần đọc.
- [ ] Có thời gian chờ hợp lý.
- [ ] Có câu hỏi kiểm tra sau khi người học đọc màn hình.
- [ ] Không đưa đáp án root cause trong 20 phút đầu.

Xem thêm: [`docs/ai-mentor-runbook.md`](ai-mentor-runbook.md) ·
[`docs/learner-quickstart.md`](learner-quickstart.md) ·
[`labs/<id>/README.md`](../labs/) mục 5c · `./bin/lab console <id>`.
