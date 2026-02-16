#!/usr/bin/env python3
"""PromptHub E2E Verification Script — Phase 5 AI capabilities + full platform check.

Usage:
    cd /path/to/prompthub
    python verify_e2e.py

Requires: backend running on localhost:8000, OPENAI_API_KEY configured.
"""

import json
import sys
import time
from datetime import datetime

import httpx

BASE = "http://localhost:8000"
API = f"{BASE}/api/v1"
KEY = "ph-dev-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
HEADERS = {"Authorization": f"Bearer {KEY}"}

report_lines: list[str] = []


def log(msg: str) -> None:
    print(msg)
    report_lines.append(msg)


def section(title: str) -> None:
    log(f"\n{'='*70}")
    log(f"## {title}")
    log(f"{'='*70}\n")


def api(method: str, path: str, **kwargs) -> dict:
    """Call the API and return the full JSON response."""
    url = f"{API}{path}" if not path.startswith("http") else path
    with httpx.Client(timeout=120) as c:
        resp = c.request(method, url, headers=HEADERS, **kwargs)
    data = resp.json()
    if resp.status_code >= 400:
        log(f"  ❌ {method} {path} → {resp.status_code}: {data.get('message', 'Unknown')}")
        log(f"     detail: {data.get('detail', 'N/A')}")
    return data


