# No Ads modification notice

This is an unofficial modified build of MHSanaei/3x-ui, distributed under the original GPL-3.0 license. Original attribution and copyright notices are retained.

Changes introduced on 2026-10-14:

- Remove the Sponsors menu/page and paid placements from overview, sidebar and login.
- Remove sponsor-list and sponsor-logo HTTP routes and their remote fetch implementation.
- Remove the corresponding frontend query/components and obsolete sponsor API documentation/tests.
- Use xinian5216/3x-ui-noads for installation, release discovery and panel/CLI updates.
- Publish only stable upstream releases after patch checks, secret checks, frontend/Go tests and all platform builds succeed.
- Replace upstream publishing/Claude-bot workflows with this repository's release pipeline; preserve bot-only workflow documentation checks as a non-executable archive in `.noads/upstream-bot-context_test.go.txt`. Application and protocol tests remain active.

The panel version remains the upstream version for compatibility. This notice and provenance.json inside each package identify the modified build and the exact upstream source commit. Existing user data, protocols and user-configurable MTProto adTag settings are not altered.

Source: https://github.com/xinian5216/3x-ui-noads
Original project: https://github.com/MHSanaei/3x-ui

## Maintenance rules and documentation

Every stable synchronization restores downstream `AGENTS.md`, `README.md`, `NOADS.md`, `.noads/` and `.github/workflows/` from the current downstream main branch. Their retained contents are compared byte for byte before publication. Upstream workflows and agent instructions cannot replace downstream maintenance rules.

Promotional sponsorship/donation sections in tracked Markdown READMEs (including translations and nested READMEs) and GitHub FUNDING configuration are removed on every sync. Attribution, licenses, technical documentation and normal community integrations remain. Unrecognized inline promotional links stop publication for review. Future changes outside recognized patterns require maintenance; these rules do not promise to recognize every possible future advertisement.
