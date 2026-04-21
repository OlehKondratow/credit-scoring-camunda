# Accounts and repository identity

This document explains **which GitHub repository is canonical** and how to avoid accidentally publishing **personal email addresses** in git history or in the repo.

## Canonical upstream

| Item | Value |
|------|--------|
| **Primary GitHub repo** | [OlehKondratow/credit-scoring-camunda](https://github.com/OlehKondratow/credit-scoring-camunda) |
| **Default integration branch** | `develop` (see [git-workflow.md](git-workflow.md)) |

Other remotes (forks, mirrors, or legacy clones) may exist on developers’ machines; treat them as **personal or transitional**, not as the source of truth for releases or CI.

## Analysis (historical identities)

A local note file previously listed **several distinct `user.name` / `user.email` pairs** (including temporary or alternate GitHub-related identities) and a **second remote** under another GitHub user pointing at a fork of this project.

**Implications:**

1. **Commit attribution** — Past commits may show different authors; that is normal after account changes or forks. For **new** work, use one consistent `user.name` and `user.email` per organisation policy.
2. **Privacy** — Email lists and “which account maps to which mailbox” belong in **local or internal** docs, not in a public tree (they are easy to scrape and hard to remove from history once pushed).
3. **Remote confusion** — Before `git push`, confirm `git remote -v` points at the intended repository (upstream vs fork).

## Recommendations

- Set local git identity explicitly in this clone if needed:
  - `git config user.name "…"`
  - `git config user.email "…"`
- To **rewrite display names** for old commits without changing hashes in all cases, maintainers sometimes use `.mailmap`; see `git shortlog -se` and [git-mailmap](https://git-scm.com/docs/gitmailmap).
- Keep a **private** list of your own identities/remotes in `doc/accounts.local.md` (gitignored). Template: [accounts.local.example.md](accounts.local.example.md).

## Related

- [GOVERNANCE.md](../GOVERNANCE.md) — maintainers
- [CONTRIBUTING.md](../CONTRIBUTING.md) — branches and PRs
- [SECURITY.md](../SECURITY.md) — reporting issues safely
