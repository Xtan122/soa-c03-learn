SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

.PHONY: help start init doctor bootstrap core-up core-down app-up app-down status cost inventory cleanup upload dash test list audit preflight console

start: ## Show the session entrypoint + progress
	@echo "1. Open START-HERE.md"
	@echo "2. Ask AI: 'Đọc START-HERE.md và bắt đầu buổi lab hôm nay.'"
	@echo "3. Current progress:"
	@./bin/lab progress

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init: ## Create .env and fill account id / region from AWS CLI
	@./scripts/init.sh

doctor: ## Check credentials, budget, stacks, app health, cost, expiry
	@./bin/lab doctor

bootstrap: ## One-time: deploy core stack, budget, upload app artifacts
	@./scripts/bootstrap.sh

core-up: ## Deploy/update the persistent core stack (cheap: ~$1-2/month)
	@./scripts/core-up.sh

core-down: ## Delete core stack (run cleanup first)
	@./scripts/core-down.sh

app-up: ## Deploy the on-demand app stack (ALB + ASG + RDS)
	@./scripts/app-up.sh

app-down: ## Delete the on-demand app stack (stops the meter)
	@./scripts/app-down.sh

upload: ## Upload app artifacts to the lab S3 bucket
	@./scripts/upload-app.sh

dash: ## Create/update the CloudWatch dashboard
	@./scripts/create-dashboard.sh

status: ## Show stacks, app URL, alarms, running resources
	@./bin/lab status

cost: ## Spend today/week/month + leftover expensive resources
	@./scripts/cost-check.sh

inventory: ## List every resource tagged Project=soa-c03
	@./scripts/inventory.sh

cleanup: ## DESTRUCTIVE: delete all lab resources (requires CONFIRM_DESTROY=yes)
	@./scripts/cleanup-all.sh

test: ## Lint bash, Python and CloudFormation locally
	@./scripts/test.sh

list: ## List the 24 labs and progress
	@./bin/lab list

audit: ## Static audit of all 24 labs (offline, no AWS)
	@python3 tools/check_labs.py

preflight: ## Check one lab before up: make preflight LAB=05 [LIVE=1]
	@test -n "$(LAB)" || { echo "usage: make preflight LAB=05 [LIVE=1]"; exit 1; }
	@./bin/lab preflight $(LAB) $(if $(LIVE),--live,)

console: ## Show console click path for one lab: make console LAB=05
	@test -n "$(LAB)" || { echo "usage: make console LAB=05"; exit 1; }
	@./bin/lab console $(LAB)
