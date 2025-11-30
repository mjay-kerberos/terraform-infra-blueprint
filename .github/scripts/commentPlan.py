#!/usr/bin/env python3
import os
import json
import urllib.request

def main():
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["GITHUB_PR_NUMBER"]

    init_outcome = os.environ.get("TF_INIT_OUTCOME", "unknown")
    validate_outcome = os.environ.get("TF_VALIDATE_OUTCOME", "unknown")
    plan_outcome = os.environ.get("TF_PLAN_OUTCOME", "unknown")

    actor = os.environ.get("GITHUB_ACTOR", "unknown")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "unknown")
    workflow = os.environ.get("GITHUB_WORKFLOW", "unknown")
    run_id = os.environ.get("GITHUB_RUN_ID", "")

    plan_status = "Plan succeeded" if plan_outcome == "success" else "Plan failed"

    approval_message = (
        "\n\n### Changes detected! Please review the plan and approve the apply job in GitHub Actions."
        if plan_status == "Plan succeeded"
        else ""
    )

    lines = [
        "#### Terraform Format and Style: not checked",
        f"#### Terraform Initialization: `{init_outcome}`",
        f"#### Terraform Validation: `{validate_outcome}`",
        "",
        f"#### Terraform Plan Status: {plan_status}",
        "",
        "Terraform plan was uploaded as an artifact (if this step succeeded).",
        f"[View it in the Actions tab](https://github.com/{repo}/actions/runs/{run_id})",
        approval_message,
        "",
        f"*Pusher: @{actor}, Action: {event_name}, Workflow: {workflow}*",
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
        print(f"Posted plan comment to PR #{pr_number}, status: {resp.status}")
        print(resp.read().decode())

if __name__ == "__main__":
    main()
