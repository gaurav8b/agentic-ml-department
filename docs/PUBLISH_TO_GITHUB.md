# Publish this project to GitHub

The local project is complete and can be published to a new GitHub repository. The connected GitHub integration available to this build session can inspect and edit files in repositories that already exist, but it does not expose the GitHub operation that creates a brand-new repository. The local build environment also has no authenticated GitHub CLI. Therefore, the owner must create the empty repository once in GitHub; the project files can then be pushed normally.

## Step 1 — create the remote repository

1. Sign in to GitHub in your browser.
2. Open [github.com/new](https://github.com/new).
3. Set the repository name to `agentic-ml-department`.
4. Add the description: `Human-supervised Agentic AI machine-learning department prototype and enterprise SOP`.
5. Choose **Private** for an initial working project. You can make it public later after checking secrets, data and licence requirements.
6. Do not select “Add a README”, `.gitignore` or license; this project already contains those files.
7. Click **Create repository**.

## Step 2 — publish from this project folder

Open a terminal in the extracted `agentic-ml-department` project directory. Make sure `.env` is not present in the files you intend to commit; it is excluded by `.gitignore`.

```bash
git init
git add .
git status
```

Review the `git status` output. Check that `.env`, generated databases, model files and secrets are not included. Then:

```bash
git commit -m "Build supervised agentic ML department prototype"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_ACCOUNT>/agentic-ml-department.git
git push -u origin main
```

Replace `<YOUR_GITHUB_ACCOUNT>` with your GitHub account login. GitHub may open a browser login or ask you to authenticate using your configured Git credential manager.

## Step 3 — verify the repository

Refresh the GitHub repository page. Confirm that the README, source code, docs, tests and Docker Compose files are present. The GitHub Actions `Tests` workflow should start after the first push.

## Step 4 — start the project from the repository

Follow the Docker Compose instructions in the main README. Do not commit `.env`; it contains local credentials. The synthetic database is generated automatically.

## Step 5 — future updates

After making a change:

```bash
git status
git add <files-you-reviewed>
git commit -m "Describe the change"
git push
```

Review diffs before committing. Never commit passwords, API keys, production extracts or real customer data.
