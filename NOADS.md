# No Ads modification notice

This is an unofficial modified build of MHSanaei/3x-ui, distributed under the original GPL-3.0 license. Original attribution and copyright notices are retained.

Changes introduced on 2026-10-14:

- Remove the Sponsors menu/page and paid placements from overview, sidebar and login.
- Remove sponsor-list and sponsor-logo HTTP routes and their remote fetch implementation.
- Remove the corresponding frontend query/components and obsolete sponsor API documentation/tests.
- Use xinian5216/3x-ui-private for installation, release discovery and panel/CLI updates.
- Publish only stable upstream releases after patch checks, secret checks, frontend/Go tests and all platform builds succeed.

The panel version remains the upstream version for compatibility. This notice and provenance.json inside each package identify the modified build and the exact upstream source commit. Existing user data, protocols and user-configurable MTProto adTag settings are not altered.

Source: https://github.com/xinian5216/3x-ui-private
Original project: https://github.com/MHSanaei/3x-ui
