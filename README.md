<div id="top">

<!-- HEADER STYLE: CLASSIC -->
<div align="center">

# terraform-infra-blueprint

<em>A small but realistic project that shows how to deploy AWS infrastructure with Terraform **the right way** – using GitHub Actions, OIDC, and approval gates instead of running `terraform apply` from your laptop.</em>

<!-- BADGES -->
<img src="https://github.com/mjay-kerberos/terraform-infra-blueprint/actions/workflows/tf-deploy.yaml/badge.svg" alt="Terraform AWS Workflow Status">
<img src="https://img.shields.io/github/last-commit/mjay-kerberos/snort-ansible?style=flat&logo=git&logoColor=white&color=0080ff" alt="last-commit">
<br>

<em>Built with the tools and technologies:</em>
<br>
<img src="https://img.shields.io/badge/Terraform-844FBA.svg?style=flat&logo=Terraform&logoColor=white" alt="Terraform">
<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat&logo=Python&logoColor=white" alt="Python">



</div>
<br>


## Project Goal

This repo is a learning + portfolio project for:

- **Terraform** (IaC for AWS)
- **GitHub Actions** (CI/CD)
- **AWS IAM + OIDC** (secure auth without long-lived keys)

The pipeline is designed to look like what you’d see on a real DevOps / Platform / Security team:

- A **plan** stage that runs on every pull request
- A **manual approval** gate before changes are applied
- An **apply** stage that uses the same Terraform plan file
- **PR comments** summarising what happened – implemented in Python instead of JavaScript


---

## High-Level Architecture

**Flow:**

1. You push a branch and open a PR into `main`.
2. GitHub Actions runs the `IAC – PLAN` job:
   - Checks Terraform formatting.
   - Runs `terraform init`, `terraform validate`, and `terraform plan`.
   - Uploads the generated plan (`tfplan`) as an artifact.
   - Uses a Python script to comment on the PR with the results.
3. A reviewer checks the PR + the Terraform plan.
4. When ready, they approve the protected environment `terraform-prod`.
5. GitHub Actions runs the `IAC – APPLY` job:
   - Downloads the `tfplan` artifact.
   - Runs `terraform apply` using that plan.
   - Uses another Python script to comment on the PR with the apply result.

**Authentication to AWS:**

- Uses **GitHub OIDC** + an IAM role (`TerraformDeploy`).
- No static AWS keys are stored in GitHub.
- The IAM trust policy limits access to this specific repo/branch.

---

##  What’s Implemented

### Terraform

- Uses **Terraform `1.14.0`**.
- AWS provider, region `eu-west-2`.
- Simple Terraform config for POC.

### GitHub Actions Workflow

File: `.github/workflows/tf-deploy.yaml`

- Triggers:
  - On `pull_request` → `main`
  - (Optionally) on `push` with filters, depending on how you configure it.
- Permissions:
  - `id-token: write` – required for OIDC.
  - `pull-requests: write` – to post PR comments.

**Jobs:**

#### `plan` – _IAC – PLAN_

- Checks out the repo.
- Sets up Terraform (`hashicorp/setup-terraform@v3`).
- Configures AWS credentials using OIDC:

  ```yaml
  - name: Configure AWS Creds
    uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
      aws-region: ${{ secrets.AWS_REGION }}
    ```

- Runs:
    - `terraform fmt -check`
    - `terraform init`
    - `terraform validate`
    - `terraform plan -out=tfplan`
- Uploads the `tfplan` file as a short-lived artifact.
- Calls a Python script to comment on the PR with init/validate/plan status.

#### `apply` – _IAC – APPLY_

- Depends on `plan` (`needs: plan`).
- Only runs for pull requests, and behind a protected **environment**:
    
   ```yaml
    environment:
      name: terraform-prod
    ```
    
- Downloads the `tfplan` artifact produced by the plan job.
- Runs:
    - `terraform init`
    - `terraform validate`
    - `terraform apply -auto-approve tfplan`
- Calls another Python script to comment on the PR with the apply result.
    

---

##  Python PR Comment Scripts

Instead of using `actions/github-script` with JavaScript, this repo uses **plain Python** + the GitHub REST API.

### `.github/scripts/commentPlan.py`

- Reads environment variables set by the workflow:
    - `TF_INIT_OUTCOME`, `TF_VALIDATE_OUTCOME`, `TF_PLAN_OUTCOME`
    - `GITHUB_REPOSITORY`, `GITHUB_RUN_ID`, etc.
- Builds a nice Markdown comment that includes:
    - Init / validate / plan status
    - Link to the Actions run
    - A message asking for approval if the plan succeeded
- Posts the comment to the pull request via:
    
    ```python
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    ```
    

### `.github/scripts/commentApply.py`

- Reads `APPLY_OUTCOME` and other metadata.
- Posts a comment summarising the apply result and linking to the logs.

This keeps everything Python-centric for someone more comfortable in Python than JavaScript, while still using modern GitHub workflows.

---

## AWS & Security Notes

This repo is designed to follow good practices:

- **No AWS access keys** are stored in the repo or in Actions.
- Authentication uses **OIDC** + an **IAM role**.
- The IAM trust policy should restrict:
    - `aud` = `sts.amazonaws.com`
    - `sub` to this specific repo/branch (e.g. `repo:mjay-kerberos/terraform-infra-blueprint:ref:refs/heads/main`).
- The actual role ARN is passed in as **GitHub Secrets**:
    - `AWS_ROLE_ARN`
        

If you fork this repo, you’ll need to create your own IAM role and update these secrets.

---

##  Getting Started (if you fork)

1. **Fork the repo.**
2. **Create an IAM OIDC provider and role** in your AWS account:
    - Provider URL: `https://token.actions.githubusercontent.com`
    - Audience: `sts.amazonaws.com`
    - Trust policy conditioned on your repo and branch.
3. **Attach a scoped IAM policy** (don’t use `AdministratorAccess` in production).
4. **Add GitHub Secrets:**
    - `AWS_ROLE_ARN` – the role's ARN
5. **Add your own Terraform files** in the repo root (`.tf` files).
6. **Create a feature branch, open a PR → main.**
    - Watch the `IAC – PLAN` job run.
    - Review the PR comment from `commentPlan.py`.
7. **Approve the `terraform-prod` environment** to let `IAC – APPLY` run.
    - Watch the apply comment appear on the PR.

---

##  Why I Made This Repo

This is a learning + portfolio project to show:

- I understand **Terraform workflows** beyond `terraform apply` on my laptop.
- I can wire up **GitHub Actions** with **AWS OIDC** safely.
- I understand how to use GitHub Actions snippets with **Python** and raw API calls when needed.
