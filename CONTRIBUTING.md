# Contributing (Beedy and Bob)

## One-time setup

**Beedy (repo owner)** adds Bob as a collaborator:

```bash
gh api --method PUT repos/beedydo/ccna-auto-study-notes/collaborators/BOB_GITHUB_USERNAME --field permission=push
```

Then replace `BOB_GITHUB_USERNAME` in `.github/CODEOWNERS`.

**Bob** accepts the invite and clones:

```bash
gh repo clone beedydo/ccna-auto-study-notes
cd ccna-auto-study-notes
git config user.name "Bob (Jun Hao)"
git config user.email "BOB_EMAIL"
```

**Both**, optionally, build the lab container once:

```bash
docker build --tag ccna-auto-lab:latest --file labs/Dockerfile labs/
```

## Per-batch workflow

1. Create a branch for the batch:

   ```bash
   git switch main
   git pull --ff-only origin main
   git switch --create beedy/batch-2-apis
   ```

2. In Claude Code, for each of your topics: `/note TXX` → read it → `/verify TXX` → do the questions → set `status: verified` yourself.

3. Commit each topic on its own:

   ```bash
   git add notes/d2-apis/T07-*.md
   git commit --message "T07: draft REST fundamentals notes"
   ```

4. Before the teach-back, run `/teachback N`, then commit and push:

   ```bash
   git push --set-upstream origin beedy/batch-2-apis
   gh pr create --base main --head beedy/batch-2-apis --title "Batch 2: APIs (T07-T11)" --body-file .github/pull_request_template.md
   ```

5. The partner reviews the PR. Use review comments for questions; this is practice for blueprint 5.13.
6. Merge after the teach-back:

   ```bash
   gh pr merge beedy/batch-2-apis --squash --delete-branch
   ```

## Rules

- Edit only your own topic notes (`owner:` in front matter). For your partner's notes, comment on the PR or add an item under `## To verify` in your branch.
- Shared files (`cheatsheet.md`, `teach-back/*.md`, `data/practice-log.csv`): edit only your own section or rows.
- Never commit secrets. `labs/.env` is git-ignored; use `labs/.env.example` as the template.
- Status flow: `not-started` → `drafted` (Claude) → `verified` (you) → `taught` (after the teach-back).
