#!/usr/bin/env python3
import os
import sys
import glob
from typing import List
import requests
import frontmatter

REPO = os.environ.get("GITHUB_REPOSITORY")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}
API = f"https://api.github.com/repos/{REPO}"

class Conflict(Exception):
    pass

def req(method: str, path: str, **kwargs):
    r = requests.request(method, f"{API}{path}", headers=HEADERS, **kwargs)
    if r.status_code >= 400:
        raise requests.HTTPError(f"{method} {path} -> {r.status_code} {r.text}")
    return r

def parse_front_matter(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return frontmatter.load(f)

def ensure_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]

# Cache for assignee validation to avoid repeated API calls (repo-scoped)
_ASSIGNABLE_CACHE = {}

def is_assignable(username: str) -> bool:
    """Return True if the user can be assigned in this repo.
    Uses GET /repos/{owner}/{repo}/assignees/{assignee} which returns 204 if assignable, 404 otherwise.
    Cache is keyed by (REPO, username) to avoid cross-repo contamination.
    """
    if not username:
        return False
    key = (REPO, username)
    cached = _ASSIGNABLE_CACHE.get(key)
    if cached is not None:
        return cached
    r = requests.get(f"{API}/assignees/{username}", headers=HEADERS)
    ok = (r.status_code == 204)
    _ASSIGNABLE_CACHE[key] = ok
    return ok

def filter_assignable(users: list):
    """Split into (valid, invalid) assignees for this repo."""
    valid = []
    invalid = []
    for u in users or []:
        if is_assignable(u):
            valid.append(u)
        else:
            invalid.append(u)
    return valid, invalid

def upsert_issue(md_path: str):
    post = parse_front_matter(md_path)
    fm = post.metadata
    body = post.content or ""

    number = fm.get("issue")
    title = fm.get("title")
    state = fm.get("state")
    labels = ensure_list(fm.get("labels"))
    labels_mode = fm.get("labels_mode", "merge")
    assignees = ensure_list(fm.get("assignees"))
    milestone = fm.get("milestone")
    updated_at_local = fm.get("updated_at")

    if number is None:
        payload = {}
        payload["title"] = title or f"Issue from {os.path.basename(md_path)}"
        if body is not None: payload["body"] = body
        if labels: payload["labels"] = labels
        # optional parity: resolve milestone title -> number on create
        if milestone:
            try:
                mlist = req("GET", "/milestones").json()
                found = next((m for m in mlist if m["title"] == milestone), None)
                if found:
                    payload["milestone"] = found["number"]
                else:
                    payload["milestone"] = milestone
            except Exception:
                payload["milestone"] = milestone
        valid_assignees, invalid_assignees = filter_assignable(assignees)
        if invalid_assignees:
            print(f"::warning file={md_path}::Skipping invalid assignees on create: {', '.join(invalid_assignees)}")
        if valid_assignees:
            payload["assignees"] = valid_assignees
        try:
            issue = req("POST", "/issues", json=payload).json()
        except requests.HTTPError as e:
            msg = str(e)
            if "POST /issues" in msg and "422" in msg and '"field":"assignees"' in msg:
                print(f"::warning file={md_path}::Create failed due to assignees; retrying without assignees")
                payload.pop("assignees", None)
                issue = req("POST", "/issues", json=payload).json()
            else:
                raise
        print(f"Created issue #{issue['number']} from {md_path}")
        return

    # Fetch remote for conflict detection and ids
    issue = req("GET", f"/issues/{number}").json()
    remote_updated = issue.get("updated_at")
    if updated_at_local and remote_updated and updated_at_local < remote_updated:
        raise Conflict(f"{md_path}: remote newer ({remote_updated}) than local ({updated_at_local})")

    payload = {}
    if title: payload["title"] = title
    payload["body"] = body
    if state in ("open", "closed"): payload["state"] = state

    if milestone:
        # Resolve milestone title -> number; if not found, pass the title as-is for parity
        mlist = req("GET", "/milestones").json()
        found = next((m for m in mlist if m["title"] == milestone), None)
        if found:
            payload["milestone"] = found["number"]
        else:
            payload["milestone"] = milestone

    if payload:
        try:
            req("PATCH", f"/issues/{number}", json=payload)
        except requests.HTTPError as e:
            msg = str(e)
            if "PATCH /issues/" in msg and "422" in msg and '"field":"milestone"' in msg:
                # Retry without milestone if server rejects it
                payload.pop("milestone", None)
                req("PATCH", f"/issues/{number}", json=payload)
            else:
                raise

    # Labels
    if labels:
        if labels_mode == "replace":
            requests.put(f"{API}/issues/{number}/labels", headers=HEADERS, json={"labels": labels}).raise_for_status()
        else:
            current = req("GET", f"/issues/{number}/labels").json()
            current_names = {l["name"] for l in current}
            to_add = [l for l in labels if l not in current_names]
            if to_add:
                req("POST", f"/issues/{number}/labels", json={"labels": to_add})

    # Assignees (merge behavior)
    if assignees:
        valid_assignees, invalid_assignees = filter_assignable(assignees)
        if invalid_assignees:
            print(f"::warning file={md_path}::Skipping invalid assignees on update: {', '.join(invalid_assignees)}")
        if valid_assignees:
            try:
                req("POST", f"/issues/{number}/assignees", json={"assignees": valid_assignees})
            except requests.HTTPError as e:
                msg = str(e)
                if "422" in msg and '"field":"assignees"' in msg:
                    print(f"::warning file={md_path}::Update assignees rejected; continuing without changes")
                else:
                    raise

    print(f"Updated issue #{number} from {md_path}")

def upsert_comment(md_path: str):
    # .junie/comments/<issue>/<file>.md
    issue_num = os.path.basename(os.path.dirname(md_path))
    post = parse_front_matter(md_path)
    fm = post.metadata
    body = (post.content or "").strip()
    if not body:
        print(f"Skip empty comment: {md_path}")
        return
    cid = fm.get("id")
    if cid:
        req("PATCH", f"/issues/comments/{cid}", json={"body": body})
        print(f"Edited comment {cid} on issue #{issue_num}")
    else:
        r = req("POST", f"/issues/{issue_num}/comments", json={"body": body}).json()
        print(f"Created comment {r.get('id')} on issue #{issue_num}")

def collect_changed_paths() -> List[str]:
    # The workflow already gated by diff; for workflow_dispatch, process all .junie files
    paths = []
    paths.extend(sorted(glob.glob(".junie/issues/*.md")))
    paths.extend(sorted(glob.glob(".junie/comments/*/*.md")))
    return paths

def main():
    if not (REPO and TOKEN):
        print("Missing GITHUB_REPOSITORY or GITHUB_TOKEN", file=sys.stderr)
        sys.exit(1)

    changed = collect_changed_paths()
    issues = [p for p in changed if p.startswith(".junie/issues/")]
    comments = [p for p in changed if p.startswith(".junie/comments/")]

    errors = []
    for p in issues:
        try:
            upsert_issue(p)
        except Conflict as e:
            print(f"::warning file={p}::{e}")
            errors.append(str(e))
        except Exception as e:
            print(f"::error file={p}::Issue upsert failed: {e}")
            errors.append(str(e))

    for p in comments:
        try:
            upsert_comment(p)
        except Exception as e:
            print(f"::error file={p}::Comment upsert failed: {e}")
            errors.append(str(e))

    if errors:
        sys.exit(1)

if __name__ == "__main__":
    main()
