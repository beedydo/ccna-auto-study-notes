---
description: Write a runnable lab for a topic against DevNet Sandbox or local Docker (e.g. /lab T16)
argument-hint: <topic-id>
---
Create a hands-on lab for **$ARGUMENTS** in `labs/$ARGUMENTS/`.

- `README.md`: goal, which DevNet Sandbox (always-on vs reservable) or local-only, env vars needed, the exact full commands to run in the lab container (see `labs/README.md`), expected output, and 3 "what changed / what does this mean" questions.
- Script(s) in Python 3.12 using requests / ncclient / xmltodict / pyyaml / meraki / dnacentersdk / pyats as relevant. Credentials and hosts from env vars only. Handle 401/429 sensibly.
- Look up current sandbox hostnames/credentials on developer.cisco.com at the time of writing; mark `⚠ verify` if unsure, as sandboxes change.
- Keep it under 30 minutes. Link the lab from the topic note's `## Examples`.
