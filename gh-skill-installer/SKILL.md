---
name: gh-skill-installer
description: Discover, security-audit, and install popular agent skills (SKILL.md format) from GitHub into a local skills directory. Use when the user says "search GitHub for skills", "install a skill from GitHub", "find popular X skills and add them", or wants to grow their skill library from community repos.
license: MIT
---

# GitHub Skill Installer

Workflow for pulling well-regarded community skills (Claude Code / Cursor / Codex / WorkBuddy `SKILL.md` format) from GitHub into a local skills folder, with a mandatory security audit.

## When to use
- User asks to find/install popular skills from GitHub ("最好用热门的 skill", "install UI design skills").
- Growing a personal skills repo (e.g. `D:/AI SKILLS`).

## Steps

### 1. Inventory what's already installed
List the target skills dir first. Do NOT re-install duplicates or near-duplicates.
- If target is a git repo, check `.gitignore` so copied skills won't be excluded.

### 2. Search for candidates
- `WebSearch` queries like: `best popular <category> skill github claude code SKILL.md`, `<category> frontend skill AI coding agents 2026`.
- Cross-check stars/installs and recency. Prefer official + top-community repos.
- Verify a candidate repo actually exists with `WebFetch https://github.com/<owner>/<repo>` before cloning (404s are common — e.g. `vercel/agent-skills` does not exist).
- Skip repos that are off-topic (e.g. "BuilderIO/skills" is code-agent planning/recap, not UI *aesthetic* design).

### 3. Clone
Temp dir: `/c/Users/13588/AppData/Local/Temp/skill_clones` (scratch work stays in temp).
- Whole repo: `git clone --depth 1 <url> <name>`
- Single skill from a big repo (e.g. `anthropics/skills`): sparse checkout:
  `git clone --filter=blob:none --sparse --depth 1 <url> <name> && cd <name> && git sparse-checkout set skills/<skill>`
- Skill folders usually live at `.claude/skills/<name>/` or `skills/<name>/`. Copy that `<name>` folder, not the whole repo.

### 4. Security audit (MANDATORY before install)
Scan every copied skill (SKILL.md + `scripts/`, `references/`, `assets/`) for:
`curl |wget |base64 -d|/dev/tcp|nc -e|rm -rf|os.system|subprocess|eval\(|exec\(|requests.post|fetch\(|axios|child_process|process.env|git push|ssh -`
Also eyeball any `*.py`/`*.cjs` that fetch external URLs or read env vars.
- **P0** (reverse shell, credential exfil, destructive): STRONGLY warn, require explicit confirmation.
- **P1** (suspicious but explainable): warn + confirm.
- **P2** (clean / opt-in API key usage / curated asset URLs): proceed.
Document the verdict in the reply.

### 5. Install
`cp -r <temp>/<skill> "<SKILLS_DIR>/<skill>"` — preserve the folder (SKILL.md + subfolders).
Verify with: `awk` front-matter parse to confirm `name`/`description`; `git status --short` to confirm not ignored.

### 6. Report
Summarize: which skills added, source + stars, file counts, what gaps they fill, audit verdict. Note any skipped near-duplicates.

## Notes
- Skills activate after the agent restarts / re-reads the skills dir.
- For a git-backed skills repo, the user may want to `git add` + commit the new folders (not done unless asked).
- This skill itself was created after completing a "search GitHub for UI design skills" task.
