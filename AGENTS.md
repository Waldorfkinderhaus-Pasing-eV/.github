# .github: agent instructions

What this repository is: the [README](README.md). It is public: everything committed here is published at once.

## Commands

```sh
python shared/checks/install_hooks.py    # activate the hooks, once per clone (Python 3.10 or newer, no packages)
python scripts/validate.py --fast        # the pre-commit checks
python scripts/validate.py               # the full validation, run by the pre-push hook and the tag run
```

There is no build: GitHub shows the files as they are. Check a change of a Markdown file in GitHub's preview.

The hooks run these checks, so their rules are not repeated here: `check_commits` (`commit-msg`), `check_comments`, `check_decisions`, `check_personal_data`, `check_links`, `check_readme_agents` and `check_drift` (the [shared checks](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/shared/README.md)).

## Rules no check enforces

- `profile/README.md`, the public organisation page, stays exactly as the owner wrote it; change it only on the owner's explicit instruction ([D1](docs/decisions.md#d1--the-public-organisation-page-stays-as-the-owner-wrote-it)).
- The community files (`CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/`) are the defaults of every repository of the organisation that has none of its own, and they are written in German for the public: a change there changes them for all those repositories ([ADR-0012](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0012-architecture-repository-holds-the-shared-standards.md)).
- Nothing internal goes here: no names or pictures of children and families, no internal documents, no credentials, no screenshots with real data; the repository is public ([ADR-0017](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0017-who-may-read-adebiskita-and-encrypted-snapshots.md)).
- Sign every commit (`-S`) with the responsible human's own identity and key; never push with `--no-verify`; a pull request is merged only when the `pre-push` validation passed on its head ([ADR-0014](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0014-commit-review-and-merge-rules.md), [ADR-0022](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0022-local-hooks-verify-pull-requests-ci-runs-on-tags.md)).
- Before every push, review the full diff against the base branch adversarially, fix real findings and say which were dismissed and why ([ADR-0014](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0014-commit-review-and-merge-rules.md)).
- Record a decision about this repository in [docs/decisions.md](docs/decisions.md) in the same change, as the decision in force ([ADR-0028](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0028-short-comments-and-decision-documents-in-force.md)).
- A shared check is changed in the architecture repository and vendored again, never edited here; `tag-guard.yml` is copied from there unchanged ([ADR-0029](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0029-the-repository-baseline.md)).

## Standards

The [standards](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/standards/README.md) of the architecture repository (`standards/`): [contribution](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/standards/contribution.md), [comments](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/standards/comments.md), [agent instructions](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/standards/agents.md) with its [architecture paragraph](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/standards/agents.md#the-architecture-paragraph), and the [repository baseline](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/standards/repository-checklist.md).

## Architecture

Decisions that bind more than one repository are made in the
[architecture repository](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture).
Read its README before changing an interface, a data flow, an identity or anything another
repository relies on.

- An **ADR** with status *Accepted* is a decision: follow it. The ADRs that bind this
  repository are listed below with what they require here.
- An **RFC** is a proposal, whatever its status short of *Accepted*: it authorises nothing.
  Do not implement it as a rule and do not cite it as one; raise questions in the RFC.
- A question that crosses repositories and has no ADR goes to an RFC, not into local code.
- Local decisions stay in this repository's decisions log.

The rules of this file apply alongside these decisions: a local rule may be stricter than an ADR, never weaker.

### ADRs that bind this repository

- [ADR-0012](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0012-architecture-repository-holds-the-shared-standards.md) (The architecture repository holds the shared standards, and every repository links it): this file carries its architecture paragraph; the community files here are the organisation's public defaults.
- [ADR-0014](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0014-commit-review-and-merge-rules.md) (The same commit, review and merge rules in every repository): the commit rules are checked by `check_commits` in the `commit-msg` hook and the branch check of `scripts/validate.py`; a pull request is merged by squash after the review's findings are fixed and the `pre-push` validation passed on its head.
- [ADR-0017](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0017-who-may-read-adebiskita-and-encrypted-snapshots.md) (Nothing writes to adebisKITA): nothing in this repository reads or writes adebisKITA, its backups or the snapshots of adebiskita-api.
- [ADR-0019](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0019-no-magic-numbers-in-the-code.md) (No magic numbers in the code): `scripts/validate.py` names its numbers.
- [ADR-0022](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0022-local-hooks-verify-pull-requests-ci-runs-on-tags.md) (Pull requests are verified by local hooks; CI runs only when `main` is tagged): the hooks and the tag run of [D2](docs/decisions.md#d2--local-hooks-run-the-shared-checks-the-tag-run-repeats-them), behind the guard `.github/workflows/tag-guard.yml`; whoever merges checks the pull request's title and the signatures. A green tag run releases nothing.
- [ADR-0028](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0028-short-comments-and-decision-documents-in-force.md) (Short comments; decision documents hold only the decision in force): `check_comments` on `scripts/` and the hooks, and `check_decisions` on `docs/decisions.md`.
- [ADR-0029](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0029-the-repository-baseline.md) (The repository baseline): this file, the root README, the hooks and the vendored shared checks in `shared/`; the organisation page `profile/README.md` is not part of it, and `shared/config.json` excludes it from `check_readme_agents` ([D1](docs/decisions.md#d1--the-public-organisation-page-stays-as-the-owner-wrote-it)).

### RFCs that concern this repository (proposals, not rules)

- None.
