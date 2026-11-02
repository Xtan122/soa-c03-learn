#!/usr/bin/env python3
"""Offline quality gate for the 24 labs.

Checks that do NOT touch AWS:
  1. every lab has a valid manifest and the required functions in labs.sh
  2. a lab that says NEEDS_APP=yes actually waits for a healthy app
  3. console guidance exists, has exact click paths, and uses the real resource names
  4. no us-east-1 links, no unresolved placeholders
  5. every `aws <service> <operation>` in labs.sh exists (optional, --aws-help)

Run:
  python3 tools/check_labs.py                 # all labs
  python3 tools/check_labs.py --lab 05        # one lab
  python3 tools/check_labs.py --strict        # warnings become failures
  python3 tools/check_labs.py --aws-help      # also validate CLI operations (slower)

This is deliberately conservative: a green run does not prove a lab deploys,
but it proves the lab has a build path, a cleanup path, and instructions a
beginner can follow. Runtime readiness is `./bin/lab preflight <id> --live`.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

try:
    from lab_brief import BRIEFS
except Exception:  # pragma: no cover - only when run outside tools/
    BRIEFS = {}

ROOT = pathlib.Path(__file__).resolve().parents[1]
LABS = ROOT / "labs"
LABS_SH = ROOT / "scripts/lib/labs.sh"
CONSOLE_MARKERS = ("<!-- console-guide:start -->", "<!-- console-guide:end -->")
REQUIRED_SECTIONS = [
    "## 0. Đọc nhanh (60 giây)",
    "## 1. Lab này để làm gì?",
    "## 2. Hiện tại có gì?",
    "## 3. Kiến trúc",
    "## 5. Các bước",
    "## 5c. Console — bấm ở đâu, thấy gì",
    "## 6. Hiện tượng bạn sẽ thấy",
    "## 7. Tự chẩn đoán: nhìn đâu?",
    "## 8. Thành công trông như thế nào?",
    "## 9. Exam takeaway",
    "## 10. Note mẫu",
    "## 11. Cleanup",
    "## 12. Nếu bí",
]
REQUIRED_MANIFEST = {"LAB_ID", "LAB_TITLE", "DOMAIN", "MINUTES", "COST", "NEEDS_APP"}
REQUIRED_FUNCS = ("build", "break", "verify")
FUNC_RE = re.compile(r"^(lab\d{2})_(build|break|verify|reset|cleanup)\(\)\s*\{", re.M)
TOKEN_RE = re.compile(r"`(soa-c03-[a-z0-9][a-z0-9-]*)`")
AWS_CALL_RE = re.compile(r"\baws\s+([a-z][a-z0-9-]*)\s+([a-z][a-z0-9-]*)")


class Result:
    def __init__(self) -> None:
        self.fail: list[str] = []
        self.warn: list[str] = []

    def bad(self, msg: str) -> None:
        self.fail.append(msg)

    def soft(self, msg: str) -> None:
        self.warn.append(msg)


def read_manifest(path: pathlib.Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def parse_lab_functions() -> dict[str, dict[str, str]]:
    text = LABS_SH.read_text()
    matches = list(FUNC_RE.finditer(text))
    out: dict[str, dict[str, str]] = {}
    for i, match in enumerate(matches):
        lab, fn = match.group(1), match.group(2)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.setdefault(lab, {})[fn] = text[match.start():end]
    return out


def known_resource_suffixes(texts: list[str]) -> set[str]:
    """Collect `soa-c03-<suffix>` and `${LAB_PREFIX}-<suffix>` tokens."""
    suffixes: set[str] = set()
    for text in texts:
        suffixes.update(re.findall(r"soa-c03-([a-z0-9][a-z0-9-]*)", text))
        suffixes.update(re.findall(r"\$\{LAB_PREFIX\}-([a-z0-9][a-z0-9-]*)", text))
        suffixes.update(re.findall(r"\$\{ProjectName\}-([a-z0-9][a-z0-9-]*)", text))
    # Keep only the first component as well: soa-c03-lab01-cpu-high -> lab01
    expanded = set(suffixes)
    for suffix in list(suffixes):
        expanded.add(suffix.split("-")[0])
    return expanded


def check_resource_tokens(section: str, known: set[str], result: Result, label: str) -> None:
    for token in re.findall(r"soa-c03-[a-z0-9][a-z0-9-]*", section):
        suffix = token.removeprefix("soa-c03-")
        if suffix in known or suffix.split("-")[0] in known:
            continue
        result.soft(f"{label} mentions unknown resource name: {token}")


def check_console(readme: str, result: Result, known: set[str]) -> None:
    for marker in CONSOLE_MARKERS:
        if readme.count(marker) != 1:
            result.bad(f"console marker {marker!r} must appear exactly once")
            return
    start = readme.index(CONSOLE_MARKERS[0]) + len(CONSOLE_MARKERS[0])
    end = readme.index(CONSOLE_MARKERS[1])
    section = readme[start:end]

    for heading in (
        "### Từ vựng nhanh (đọc trước)",
        "### Khái niệm của lab này",
        "### Đường bấm từng bước",
        "### Trên màn hình, đọc những ô này",
        "### Link nhanh",
        "### Nếu không thấy mục đó",
        "### Checkpoint trước khi bấm tiếp",
    ):
        if heading not in section:
            result.bad(f"console section missing {heading!r}")

    if "**Cách AI dạy:**" not in section:
        result.bad("console section missing the 'Cách AI dạy' one-screen/one-button note")

    terms_at = section.find("### Từ vựng nhanh (đọc trước)")
    concept_at = section.find("### Khái niệm của lab này")
    if terms_at > concept_at:
        result.bad("console section must put the glossary before the concepts")

    concept_block = section[concept_at:section.find("### Đường bấm từng bước")]
    if len([line for line in concept_block.splitlines() if line.startswith("- ")]) < 2:
        result.soft("concepts should be split into at least 2 bullets")

    steps = re.findall(r"^\d+\.\s+.+$", section, re.M)
    if len(steps) < 3:
        result.bad(f"console section has {len(steps)} numbered steps (need >= 3)")
    long_steps = [step for step in steps if len(step) > 240]
    if long_steps:
        result.soft(f"console step is too long to scan ({len(long_steps)} over 240 chars)")
    vague = [
        step for step in steps
        if not any(word in step.lower() for word in (
            "→", "bấm", "chọn", "mở", "tick", "gõ", "dán", "tab", "xem", "đọc",
            "điền", "search", "filter", "run", "poll", "terminal", "trang",
            "mục", "menu", "bộ lọc", "tìm", "query", "nếu",
        ))
    ]
    if vague:
        result.soft(f"console step(s) may be too vague: {vague[0][:90]}")

    term_rows = [line for line in section.splitlines() if line.startswith("| ") and "|" in line[2:]]
    if len(term_rows) < 6:
        result.soft(f"console section has only {len(term_rows)} table rows")

    links = re.findall(r"\[[^\]]+\]\((https://[^)]+)\)", section)
    if len(links) < 2:
        result.bad(f"console section has {len(links)} links (need >= 2)")
    for link in links:
        if not link.startswith("https://console.aws.amazon.com/"):
            result.soft(f"non-console link in console section: {link}")
        if "us-east-1" in link:
            result.bad(f"us-east-1 link in console section: {link}")
        if "region=ap-southeast-1" not in link and "/iam/home" not in link:
            result.soft(f"console link is not pinned to ap-southeast-1: {link}")
        if any(p in link for p in ("{region}", "{prefix}", "<account>", "<bucket>")):
            result.bad(f"unresolved placeholder in console link: {link}")

    for token in TOKEN_RE.findall(section):
        suffix = token.removeprefix("soa-c03-")
        first = suffix.split("-")[0]
        if suffix in known or first in known:
            continue
        result.soft(f"console mentions unknown resource name: {token}")


def logical_lines(block: str) -> list[str]:
    """Join bash continuation lines so a guard on line 2 applies to line 1."""
    out: list[str] = []
    buf = ""
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        buf = f"{buf} {line}".strip() if buf else line
        if buf.endswith("\\"):
            buf = buf[:-1].rstrip()
            continue
        out.append(buf)
        buf = ""
    if buf:
        out.append(buf)
    return out


def check_lab(lab_dir: pathlib.Path, funcs: dict[str, dict[str, str]],
              known: set[str]) -> Result:
    r = Result()
    env_path = lab_dir / "lab.env"
    readme_path = lab_dir / "README.md"
    if not env_path.exists():
        r.bad("missing lab.env")
        return r
    env = read_manifest(env_path)
    missing = REQUIRED_MANIFEST - env.keys()
    if missing:
        r.bad(f"lab.env missing keys: {sorted(missing)}")
        return r
    lab_id = env["LAB_ID"]
    if not lab_dir.name.startswith(f"{lab_id}-"):
        r.bad(f"directory {lab_dir.name!r} does not start with {lab_id!r}")
    if env["NEEDS_APP"] not in ("yes", "no"):
        r.bad(f"NEEDS_APP must be yes/no, got {env['NEEDS_APP']!r}")
    try:
        if int(env["MINUTES"]) < 30:
            r.bad("MINUTES is too small")
    except ValueError:
        r.bad(f"MINUTES is not a number: {env['MINUTES']!r}")

    lab_funcs = funcs.get(f"lab{lab_id}", {})
    for fn in REQUIRED_FUNCS:
        if fn not in lab_funcs:
            r.bad(f"missing function lab{lab_id}_{fn}()")
    if "cleanup" not in lab_funcs and "reset" not in lab_funcs:
        r.bad(f"missing cleanup/reset for lab {lab_id}")

    build = lab_funcs.get("build", "")
    if env["NEEDS_APP"] == "yes":
        if not any(word in build for word in ("ensure_app_healthy", "require_app")):
            r.bad("NEEDS_APP=yes but build does not require/verify the app stack")
        if "ensure_app_healthy" not in build:
            r.soft("NEEDS_APP=yes but build only calls require_app (no health wait)")
    else:
        if "ensure_app_healthy" in build:
            r.bad("NEEDS_APP=no but build waits for the app stack")

    # Heuristic: unguarded create-* calls usually break a second `up` run.
    safe_creates = (
        "create-tags", "create-queue", "create-log-group", "create-cluster",
        "create-alarm", "create-dashboard", "create-budget", "create_sqs",
        "create_alarm", "create_canary",
    )
    lines = logical_lines(build)
    for idx, line in enumerate(lines):
        if not re.search(r"\bcreate[-_][a-z0-9-]+", line):
            continue
        if any(op in line for op in safe_creates):
            continue
        context = " ".join(lines[max(0, idx - 6):idx + 2])
        guarded = any(mark in context for mark in (
            "|| true", "2>/dev/null", "|| aws", "head-bucket", "get-role",
            "list-analyzers", "|| \\", "existing",
        ))
        if guarded:
            continue
        r.soft(f"unguarded create in build (second `up` may fail): {line[:110]}")

    if not readme_path.exists():
        r.bad("missing README.md")
        return r
    readme = readme_path.read_text()
    if f"# Lab {lab_id}" not in readme:
        r.bad("README heading does not match lab id")
    for section in REQUIRED_SECTIONS:
        if section not in readme:
            r.bad(f"README missing {section!r}")
    quick_start = readme.find("## 0. Đọc nhanh (60 giây)")
    quick_end = readme.find("## 1. Lab này để làm gì?")
    if quick_start != -1 and quick_end > quick_start:
        quick = readme[quick_start:quick_end]
        if len([line for line in quick.splitlines() if line.startswith("- ")]) < 4:
            r.bad("60-second card must have 4 bullets: làm gì, việc đầu tiên, xong khi, nếu lạc")
    if "<điền" in readme or "TODO" in readme:
        r.bad("README still has a placeholder")
    if f"{int(lab_id):02d}" in BRIEFS:
        brief_heading = "## 5d. Baseline" if lab_id == "00" else "## 5d. Brief trước khi phá"
        brief_start = readme.find(brief_heading)
        if brief_start == -1:
            r.bad(f"lab has Brief data but README is missing {brief_heading!r}")
        else:
            for heading in ("### Hệ thống hiện tại (baseline)", "### Bản đồ chẩn đoán",
                            "### Trước khi"):
                if heading not in readme:
                    r.bad(f"brief section missing {heading!r}")
            brief_end = readme.find("## 6.", brief_start)
            check_resource_tokens(readme[brief_start:brief_end], known, r, "brief")
    check_console(readme, r, known)

    return r


def validate_aws_help(funcs: dict[str, dict[str, str]]) -> list[str]:
    """Validate service/operation pairs with `aws <svc> <op> help` (offline)."""
    pairs: set[tuple[str, str]] = set()
    for body in (b for lab in funcs.values() for b in lab.values()):
        pairs.update(AWS_CALL_RE.findall(body))
    bad: list[str] = []
    for svc, op in sorted(pairs):
        proc = subprocess.run(
            ["aws", svc, op, "help"],
            capture_output=True, text=True, timeout=20,
            env={"PATH": "/usr/local/bin:/usr/bin:/bin", "AWS_PAGER": ""},
        )
        if proc.returncode != 0:
            bad.append(f"aws {svc} {op}: {proc.stderr.strip().splitlines()[:1]}")
    return bad


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", help="only check one lab id, e.g. 05")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--aws-help", action="store_true", help="validate aws service/operation names")
    parser.add_argument("--quiet", action="store_true", help="only print failures and summary")
    args = parser.parse_args()

    funcs = parse_lab_functions()
    texts = [LABS_SH.read_text()]
    texts += [p.read_text() for p in (ROOT / "platform").glob("*.yaml")]
    texts += [p.read_text() for p in (ROOT / "scripts").glob("*.sh")]
    texts += [p.read_text() for p in (ROOT / "scripts/lib").glob("*.sh")]
    known = known_resource_suffixes(texts)

    lab_dirs = sorted(d for d in LABS.iterdir() if d.is_dir() and (d / "lab.env").exists())
    if args.lab:
        wanted = f"{int(args.lab):02d}"
        lab_dirs = [d for d in lab_dirs if d.name.startswith(wanted + "-")]
        if not lab_dirs:
            print(f"FAIL lab {args.lab} not found", file=sys.stderr)
            return 1

    total_fail = 0
    total_warn = 0
    for lab_dir in lab_dirs:
        r = check_lab(lab_dir, funcs, known)
        if args.strict:
            r.fail.extend(r.warn)
            r.warn = []
        total_fail += len(r.fail)
        total_warn += len(r.warn)
        if not args.quiet or r.fail or r.warn:
            print(f"{lab_dir.name:38} {'FAIL' if r.fail else 'PASS':4} "
                  f"{'' if not r.warn else f'({len(r.warn)} warn)'}")
        for msg in r.fail:
            print(f"  FAIL {msg}")
        for msg in r.warn:
            print(f"  warn {msg}")

    if args.aws_help:
        print("== aws CLI operation names ==")
        bad = validate_aws_help(funcs)
        for msg in bad:
            print(f"  FAIL {msg}")
        total_fail += len(bad)

    print(f"\n{len(lab_dirs)} labs, {total_fail} failure(s), {total_warn} warning(s)")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
