# Pipeline: Registry Build Tools

This folder contains the registry build pipeline for otinstaller.

## discover.py

`discover.py` searches GitHub for OSINT-related tools and writes a candidates file
(`pipeline/candidates.yaml`) for manual review and testing.

### What it does

1. Searches GitHub's REST API for repos with OSINT-related topics (osint, osint-tools,
   osint-python, reconnaissance, information-gathering) with 1000+ stars.
2. Filters out:
   - Archived repos
   - Non-Python repos
   - Awesome-lists (name or description contains "awesome")
   - Repos matching the denylist (registry/denylist.yaml)
3. Detects install method from repo root files:
   - `pyproject.toml` or `setup.py` -> `pip-repo`
   - `requirements.txt` -> `git-requirements`
   - Neither -> `unknown`
4. Checks if the repo is published on PyPI (tries name variations).
5. Writes `pipeline/candidates.yaml` with all surviving candidates.

### Requirements

- A `GITHUB_TOKEN` environment variable (no special scopes needed; only reads public data)
- Python 3.10+
- `requests` library (install with `pip install -e ".[pipeline]"`)

### Usage

```bash
# Install the pipeline dependencies
pip install -e ".[pipeline]"

# Run with a limit for testing (recommended first run)
python pipeline/discover.py --limit 100

# Full run (no limit)
python pipeline/discover.py
```

### Output

The script writes `pipeline/candidates.yaml` with entries like:

```yaml
- name: sherlock
  repo: sherlock-project/sherlock
  stars: 50000
  description: "Search usernames across social networks"
  license: MIT
  detected_install_method: pip-repo
  candidate_pip_package: sherlock-project
  default_branch: master
  discovered_at: "2026-09-23T12:34:56+00:00"
```

### Notes

- `candidates.yaml` is an input to the next task (verification), not the final registry.
- The script is safe to re-run; it overwrites `candidates.yaml` cleanly each time.
- Network errors on individual repos are logged and skipped; the script continues.
- GitHub rate limits are respected; the script sleeps if `X-RateLimit-Remaining` drops below 10.

### GitHub Token

The `GITHUB_TOKEN` environment variable must be set. It only needs read access to public
repositories (no special scopes required). The script does not write the token to any
output file.