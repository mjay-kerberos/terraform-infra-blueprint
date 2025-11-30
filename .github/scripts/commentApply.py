#!/usr/bin/env python3
import os
import json
import urllib.request

def main():
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["GITHUB_PR_NUMBER"]

    apply_outcome = os.environ.get("APPLY_OUTCOME", "unknown")
    actor = os.environ.get("GITHUB_ACTOR", "unknown")
    run_id = os.environ.get("GITHUB_RUN_ID", "")

    lines = [
        f"#### Terraform Apply `{apply_outcome}`",
        "",
        "<details><summary>Show Apply Details</summary>",
        "",
        "Apply logs are available in the Actions run:",
        f"https://github.com/{repo}/actions/runs/{run_id}",
        "",
        "</details>",
        "",
        f"*Applied by: @{actor}*",
    ]

    body = "\n".join(lines)

    data = json.dumps({"body": body}).encode("utf-8")
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    with urllib.request.urlopen(req) as resp:
        print(f"Posted apply comment to PR #{pr_number}, status: {resp.status}")
        print(resp.read().decode())

if __name__ == "__main__":
    main()
