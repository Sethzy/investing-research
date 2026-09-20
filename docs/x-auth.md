# Connect your own X account

No X developer key is needed. Bird reads your existing browser login locally and makes read-only requests. A Git clone contains no account or session. Each recipient must authenticate independently.

## First connection

1. Open X in your normal **Chrome, Brave, Edge or Firefox** browser and sign in yourself. Complete any X login challenge there.
2. Find the profile containing that session. For Chrome, open `chrome://version` and read **Profile Path**. For Edge use `edge://version`; for Brave use `brave://version`. Use the final directory name (for example `Default` or `Profile 2`) or its full absolute path. Firefox: `about:profiles` → Root Directory; supply that absolute directory.
3. Run `uv run invest setup` and enter that browser/profile. With saved settings, use `uv run invest setup --edit` to change them. Do not send a screenshot containing other private browser information.
4. Allow the local Python process access to the browser's encrypted cookies if your operating system prompts. This can require an interactive desktop session.
5. Run `uv run invest doctor --live-x`. Success means `x.status` is `ok`. Zero returned posts can still be a successful bounded query; an error is never proof that nothing happened on X.

The validated platform is macOS. Other OS/browser combinations may need different cookie-access support. The setup guide does not promise that Chrome encrypted cookies are readable on every platform.

## When the check fails

| Code / symptom | What to do |
|---|---|
| `credentials_unavailable` | Confirm X is logged in in the selected profile, verify Profile Path, and resolve local OS access prompts. If the cookie database is locked, close that browser and retry. Try another supported browser with your own fresh login if extraction remains unsupported. |
| `authentication_failed` | Reopen X in that profile, complete any challenge or sign in again, then retry. |
| `dependency_missing` | Rerun the installer; verify `node --version` is 22+ and use `uv run` so the Python environment is active. |
| `rate_limited` | Stop repeated attempts and retry later. Retain the failed-coverage receipt. |
| `upstream_failed` | X may have changed its web endpoints or a request may have failed. Retry later; use the host's authenticated browser for an explicitly labelled manual capture if needed. |
| Works interactively, fails scheduled | Verify that the host can run, the desktop is available, and the selected profile/Keychain can be accessed in that execution context. Test the actual scheduled run. |

Recheck with `doctor --live-x` after a relevant change. Reinstalling the project does not repair an expired session. Do not repeatedly attempt to bypass login challenges.

## Credential handling

Never paste cookies, passwords, tokens or browser databases into chat, issues, Git or setup answers. The adapter extracts only the X session values it needs, passes them to its local Node process via stdin, and excludes them from returned results and diagnostic output. It does not save them in project configuration. The upstream client receives no posting or messaging command.

If `X_AUTH_TOKEN` or `X_CT0` were already set in your environment, they override browser extraction and must be supplied together. Clear stale overrides locally to test browser authentication. The normal setup interview does not request or store these values.

Bird depends on X's web endpoints; authentication can expire and those endpoints can change. Keep coverage failures visible, even after a previous successful check. A signed-in browser fallback helps the research continue but does not establish that automated Bird monitoring is healthy.
