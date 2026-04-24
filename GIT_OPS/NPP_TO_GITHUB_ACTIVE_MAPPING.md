# NPP to GitHub Active Mapping

## Purpose

This document extracts the active GitHub-native mapping rules for
`newPhasePlanProcess` from the mixed research and transcript files in `GIT_OPS/`.

It keeps the useful bridge between the planning template and GitHub features and
excludes the later custom projection/controller architecture that has been
archived.

## Source set

This summary is derived from:

- `ChatGPT-Template to GitHub Mapping (1).md`
- `Template to GitHub Mapping.pdf`
- `GitHub Project Management Capabilities and Mapping to a Phase-Process Template.pdf`
- `Technical Execution Processes for Each GitHub Workspace Solution.pdf`
- `gitauto_eval.txt`

## Active mapping rules

| `newPhasePlanProcess` concept | GitHub implementation rule |
| --- | --- |
| Phase | Use a Project single-select field named `Phase`. Do not treat milestones as lifecycle state. |
| Delivery checkpoint | Use milestones for delivery checkpoints, due dates, and completion percentages. |
| Step contract | Use one issue per step as the default rule. |
| Step decomposition | Use sub-issues only when a step needs nested decomposition. |
| Gate | Use GitHub Actions jobs plus required status checks. No merge without required gates passing. |
| Execution | Use pull requests linked to the governing issue. |
| Completion | Completion is represented by issue closure, project status update, and milestone progress. |
| Planning timeline | Use roadmap views plus date or iteration fields. |
| Metadata | Use project custom fields first. Treat org-level issue fields as optional until they are stable for your environment. |
| Intake | Use issue forms and, where useful, draft items for early intake and triage. |
| Visibility | Use saved views, hierarchy view, charts, and roadmap layouts for reporting. |

## Active operational guidance

1. Phases belong in a `Phase` project field, not in milestones.
2. Milestones represent delivery groupings, releases, or checkpoints.
3. A step should map to one issue. Keep the unit of work explicit and stable.
4. A pull request is the execution attempt for one or more governed issues.
5. Gates should be implemented as required checks, not informal review steps.
6. Built-in project automations should be used first for status, auto-add, and auto-archive behavior.
7. Use Actions plus GraphQL only for behavior that built-in automations cannot express.
8. Roadmaps, iterations, and charts are reporting and scheduling layers on top of issues and project items.

## Implementation cautions retained from evaluation

These are still active cautions even in the GitHub-native-first direction:

- Prefer GitHub App auth over PAT-based automation for project mutations.
- Do not hardcode project field IDs or option IDs across environments.
- Keep Windows-specific execution separate from GitHub-hosted Linux control workflows.
- Do not make the core mapping depend on preview-only GitHub features when a stable project-field alternative exists.

## Boundary

This document is the active bridge between `newPhasePlanProcess` concepts and
GitHub-native project management.

Archived custom control-plane, projection, reconciliation, and ProgramSpec-heavy
proposals remain historical context only under `GIT_ARC/`.
