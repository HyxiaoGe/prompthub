#!/usr/bin/env python3
"""Merge 5 audio-* projects into one audio-assistant project."""

import json
import httpx

BASE = "http://localhost:8000/api/v1"
AUTH = {"Authorization": "Bearer ph-dev-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}

# Old project slug → new category name
PROJECT_TO_CATEGORY = {
    "audio-summary": "summary",
    "audio-visual": "visual",
    "audio-segmentation": "segmentation",
    "audio-images": "images",
    "audio-shared": "shared",
}


def api(method, path, **kw):
    with httpx.Client(timeout=30) as c:
        r = c.request(method, f"{BASE}{path}", headers=AUTH, **kw)
    d = r.json()
    if r.status_code >= 400:
        print(f"  ❌ {method} {path} → {r.status_code}: {d}")
    return d


def main():
    # 1. Get all projects
    projects = api("GET", "/projects?page_size=50")["data"]
    audio_projects = {p["id"]: p for p in projects if p["slug"] in PROJECT_TO_CATEGORY}

    print(f"Found {len(audio_projects)} audio projects to merge:")
    for pid, p in audio_projects.items():
        print(f"  {p['slug']:<25s} id={pid[:8]}…")

    # 2. Create audio-assistant project
    print("\n--- Creating audio-assistant project ---")
    resp = api("POST", "/projects", json={
        "name": "音频助手",
        "slug": "audio-assistant",
        "description": "音频内容处理全流程提示词：摘要、关键点、章节划分、可视化、配图",
    })
    if resp.get("code") != 0:
        # Maybe already exists
        print(f"  Create response: {resp}")
        # Try to find it
        for p in api("GET", "/projects?page_size=50")["data"]:
            if p["slug"] == "audio-assistant":
                new_project_id = p["id"]
                break
        else:
            print("❌ Cannot create or find audio-assistant project")
            return
    else:
        new_project_id = resp["data"]["id"]
    print(f"  audio-assistant ID: {new_project_id}")

    # 3. Migrate prompts
    print("\n--- Migrating prompts ---")
    migrated = 0
    for old_pid, old_proj in audio_projects.items():
        category = PROJECT_TO_CATEGORY[old_proj["slug"]]
        # Get all prompts for this project
        prompts_resp = api("GET", f"/prompts?project_id={old_pid}&page_size=100")
        prompts = prompts_resp["data"]
        print(f"\n  {old_proj['slug']} → category={category} ({len(prompts)} prompts)")

        for p in prompts:
            # Update project_id and category via direct DB would be ideal,
            # but we only have the API. The PUT /prompts/{id} doesn't support
            # changing project_id (it's not in PromptUpdate schema).
            # We need to check if the API supports it.
            resp = api("PUT", f"/prompts/{p['id']}", json={
                "category": category,
            })
            if resp.get("code") == 0:
                # Try updating project_id too — may or may not work
                pass
            print(f"    {p['slug']:<45s} category → {category}")
            migrated += 1

    print(f"\n  Set category on {migrated} prompts")

    # 4. Check if PUT supports project_id change
    # Let's test with one prompt
    print("\n--- Testing project_id migration ---")
    test_prompts = api("GET", f"/prompts?project_id={list(audio_projects.keys())[0]}&page_size=1")
    if test_prompts["data"]:
        test_p = test_prompts["data"][0]
        resp = api("PUT", f"/prompts/{test_p['id']}", json={
            "project_id": new_project_id,
        })
        # PromptUpdate schema doesn't include project_id, so this field will be
        # silently ignored by Pydantic. We need a different approach.
        # Check if it actually changed
        check = api("GET", f"/prompts/{test_p['id']}")
        if check["data"]["project_id"] == new_project_id:
            print("  ✅ project_id update works via API")
        else:
            print("  ⚠️ project_id update NOT supported via API — need DB migration")
            print("     Will need to add project_id to PromptUpdate schema or use SQL")

    print("\n--- Done (category updates applied) ---")
    print(f"NOTE: If project_id migration failed, a DB-level UPDATE is needed.")


if __name__ == "__main__":
    main()
