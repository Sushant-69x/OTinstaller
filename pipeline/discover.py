#!/usr/bin/env python3
"""
Discover OSINT tools on GitHub and write candidates to pipeline/candidates.yaml.
"""

import argparse
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

from otinstaller.denylist import Denylist, check_tool, load_denylist
from otinstaller.registry import Tool

GITHUB_API = "https://api.github.com"
PYPI_API = "https://pypi.org/pypi"

TOPIC_QUERIES = [
    "topic:osint stars:>=1000",
    "topic:osint-tools stars:>=1000",
    "topic:osint-python stars:>=1000",
    "topic:reconnaissance stars:>=1000",
    "topic:information-gathering stars:>=1000",
]

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def get_github_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN")


def make_session() -> requests.Session:
    session = requests.Session()
    token = get_github_token()
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
    session.headers.update(HEADERS)
    return session


def handle_rate_limit(response: requests.Response, session: requests.Session) -> None:
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is not None:
        remaining_int = int(remaining)
        if remaining_int < 10:
            reset = response.headers.get("X-RateLimit-Reset")
            if reset:
                wait_seconds = max(int(reset) - int(time.time()) + 5, 0)
                print(f"Rate limit low ({remaining_int}), sleeping {wait_seconds}s until reset...")
                time.sleep(wait_seconds)


def search_repos(session: requests.Session, query: str, limit: int | None = None) -> list[dict]:
    repos = []
    page = 1
    per_page = 100

    while True:
        if limit and len(repos) >= limit:
            break

        params = {
            "q": query,
            "per_page": min(per_page, limit - len(repos) if limit else per_page),
            "page": page,
            "sort": "stars",
            "order": "desc",
        }

        try:
            print(f"  Searching page {page}...")
            resp = session.get(
                f"{GITHUB_API}/search/repositories",
                params=params,
                timeout=30,
            )
            remaining = resp.headers.get("X-RateLimit-Remaining")
            print(f"  Search response: {resp.status_code}, remaining: {remaining}")
            handle_rate_limit(resp, session)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"Search error for query '{query}': {e}")
            break

        data = resp.json()
        items = data.get("items", [])
        if not items:
            break

        repos.extend(items)
        if len(items) < per_page:
            break

        page += 1

    return repos[:limit] if limit else repos


def fetch_repo_details(session: requests.Session, full_name: str) -> dict | None:
    try:
        print(f"  Fetching details for {full_name}...")
        resp = session.get(f"{GITHUB_API}/repos/{full_name}", timeout=30)
        remaining = resp.headers.get("X-RateLimit-Remaining")
        print(f"  Details response: {resp.status_code}, remaining: {remaining}")
        handle_rate_limit(resp, session)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"Error fetching repo {full_name}: {e}")
        return None


def fetch_repo_root_files(
    session: requests.Session, full_name: str, default_branch: str
) -> list[str]:
    try:
        print(f"  Fetching root files for {full_name}...")
        resp = session.get(
            f"{GITHUB_API}/repos/{full_name}/contents",
            params={"ref": default_branch},
            timeout=30,
        )
        remaining = resp.headers.get("X-RateLimit-Remaining")
        print(f"  Root files response: {resp.status_code}, remaining: {remaining}")
        handle_rate_limit(resp, session)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return [item["name"] for item in data if item["type"] == "file"]
        return []
    except requests.RequestException as e:
        print(f"Error fetching root files for {full_name}: {e}")
        return []


def detect_install_method(root_files: list[str]) -> str:
    if any(f in root_files for f in ("pyproject.toml", "setup.py")):
        return "pip-repo"
    if "requirements.txt" in root_files:
        return "git-requirements"
    return "unknown"


def check_pypi(session: requests.Session, name: str) -> str | None:
    for variant in (name, name.replace("-", ""), name.replace("-", "_")):
        try:
            resp = session.get(f"{PYPI_API}/{variant}/json", timeout=10)
            if resp.status_code == 200:
                return variant
        except requests.RequestException:
            pass
    return None


def sanitize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-")


def truncate_description(desc: str | None, max_len: int = 200) -> str:
    if not desc:
        return ""
    desc = desc.replace("\n", " ").replace("\r", " ")
    desc = re.sub(r"\s+", " ", desc).strip()
    if len(desc) > max_len:
        desc = desc[:max_len].rstrip() + "..."
    return desc


