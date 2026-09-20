# X adapter and upstream provenance

The application uses a read-only vendored subset of **@steipete/bird 0.8.0**, copyright Peter Steinberger, MIT license retained at `src/investing_research/vendor/bird-search/LICENSE`. Source: <https://github.com/steipete/bird>. The initial snapshot is the search subset distributed by <https://github.com/mvanhorn/last30days-skill>; its package metadata identifies 0.8.0. This is a version-labelled snapshot, not a verified pristine upstream Git commit. Existing local copies supplied the snapshot; they are not runtime dependencies.

`vendor/x-detail.mjs` integrates the upstream search client and TweetDetail primitives directly. It has no posting, liking, following, messaging, or brokerage operations. The Python adapter uses `browser-cookie3` to load only X-domain sessions and passes auth_token/ct0 via the Node child's stdin. Credentials are never included in command arguments, returned results, configuration or logs. Upstream diagnostics are discarded and errors are sanitized. Runtime feature/query caches use a temporary directory rather than a shared personal Bird installation.

## Setup and session selection

Install the project's Python dependencies, install Node.js 22 or newer, and sign into X in Chrome, Brave, Edge or Firefox. A Chrome profile name such as `Profile 3` is resolved using the current OS's normal browser directory. An absolute profile directory or cookie database path may also be supplied; Firefox requires an absolute path when selecting a profile explicitly. Omitting the profile uses browser-cookie3's default lookup. OS Keychain access may require an interactive authorization; encrypted-cookie support varies by OS/browser version. Never share your browser profile or session secrets with a repository recipient.

`X_AUTH_TOKEN` and `X_CT0` are optional session-cookie alternatives for a process environment; these are existing login sessions, not developer API keys. Both must be set together. Do not put them into shell commands, committed files, or diagnostic transcripts.

The API exports `search(query, count=50, browser='chrome', profile=None)` and `capture(url, browser='chrome', profile=None)`. Both return `status`, `posts`, and `coverage`; failure returns a sanitized `error.code` and `error.message`. Search accepts 1–100 results, requests Latest ordering, and limits paging to five pages. Coverage is always non-exhaustive. Search previews are marked partial. Exact post text is marked complete only when TweetDetail supplies an ordinary full_text payload matching the extracted text without a truncation flag, trailing ellipsis, or pending note/article, or supplies the full note_tweet text. Completeness is scoped to post_text; threads, media and linked content remain outside that claim. Articles and uncertain payloads remain partial. Exact captures additionally return the accessible `conversation` array.

## Maintenance and limitations

X's private web endpoints can change without notice. A valid session today does not guarantee unattended operation tomorrow. Auth failures, rate limits and upstream changes are errors, not empty successful checks. Use the normal signed-in browser as a manual fallback. HTTP 429 and 5xx responses receive at most two short bounded retries per request, under a 180-second subprocess ceiling. Authentication failures receive no retries. The integration never bypasses login challenges. Search snapshots do not independently verify claims or establish complete coverage of any time interval.

Intentional vendored modification: search response validation rejects a missing timeline instructions array rather than treating an unknown response shape as a successful empty search.

## Verification, 2026-09-20

Live standalone smoke using this repo's Python environment (`browser-cookie3 0.20.1`), Node 23.11.0 and an explicitly selected signed-in Chrome profile passed:

- Keyword `"Metals X"`: three Latest results returned at a requested limit of three; marked capped.
- Date-filtered `"Metals X" since:2026-09-01 until:2026-09-21`: five results returned; all publication timestamps fell within the requested interval; marked capped.
- Exact post <https://x.com/utopia_escape/status/2098825471953605036>: 286 characters of accessible post text returned through TweetDetail; post-text completeness rechecked against the raw TweetDetail truncation/note fields; thread completeness remains partial.

The session belongs to the local operator and is not distributed. Fresh-user authentication and unattended host/session availability remain environment-specific setup checks. The shipped unit tests exercise invalid inputs, missing credentials, capped results, conservative completeness, sanitized errors and exact-post conversation handling.