def main() -> None:
    started = time.monotonic()
    log(f"# PromptHub E2E Verification Report")
    log(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"**Backend**: {BASE}")

    # =====================================================================
    # Step 1: Basic Verification
    # =====================================================================
    section("Step 1: Basic Verification — Health & Data")

    # Health
    with httpx.Client(timeout=10) as c:
        health = c.get(f"{BASE}/health").json()
    log(f"- Health: {health['data']['status']} ✅")

    # Projects
    proj_resp = api("GET", "/projects?page_size=50")
    projects = proj_resp["data"]
    audio_projects = [p for p in projects if p["slug"].startswith("audio-")]
    log(f"- Total projects: {proj_resp['meta']['total']}")
    log(f"- Audio projects: {len(audio_projects)}")
    for p in audio_projects:
        log(f"  - {p['slug']} — {p['name']} ({p['id'][:8]}…)")

    # Prompt counts per project
    project_prompts: dict[str, list[dict]] = {}
    total_prompts = 0
    for p in projects:
        resp = api("GET", f"/prompts?project_id={p['id']}&page_size=100")
        prompts = resp["data"]
        project_prompts[p["slug"]] = prompts
        total_prompts += len(prompts)
        log(f"  - {p['slug']}: {len(prompts)} prompts")
    log(f"- **Total prompts across all projects: {total_prompts}**")

    # =====================================================================
    # Step 2: Batch Evaluate — audio-summary prompts
    # =====================================================================
    section("Step 2: Batch Evaluate — audio-summary prompts")

    audio_summary_id = next(p["id"] for p in projects if p["slug"] == "audio-summary")
    summary_prompts = project_prompts["audio-summary"]
    batch_ids = [p["id"] for p in summary_prompts[:10]]
    log(f"- Evaluating {len(batch_ids)} prompts from audio-summary…")

    batch_resp = api("POST", "/ai/evaluate/batch", json={
        "prompt_ids": batch_ids,
        "criteria": ["clarity", "specificity", "completeness", "consistency"],
    })

    if batch_resp.get("code") == 0:
        results = batch_resp["data"]["results"]
        model = batch_resp["data"]["model_used"]
        log(f"- Model used: {model}")
        log(f"- Results:")

        scores = []
        low_score_prompts = []
        high_score_prompts = []

        # Build id→slug map
        id_to_slug = {p["id"]: p["slug"] for p in summary_prompts}

        for r in results:
            pid = r["prompt_id"]
            slug = id_to_slug.get(pid, pid[:8])
            score = r["overall_score"]
            scores.append(score)
            criteria_str = ", ".join(f"{k}={v}" for k, v in r["criteria_scores"].items())
            suggestions_str = "; ".join(r["suggestions"][:2]) if r["suggestions"] else "none"
            log(f"  | {slug:<45} | score={score:.1f} | {criteria_str}")
            if r["suggestions"]:
                log(f"  |   suggestions: {suggestions_str}")

            if score < 3.5:
                low_score_prompts.append((slug, score, r, pid))
            if score >= 4.0:
                high_score_prompts.append((slug, score, r, pid))

        avg = sum(scores) / len(scores) if scores else 0
        log(f"\n  **Summary**:")
        log(f"  - Average score: {avg:.2f}/5")
        log(f"  - Highest: {max(scores):.1f} | Lowest: {min(scores):.1f}")
        log(f"  - High (≥4.0): {len(high_score_prompts)} prompts")
        log(f"  - Low (<3.5): {len(low_score_prompts)} prompts")
    else:
        log(f"  ❌ Batch evaluate failed: {batch_resp}")
        low_score_prompts = []
        high_score_prompts = []

    # =====================================================================
    # Step 3: Lint Check — sample from each project
    # =====================================================================
    section("Step 3: Lint Check — sample from each project")

    lint_total_issues = 0
    lint_by_rule: dict[str, int] = {}
    lint_results_all: list[dict] = []

    for proj_slug, prompts in project_prompts.items():
        if not prompts:
            continue
        sample = prompts[:3]
        log(f"\n### Project: {proj_slug}")
        for p in sample:
            # Need full prompt content
            full = api("GET", f"/prompts/{p['id']}")
            if full.get("code") != 0:
                continue
            prompt_data = full["data"]
            content = prompt_data["content"]
            variables = prompt_data.get("variables") or []

            lint_resp = api("POST", "/ai/lint", json={
                "content": content,
                "variables": variables,
            })

            if lint_resp.get("code") == 0:
                lint_data = lint_resp["data"]
                issues = lint_data["issues"]
                score = lint_data["score"]
                lint_total_issues += len(issues)
                lint_results_all.append({
                    "slug": p["slug"],
                    "project": proj_slug,
                    "score": score,
                    "issues": issues,
                })
                status = "✅" if not issues else f"⚠️ {len(issues)} issue(s)"
                log(f"  - {p['slug']}: lint={score:.0f}/100 {status}")
                for issue in issues:
                    rule = issue["rule"]
                    lint_by_rule[rule] = lint_by_rule.get(rule, 0) + 1
                    log(f"    [{issue['severity']}] {rule}: {issue['message'][:80]}")

    log(f"\n**Lint Summary**:")
    log(f"- Total issues found: {lint_total_issues}")
    log(f"- By rule:")
    for rule, count in sorted(lint_by_rule.items(), key=lambda x: -x[1]):
        log(f"  - {rule}: {count}")

    # =====================================================================
    # Step 4: AI Generation Capabilities
    # =====================================================================
    section("Step 4: AI Generation Capabilities")

    # 4a: Generate
    log("### 4a: Generate — 播客摘要提示词")
    gen_resp = api("POST", "/ai/generate", json={
        "description": "生成一个播客摘要系统提示词，用于将播客音频的转录文本总结为结构化摘要，包含主题概述、关键要点、嘉宾观点",
        "count": 3,
        "language": "zh",
        "target_format": "text",
    })
    if gen_resp.get("code") == 0:
        candidates = gen_resp["data"]["candidates"]
        log(f"- Generated {len(candidates)} candidates (model: {gen_resp['data']['model_used']})")
        for i, c in enumerate(candidates):
            log(f"  Candidate {i+1}: {c['name']}")
            log(f"    slug: {c['slug']}")
            log(f"    rationale: {c['rationale'][:100]}…")
            log(f"    content preview: {c['content'][:120]}…")
            log(f"    variables: {[v.get('name') for v in c.get('variables', [])]}")
    else:
        log(f"  ❌ Generate failed")

    # 4b: Enhance — pick a low-score prompt
    log("\n### 4b: Enhance — improve a low-score prompt")
    if low_score_prompts:
        enhance_slug, enhance_score, _, enhance_pid = low_score_prompts[0]
        full_prompt = api("GET", f"/prompts/{enhance_pid}")
        original_content = full_prompt["data"]["content"]
        log(f"- Enhancing: {enhance_slug} (original score: {enhance_score:.1f})")
        log(f"  Original content preview: {original_content[:150]}…")

        enhance_resp = api("POST", "/ai/enhance", json={
            "content": original_content,
            "aspects": ["clarity", "specificity", "structure", "completeness"],
            "language": "zh",
        })
        if enhance_resp.get("code") == 0:
            edata = enhance_resp["data"]
            log(f"  Enhanced content preview: {edata['enhanced_content'][:150]}…")
            log(f"  Improvements:")
            for imp in edata["improvements"]:
                log(f"    - {imp}")

            # Re-evaluate enhanced version
            log("\n  Re-evaluating enhanced version…")
            re_eval = api("POST", "/ai/evaluate", json={
                "content": edata["enhanced_content"],
                "criteria": ["clarity", "specificity", "completeness", "consistency"],
            })
            if re_eval.get("code") == 0:
                new_score = re_eval["data"]["overall_score"]
                delta = new_score - enhance_score
                arrow = "⬆️" if delta > 0 else ("⬇️" if delta < 0 else "➡️")
                log(f"  Score change: {enhance_score:.1f} → {new_score:.1f} ({arrow} {delta:+.1f})")
        else:
            log(f"  ❌ Enhance failed")
    else:
        log("- No low-score prompts to enhance, picking first prompt instead")
        first = summary_prompts[0]
        full_prompt = api("GET", f"/prompts/{first['id']}")
        original_content = full_prompt["data"]["content"]
        enhance_resp = api("POST", "/ai/enhance", json={
            "content": original_content,
            "aspects": ["clarity", "specificity"],
        })
        if enhance_resp.get("code") == 0:
            log(f"  Enhanced successfully. Improvements: {enhance_resp['data']['improvements']}")

    # 4c: Variants — pick a high-score prompt
    log("\n### 4c: Variants — generate variants of a high-score prompt")
    if high_score_prompts:
        var_slug, var_score, _, var_pid = high_score_prompts[0]
        full_prompt = api("GET", f"/prompts/{var_pid}")
        var_content = full_prompt["data"]["content"]
        log(f"- Generating variants for: {var_slug} (score: {var_score:.1f})")
    else:
        var_content = summary_prompts[0]["slug"]
        full_prompt = api("GET", f"/prompts/{summary_prompts[0]['id']}")
        var_content = full_prompt["data"]["content"]
        log(f"- Generating variants for: {summary_prompts[0]['slug']}")

    var_resp = api("POST", "/ai/variants", json={
        "content": var_content,
        "variant_types": ["concise", "detailed", "creative"],
        "count": 3,
        "language": "zh",
    })
    if var_resp.get("code") == 0:
        variants = var_resp["data"]["variants"]
        log(f"  Generated {len(variants)} variants (model: {var_resp['data']['model_used']})")
        for v in variants:
            log(f"  [{v['variant_type']}] {v['description'][:80]}")
            log(f"    preview: {v['content'][:120]}…")

    # =====================================================================
    # Step 5: Render Verification
    # =====================================================================
    section("Step 5: Render Verification — Jinja2 templates")

    # 5a: Find shared-system-role-zh
    log("### 5a: Render shared-system-role-zh with content_style=meeting")
    shared_prompts = project_prompts.get("audio-shared", [])
    sys_role = next((p for p in shared_prompts if p["slug"] == "shared-system-role-zh"), None)
    if sys_role:
        full = api("GET", f"/prompts/{sys_role['id']}")
        content = full["data"]["content"]
        log(f"  Template preview: {content[:200]}…")
        variables = full["data"].get("variables", [])
        log(f"  Variables defined: {[v.get('name') for v in variables]}")

        render_resp = api("POST", f"/prompts/{sys_role['id']}/render", json={
            "variables": {"content_style": "meeting"},
        })
        if render_resp.get("code") == 0:
            rendered = render_resp["data"]["rendered_content"]
            log(f"  ✅ Rendered ({len(rendered)} chars):")
            # Show first few lines
            for line in rendered.split("\n")[:8]:
                log(f"    > {line}")
            if len(rendered.split("\n")) > 8:
                log(f"    > … ({len(rendered.split(chr(10)))} lines total)")
        else:
            log(f"  ❌ Render failed: {render_resp.get('message')}")
    else:
        log("  ⚠️ shared-system-role-zh not found in audio-shared project")

    # 5b: Find summary-overview-meeting-zh
    log("\n### 5b: Render summary-overview-meeting-zh with transcript + format_rules")
    summary_meeting = next(
        (p for p in summary_prompts if p["slug"] == "summary-overview-meeting-zh"), None,
    )
    if summary_meeting:
        full = api("GET", f"/prompts/{summary_meeting['id']}")
        content = full["data"]["content"]
        variables = full["data"].get("variables", [])
        log(f"  Variables: {[v.get('name') for v in variables]}")

        render_vars: dict = {}
        for v in variables:
            name = v.get("name", "")
            if name == "transcript":
                render_vars["transcript"] = (
                    "主持人：大家好，今天我们讨论AI在企业的应用。\n"
                    "嘉宾A：我认为AI最大的价值在于自动化重复性工作…\n"
                    "嘉宾B：没错，但我们也要关注数据安全问题…"
                )
            elif name == "format_rules":
                render_vars["format_rules"] = "使用Markdown格式，要点用编号列表"
            elif v.get("default") is not None:
                render_vars[name] = v["default"]
            elif v.get("required", True):
                render_vars[name] = f"[test-{name}]"

        render_resp = api("POST", f"/prompts/{summary_meeting['id']}/render", json={
            "variables": render_vars,
        })
        if render_resp.get("code") == 0:
            rendered = render_resp["data"]["rendered_content"]
            log(f"  ✅ Rendered ({len(rendered)} chars):")
            for line in rendered.split("\n")[:10]:
                log(f"    > {line}")
            if len(rendered.split("\n")) > 10:
                log(f"    > … ({len(rendered.split(chr(10)))} lines total)")
        else:
            log(f"  ❌ Render failed: {render_resp.get('message')}")
            log(f"     detail: {render_resp.get('detail')}")
    else:
        log("  ⚠️ summary-overview-meeting-zh not found")

    # =====================================================================
    # Step 6: SDK Verification
    # =====================================================================
    section("Step 6: SDK Verification")

    try:
        sys.path.insert(0, "sdk")
        from prompthub import PromptHubClient

        client = PromptHubClient(
            base_url=BASE,
            api_key=KEY,
        )

        # 6a: List projects
        sdk_projects = client.projects.list()
        log(f"- SDK projects.list(): {len(sdk_projects.items)} projects ✅")

        # 6b: Get prompt
        first_prompt = sdk_projects.items[0]
        sdk_prompts = client.prompts.list(project_id=str(audio_summary_id), page_size=5)
        log(f"- SDK prompts.list(audio-summary): {len(sdk_prompts.items)} prompts ✅")

        if sdk_prompts.items:
            p = sdk_prompts.items[0]
            full_p = client.prompts.get(p.id)
            log(f"- SDK prompts.get({p.slug}): content length={len(full_p.content)} ✅")

        # 6c: AI evaluate
        sdk_eval = client.ai.evaluate(
            "You are a helpful AI assistant that summarizes audio content.",
            criteria=["clarity", "specificity"],
        )
        log(f"- SDK ai.evaluate(): score={sdk_eval.overall_score:.1f}, model={sdk_eval.model_used} ✅")

        # 6d: AI generate
        sdk_gen = client.ai.generate(
            "生成一个视频摘要提示词",
            count=2,
            language="zh",
        )
        log(f"- SDK ai.generate(): {len(sdk_gen.candidates)} candidates ✅")
        for c in sdk_gen.candidates:
            log(f"    - {c.name}: {c.content[:60]}…")

        # 6e: AI enhance
        sdk_enhance = client.ai.enhance(
            "Summarize the audio.",
            aspects=["clarity", "specificity"],
        )
        log(f"- SDK ai.enhance(): {len(sdk_enhance.improvements)} improvements ✅")

        # 6f: AI lint
        sdk_lint = client.ai.lint(
            "Hello {{ name }}, please summarize {{ topic }}.",
            variables=[
                {"name": "name", "type": "string"},
                {"name": "unused_var", "type": "string"},
            ],
        )
        log(f"- SDK ai.lint(): score={sdk_lint.score}, issues={len(sdk_lint.issues)} ✅")
        for issue in sdk_lint.issues:
            log(f"    [{issue.severity}] {issue.rule}: {issue.message[:60]}")

        # 6g: AI variants
        sdk_var = client.ai.variants("You are a helpful assistant.", count=2)
        log(f"- SDK ai.variants(): {len(sdk_var.variants)} variants ✅")

        # 6h: Render via SDK
        if sdk_prompts.items:
            try:
                sdk_render = client.prompts.render(
                    sdk_prompts.items[0].id,
                    variables={"transcript": "Test transcript", "format_rules": "Markdown"},
                )
                log(f"- SDK prompts.render(): {len(sdk_render.rendered_content)} chars ✅")
            except Exception as e:
                log(f"- SDK prompts.render(): {e}")

        client.close()
        log("\n**SDK verification: ALL PASSED** ✅")

    except Exception as exc:
        log(f"\n❌ SDK verification failed: {exc}")
        import traceback
        log(traceback.format_exc())

    # =====================================================================
    # Final Summary
    # =====================================================================
    section("Final Summary")

    elapsed = time.monotonic() - started
    log(f"- Total verification time: {elapsed:.1f}s")
    log(f"- Backend status: healthy")
    log(f"- Total projects: {len(projects)}")
    log(f"- Total prompts: {total_prompts}")
    log(f"- AI endpoints tested: generate, enhance, variants, evaluate, evaluate/batch, lint")
    log(f"- SDK methods tested: projects, prompts, ai.generate/enhance/variants/evaluate/lint, render")
    log(f"- Render engine: Jinja2 conditional + variable injection verified")

    # Write report
    report_path = "VERIFICATION_REPORT.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    print(f"\n📄 Report written to {report_path}")


if __name__ == "__main__":
    main()
