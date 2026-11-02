#!/usr/bin/env bash
# Local validation only. Does not touch AWS resources.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0

echo "== bash syntax =="
while IFS= read -r -d '' f; do
  if bash -n "$f" 2>/tmp/bash-n.err; then
    :
  else
    echo "FAIL $f"; cat /tmp/bash-n.err; fail=1
  fi
done < <(find bin scripts -type f \( -name '*.sh' -o -path 'bin/lab' \) -print0)
[[ $fail -eq 0 ]] && echo "OK"

echo "== python syntax =="
if python3 -m py_compile platform/app/app.py scripts/lab-list.py tools/gen_lab_docs.py \
    tools/lab_console.py tools/lab_brief.py tools/check_labs.py tools/lab_preflight.py labs/11-cloudformation-cdk/cdk/app.py; then echo "OK"; else fail=1; fi

echo "== yaml parse =="
python3 - <<'PY' || fail=1
import glob, sys
try:
    import yaml
except ImportError:
    print("SKIP: PyYAML not installed")
    sys.exit(0)

class CfnLoader(yaml.SafeLoader):
    pass

def unknown(loader, tag_suffix, node):
    # Ignore CloudFormation short-form intrinsics (!Ref, !Sub, !GetAtt, ...)
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)

CfnLoader.add_multi_constructor("!", unknown)
for f in glob.glob("platform/*.yaml") + glob.glob("labs/**/*.yaml", recursive=True):
    try:
        list(yaml.load_all(open(f), Loader=CfnLoader))
        print("OK", f)
    except Exception as e:
        print("FAIL", f, e); sys.exit(1)
PY

echo "== cfn-lint =="
if command -v cfn-lint >/dev/null 2>&1; then
  if cfn-lint platform/*.yaml labs/**/*.yaml 2>/dev/null; then echo "OK"; else fail=1; fi
else
  echo "SKIP: cfn-lint not installed (pipx install cfn-lint)"
fi

echo "== lab manifests =="
python3 - <<'PY' || fail=1
import glob, os, sys
required = {"LAB_ID","LAB_TITLE","DOMAIN","MINUTES","COST","NEEDS_APP"}
bad = 0
for f in sorted(glob.glob("labs/*/lab.env")):
    vals = {}
    for line in open(f):
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k,v=line.split("=",1); vals[k]=v
    missing = required - vals.keys()
    if missing:
        print("FAIL", f, "missing", missing); bad=1
print("OK" if not bad else "FAIL")
sys.exit(bad)
PY

echo "== lab READMEs (beginner contract) =="
python3 - <<'PY' || fail=1
import glob, pathlib, sys
required = [
    "## 0. Đọc nhanh (60 giây)",
    "## 1. Lab này để làm gì?",
    "## 2. Hiện tại có gì?",
    "## 3. Kiến trúc",
    "## 5. Các bước",
    "## 6. Hiện tượng bạn sẽ thấy",
    "## 7. Tự chẩn đoán: nhìn đâu?",
    "## 8. Thành công trông như thế nào?",
    "## 9. Exam takeaway",
    "## 10. Note mẫu",
    "## 11. Cleanup",
    "## 12. Nếu bí",
]
bad = 0
for d in sorted(glob.glob("labs/*/")):
    p = pathlib.Path(d)
    env = (p / "lab.env").read_text()
    lid = env.split("LAB_ID=")[1].splitlines()[0].strip()
    readme = p / "README.md"
    if not readme.exists():
        print("FAIL", d, "missing README"); bad = 1; continue
    text = readme.read_text()
    if f"# Lab {lid}" not in text:
        print("FAIL", readme, "wrong lab id"); bad = 1
    for block in required:
        if block not in text:
            print("FAIL", readme, "missing", block); bad = 1
    if "<điền" in text or "TODO" in text:
        print("FAIL", readme, "placeholder left"); bad = 1
print("OK" if not bad else "FAIL")
sys.exit(bad)
PY

echo "== lab readiness (static) =="
if python3 tools/check_labs.py; then echo "OK"; else fail=1; fi

echo "== generated lab docs =="
if python3 tools/gen_lab_docs.py --check; then echo "OK"; else fail=1; fi

if [[ $fail -ne 0 ]]; then
  echo "== TEST FAILED ==" >&2
  exit 1
fi
echo "== ALL LOCAL CHECKS PASSED =="
