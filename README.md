# Hermes Backup

This repo backs up the *safe-to-version* parts of `~/.hermes` for GitHub.

## What it keeps

- `config.yaml`, `SOUL.md`, cron job definitions
- installed skills in `~/.hermes/skills/`
- local `hooks/`, `plugins/`, `scripts/`, `memories/`
- a git patch of local changes inside `~/.hermes/hermes-agent`

## What it excludes

- secrets and auth material: `.env`, `auth.json`, tokens, cookies
- runtime noise: `logs/`, `cache/`, `sessions/`, `*.db`, pid/lock files
- the full `hermes-agent` checkout; only local diffs are exported

## Sync

```bash
cd ~/hermes-backup
./bin/sync-hermes-backup
```

## Commit

```bash
cd ~/hermes-backup
./bin/sync-hermes-backup
git add .
git commit -m "backup: update hermes config and skills"
```

## Push to GitHub

Create a **private** GitHub repo first, then:

```bash
cd ~/hermes-backup
git remote add origin <your-private-repo-url>
git branch -M main
git push -u origin main
```
