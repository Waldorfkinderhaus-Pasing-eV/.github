# Decisions

The local decisions of this repository in force: the decision, the reason and the alternatives rejected. Decisions that bind more than one repository are the accepted ADRs of the [architecture repository](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture). A changed decision is rewritten in place, numbers stay, and Git keeps the history ([ADR-0028](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0028-short-comments-and-decision-documents-in-force.md)). A new decision takes the next number and goes last.

## D1 — The public organisation page stays as the owner wrote it

- **Decision** (the owner): `profile/README.md`, the page GitHub shows on the organisation's overview, is left exactly as it is; the repository baseline does not change it. Its pictures stay in `profile/assets/`, their sources in `profile/assets/SOURCES.md`.
- **Why:** it is the association's public face, written in German for families and the public, not a document for people who work on WKP's IT. `check_readme_agents` reads only the root `README.md` and `AGENTS.md`, so the baseline applies to those and not to the profile.
- **Rejected:** giving the profile the sections of ADR-0029 (they are written for a new person at WKP's IT, not for the public).

## D2 — Local hooks run the shared checks; the tag run repeats them

- **Decision:** this repository carries out [ADR-0022](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0022-local-hooks-verify-pull-requests-ci-runs-on-tags.md) and [ADR-0029](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0029-the-repository-baseline.md) with one script, `scripts/validate.py`, that needs Python 3.10 or newer and its standard library only. `pre-commit` runs `validate.py --fast`: `git diff --cached --check`, executable hooks and the shared checks of the architecture repository, vendored in `shared/checks/`. `commit-msg` runs `shared/checks/check_commits.py`. `pre-push` runs `validate.py`: the hooks, the shared checks and the commit check of the branch, refuses a push of another commit than the checked-out one or from a changed working tree, and records its pass per commit in the clone's Git folder. `shared/checks/install_hooks.py` activates the hooks. *Full validation on a version tag* runs the same validation on a signed version tag on `main` and by hand, behind `.github/workflows/tag-guard.yml`, copied unchanged from the architecture repository.
- **Why:** the repository holds no code to test; what can go wrong is a broken link, personal data in a public file, a commit without sign-off or with AI attribution, and the shared checks find those.
- **Rejected:** no checks at all (the repository is public, so a mistake is published at once); a workflow on pull requests (ADR-0022).
