# .github · Waldorfkinderhaus Pasing e. V.

## What this is

The organisation's public GitHub repository. It holds two things:

- **The public profile:** [profile/README.md](profile/README.md) is the page GitHub shows on the overview of the organisation [`Waldorfkinderhaus-Pasing-eV`](https://github.com/Waldorfkinderhaus-Pasing-eV), in German, with the logo and the garden picture from [the association's website](https://www.waldorfkinderhaus-pasing.de/) (their sources: [profile/assets/SOURCES.md](profile/assets/SOURCES.md)).
- **The organisation's shared GitHub defaults:** the [contribution guidelines](CONTRIBUTING.md), the [pull request template](.github/PULL_REQUEST_TEMPLATE.md) and the [issue forms](.github/ISSUE_TEMPLATE) (bug, content correction, suggestion), in German. GitHub shows them in every repository of the organisation that has no such files of its own; a repository's own issue forms or issue configuration replace the whole default folder for issues. The [rights notice](LICENSE.md) applies to this repository only: GitHub does not pass licence files on to other repositories ([GitHub's documentation on default community health files](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)).

## Where it fits in WKP's IT

The map of WKP's IT is the [architecture overview](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture#where-it-fits-in-wkps-it). This repository is the organisation's public face on GitHub and holds no code or data of the kindergarten's systems. Decisions that bind more than one repository are the architecture repository's ADRs; those that bind this repository are listed in [AGENTS.md](AGENTS.md#architecture), among them [ADR-0028](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0028-short-comments-and-decision-documents-in-force.md) (short comments, decisions in force) and [ADR-0029](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0029-the-repository-baseline.md) (the repository baseline this README follows; the profile page is not part of it, [D1](docs/decisions.md#d1--the-public-organisation-page-stays-as-the-owner-wrote-it)).

## Who it is for

- Whoever looks after the organisation's appearance on GitHub and its community files, and AI agents working for them ([AGENTS.md](AGENTS.md)).
- People outside the association who want to report a problem or suggest a change: they read the German [contribution guidelines](CONTRIBUTING.md).

## First steps

You need Git and Python 3.10 or newer (no packages). From the repository's root:

```sh
python shared/checks/install_hooks.py    # activate the hooks, once per clone
python scripts/validate.py               # the full validation, the one the pre-push hook runs
```

There is no build. GitHub shows `profile/README.md` once it is on the default branch `main`; its pictures load from `profile/assets/` through fixed URLs on that branch, which must be changed if the organisation or the branch is renamed. The profile stays timeless on purpose: places, dates, opening hours and vacancies are kept on the website.

## How it is checked

Rules are checks wherever a check can enforce them ([ADR-0029](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0029-the-repository-baseline.md)). The hooks in `.githooks/` run them through `scripts/validate.py` ([D2](docs/decisions.md#d2--local-hooks-run-the-shared-checks-the-tag-run-repeats-them)):

- `pre-commit`: whitespace and conflict markers, executable hooks and the shared checks of the architecture repository in `shared/checks/` (comment length, personal data, decision documents, README and `AGENTS.md` sections, links, drift of the copy);
- `commit-msg`: the commit check, `shared/checks/check_commits.py`;
- `pre-push`: the full validation, with the commits of the branch. It must pass on the head of a pull request before it is merged.

GitHub runs the same full validation only on a signed version tag on `main` and by hand ([ADR-0022](https://github.com/Waldorfkinderhaus-Pasing-eV/architecture/blob/main/adrs/ADR-0022-local-hooks-verify-pull-requests-ci-runs-on-tags.md)).

## Docs, decisions and requirements

- [Decisions](docs/decisions.md): the local decisions of this repository in force.
- [Contribution guidelines](CONTRIBUTING.md) (German): how people outside and inside the association contribute, and the rights to the association's content.
- [Rights and use](LICENSE.md) (German): all rights to the association's own content are reserved; open source only where a licence says so.
- For agents: [AGENTS.md](AGENTS.md).
