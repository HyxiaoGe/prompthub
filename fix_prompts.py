#!/usr/bin/env python3
"""Fix prompt issues found in verification report, then re-lint."""

import json
import httpx

BASE = "http://localhost:8000/api/v1"
AUTH = {"Authorization": "Bearer ph-dev-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}

def api(method, path, **kw):
    with httpx.Client(timeout=60) as c:
        r = c.request(method, f"{BASE}{path}", headers=AUTH, **kw)
    return r.json()

def get_prompt_by_slug(slug):
    resp = api("GET", f"/prompts?slug={slug}&page_size=100")
    for p in resp["data"]:
        if p["slug"] == slug:
            full = api("GET", f"/prompts/{p['id']}")
            return full["data"]
    return None

def lint(content, variables):
    return api("POST", "/ai/lint", json={"content": content, "variables": variables or []})

def update_prompt(pid, **fields):
    return api("PUT", f"/prompts/{pid}", json=fields)

report = []

def log(msg):
    print(msg)
    report.append(msg)

# =====================================================================
log("=" * 60)
log("# Prompt Fix Report")
log("=" * 60)

# =====================================================================
# Fix 1: image-gen-v2 — undefined_variable: subject
# =====================================================================
log("\n## Fix 1: image-gen-v2 — undefined_variable: subject\n")

p = get_prompt_by_slug("image-gen-v2")
if p:
    log(f"ID: {p['id']}")
    log(f"Content (first 300 chars):\n{p['content'][:300]}...\n")
    log(f"Current variables: {json.dumps(p['variables'], ensure_ascii=False)}")

    # Lint before
    lint_before = lint(p["content"], p["variables"])
    before_score = lint_before["data"]["score"]
    before_issues = [i["rule"] for i in lint_before["data"]["issues"]]
    log(f"Lint BEFORE: score={before_score}, issues={before_issues}")

    # Add subject to variables
    new_vars = list(p["variables"] or [])
    new_vars.append({
        "name": "subject",
        "type": "string",
        "required": True,
        "description": "The subject/topic for image generation",
    })
    update_prompt(p["id"], variables=new_vars)
    log(f"\n→ Added 'subject' to variables: {json.dumps(new_vars, ensure_ascii=False)}")

    # Lint after
    lint_after = lint(p["content"], new_vars)
    after_score = lint_after["data"]["score"]
    after_issues = [i["rule"] for i in lint_after["data"]["issues"]]
    log(f"Lint AFTER:  score={after_score}, issues={after_issues}")
    log(f"Score change: {before_score} → {after_score}")
else:
    log("❌ image-gen-v2 not found")

# =====================================================================
# Fix 2: audio-visual — unused quality_notice (3 prompts)
# =====================================================================
log("\n## Fix 2: audio-visual — unused quality_notice\n")

visual_slugs = [
    "visual-outline-general-zh",
    "visual-outline-explainer-zh",
    "visual-outline-documentary-zh",
]

for slug in visual_slugs:
    log(f"\n### {slug}")
    p = get_prompt_by_slug(slug)
    if not p:
        log(f"  ❌ not found")
        continue

    log(f"  ID: {p['id']}")
    content = p["content"]
    variables = p["variables"] or []
    var_names = [v["name"] for v in variables]
    log(f"  Variables: {var_names}")

    # Check if quality_notice is in content
    has_in_content = "quality_notice" in content
    log(f"  quality_notice in content: {has_in_content}")
    log(f"  quality_notice in variables: {'quality_notice' in var_names}")

    # Lint before
    lint_before = lint(content, variables)
    before_score = lint_before["data"]["score"]
    before_rules = [f"[{i['severity']}] {i['rule']}" for i in lint_before["data"]["issues"]]
    log(f"  Lint BEFORE: score={before_score}, issues={before_rules}")

    # Show where transcript appears (quality_notice typically goes after it)
    lines = content.split("\n")
    transcript_lines = [
        (i, line.strip()[:80])
        for i, line in enumerate(lines)
        if "transcript" in line.lower() or "转写" in line or "转录" in line
    ]
    log(f"  Transcript references: {transcript_lines}")

    # Decision: quality_notice is a shared module variable that provides quality
    # guidelines. It should be inserted after the transcript/content section,
    # before output requirements. Look for a good insertion point.
    # Since it's defined but not used, and the other audio-summary prompts DO use it,
    # we should insert {{ quality_notice }} in the template.

    # Find insertion point: after transcript block, before output/format section
    insert_idx = None
    for i, line in enumerate(lines):
        # Look for output requirement section or format section
        if any(kw in line for kw in ["输出要求", "输出格式", "图片要求", "生成要求", "## 输出"]):
            insert_idx = i
            break

    if insert_idx is None:
        # Fallback: insert before last non-empty line
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip():
                insert_idx = i
                break

    if insert_idx is not None:
        new_lines = lines[:insert_idx] + ["\n{{ quality_notice }}\n"] + lines[insert_idx:]
        new_content = "\n".join(new_lines)
        log(f"  → Inserted {{{{ quality_notice }}}} at line {insert_idx}")
    else:
        # Just append
        new_content = content + "\n\n{{ quality_notice }}\n"
        log(f"  → Appended {{{{ quality_notice }}}} at end")

    update_prompt(p["id"], content=new_content)

    # Lint after
    lint_after = lint(new_content, variables)
    after_score = lint_after["data"]["score"]
    after_rules = [f"[{i['severity']}] {i['rule']}" for i in lint_after["data"]["issues"]]
    log(f"  Lint AFTER:  score={after_score}, issues={after_rules}")
    log(f"  Score change: {before_score} → {after_score}")

# =====================================================================
# Fix 3: summary-actionitems-en — unused format_rules
# =====================================================================
log("\n## Fix 3: summary-actionitems-en — unused format_rules\n")

p = get_prompt_by_slug("summary-actionitems-en")
if p:
    log(f"ID: {p['id']}")
    content = p["content"]
    variables = p["variables"] or []
    var_names = [v["name"] for v in variables]
    log(f"Variables: {var_names}")

    has_in_content = "format_rules" in content
    log(f"format_rules in content: {has_in_content}")

    # Lint before
    lint_before = lint(content, variables)
    before_score = lint_before["data"]["score"]
    before_rules = [f"[{i['severity']}] {i['rule']}: {i['message'][:60]}" for i in lint_before["data"]["issues"]]
    log(f"Lint BEFORE: score={before_score}")
    for r in before_rules:
        log(f"  {r}")

    # Show content to decide
    log(f"\nFull content:\n{content}\n")

    # The prompt already has inline formatting rules. format_rules is a shared
    # variable that other prompts use. For consistency, we should insert it.
    # Find insertion point: after transcript, before the action items extraction rules.
    lines = content.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if "format" in line.lower() and ("rule" in line.lower() or "requirement" in line.lower() or "output" in line.lower()):
            insert_idx = i
            break
        if "extract" in line.lower() and i > 3:
            insert_idx = i
            break

    if insert_idx is None:
        # Look for "Output" or similar section
        for i, line in enumerate(lines):
            if line.strip().startswith("##") or "Output" in line or "Format" in line:
                insert_idx = i
                break

    if insert_idx is not None:
        new_lines = lines[:insert_idx] + ["", "{{ format_rules }}", ""] + lines[insert_idx:]
        new_content = "\n".join(new_lines)
        log(f"→ Inserted {{{{ format_rules }}}} at line {insert_idx}")
    else:
        # Insert before the last section
        new_content = content.rstrip() + "\n\n{{ format_rules }}\n"
        log(f"→ Appended {{{{ format_rules }}}} at end")

    update_prompt(p["id"], content=new_content)

    # Lint after
    lint_after = lint(new_content, variables)
    after_score = lint_after["data"]["score"]
    after_rules = [f"[{i['severity']}] {i['rule']}: {i['message'][:60]}" for i in lint_after["data"]["issues"]]
    log(f"Lint AFTER:  score={after_score}")
    for r in after_rules:
        log(f"  {r}")
    log(f"Score change: {before_score} → {after_score}")
else:
    log("❌ summary-actionitems-en not found")

# =====================================================================
log("\n" + "=" * 60)
log("# Summary")
log("=" * 60)

with open("FIX_REPORT.md", "w") as f:
    f.write("\n".join(report))
print("\n📄 Report written to FIX_REPORT.md")