def main():
    parser = argparse.ArgumentParser(description="Discover OSINT tools on GitHub")
    parser.add_argument("--limit", type=int, help="Limit total repos found (for testing)")
    parser.add_argument("--output", default="pipeline/candidates.yaml", help="Output file")
    args = parser.parse_args()

    session = make_session()

    # Load denylist
    denylist_path = Path("registry/denylist.yaml")
    denylist = load_denylist(denylist_path) if denylist_path.exists() else Denylist()

    all_repos = []
    seen = set()

    for query in TOPIC_QUERIES:
        print(f"Searching: {query}")
        repos = search_repos(session, query, limit=args.limit)
        for repo in repos:
            full_name = repo["full_name"]
            if full_name not in seen:
                seen.add(full_name)
                all_repos.append(repo)
        if args.limit and len(all_repos) >= args.limit:
            all_repos = all_repos[: args.limit]
            break

    print(f"Found {len(all_repos)} unique repos before filtering")

    stats = {
        "archived": 0,
        "non_python": 0,
        "awesome_list": 0,
        "denylist": 0,
        "errors": 0,
        "candidates": 0,
        "install_methods": {"pip-repo": 0, "git-requirements": 0, "unknown": 0},
    }

    candidates = []

    for repo in all_repos:
        full_name = repo["full_name"]
        name = repo["name"]

        try:
            # Filter: archived
            if repo.get("archived"):
                stats["archived"] += 1
                continue

            # Filter: non-Python
            language = repo.get("language")
            if language != "Python":
                stats["non_python"] += 1
                continue

            # Filter: awesome list
            desc = repo.get("description") or ""
            if "awesome" in name.lower() or "awesome" in desc.lower():
                stats["awesome_list"] += 1
                continue

            # Fetch more details
            details = fetch_repo_details(session, full_name)
            if not details:
                stats["errors"] += 1
                continue

            # Denylist check
            # Check against denylist capabilities, topics, keywords, repos
            tool_for_check = Tool(
                name=name,
                display_name=name,
                description=details.get("description", "") or "",
                repo=full_name,
                install={"method": "pip", "package": name},
                entrypoint={"command": name},
                capabilities=[],
            )
            if check_tool(tool_for_check, denylist):
                stats["denylist"] += 1
                continue

            # Detect install method
            default_branch = details.get("default_branch", "main")
            root_files = fetch_repo_root_files(session, full_name, default_branch)
            install_method = detect_install_method(root_files)

            # Check PyPI
            candidate_pip = check_pypi(session, name.lower())

            # Build candidate entry
            candidate = {
                "name": sanitize_name(name),
                "repo": full_name,
                "stars": details.get("stargazers_count", 0),
                "description": truncate_description(details.get("description")),
                "license": (
                    details.get("license", {}).get("spdx_id", "unknown")
                    if details.get("license")
                    else "unknown"
                ),
                "detected_install_method": install_method,
                "candidate_pip_package": candidate_pip,
                "default_branch": default_branch,
                "discovered_at": datetime.now(timezone.utc).isoformat(),
            }

            candidates.append(candidate)
            stats["candidates"] += 1
            stats["install_methods"][install_method] = (
                stats["install_methods"].get(install_method, 0) + 1
            )

        except Exception as e:
            print(f"Error processing {full_name}: {e}")
            stats["errors"] += 1
            continue

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(yaml.dump(candidates, sort_keys=False, allow_unicode=True))

    # Print summary
    print("\n=== Discovery Summary ===")
    print(f"Total repos found: {len(all_repos)}")
    print(f"Dropped - archived: {stats['archived']}")
    print(f"Dropped - non-Python: {stats['non_python']}")
    print(f"Dropped - awesome-list: {stats['awesome_list']}")
    print(f"Dropped - denylist: {stats['denylist']}")
    print(f"Errors: {stats['errors']}")
    print(f"Candidates remaining: {stats['candidates']}")
    print("Install method breakdown:")
    for method, count in stats["install_methods"].items():
        print(f"  {method}: {count}")


if __name__ == "__main__":
    main()
