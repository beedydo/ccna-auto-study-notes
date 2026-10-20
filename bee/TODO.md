# Beedy · to-do (from Sun 18 Oct; updated Tue 20 Oct)

Goal: teach **T07–T11 from the cards** at Teach-back 2 tonight, then use the **essentials** to catch up on everything else before each Sunday.

**New routine for each topic (about 20 min):**

1. Read the **essentials** file in [`bee-essentials/`](../bee-essentials/README.md) (10–15 min).
2. Do its **5-question self-check**, answers hidden.
3. Open the **full note** in `bee/` only for the parts you missed, and do its 8–10 practice questions if you have time (answer key at the end).
4. Say the **cheat lines** out loud.

Tick `[x]` when done. Put the self-check score as `x/5` and the full-note score as `x/8`.

## Tonight · Tue 20 Oct

Routine per topic (~20 min): read **🟥 Must know** only → close it, say "Say it out loud" from memory → 7-Q self-check, answers hidden → open **🟨** only if you scored 6/7+, otherwise reread the 🟥 parts you missed.

| Done | Topic | Why tonight | Score |
|---|---|---|---|
| [ ] | [T09 API styles](../bee-essentials/T09-api-styles-rest-vs-rpc-sync-vs-async.md) | review: verb location + 202/taskId; T47 builds on it | /7 |
| [ ] | [T10 API auth](../bee-essentials/T10-api-authentication.md) | review: Basic / token / key, 401 vs 403 | /7 |
| [ ] | [T26 Deployment](../bee-essentials/T26-deployment-models-edge-computing.md) | first read; edge/fog/IOx are new | /7 |
| [ ] | [T27 Docker](../bee-essentials/T27-docker.md) | home turf: traps only (`-p HOST:CONTAINER`, CMD vs ENTRYPOINT) | /7 |
| [ ] | [T28 CI/CD](../bee-essentials/T28-ci-cd-devops-principles.md) | home turf: traps only (delivery vs deployment, exam-sim gaps) | /7 |

**Still due before Teach-back 3 (Sun 25 Oct):** T43, T47 and T29 (Thu 22), plus Bob's cycle-1 and cycle-2 cross-study.

## Today · Sun 18 Oct · Teach-back 2

| Done | # | Read | Concepts to cover | Task | Score |
|---|---|---|---|---|---|
| [x] | 1 | [teach-back-2.md](../teach-back/teach-back-2.md) | Your cards for T07–T11 | Cards filled | |
| [x] | 2 | [T07 essentials](../bee-essentials/T07-rest-fundamentals-http-codes.md) · [full](T07-rest-fundamentals-http-codes.md) | URL parts · REST's 6 constraints · CRUD · safe vs idempotent · status codes · `Content-Type` vs `Accept` · curl flags | Reviewed | /5 · /8 |
| [x] | 3 | [T08 essentials](../bee-essentials/T08-api-consumption-constraints.md) · [full](T08-api-consumption-constraints.md) | 429 + `Retry-After` · backoff · 3 paging styles · cursors and resuming · 413 · timeouts · 202 jobs · token expiry · versions · ETag/304 | Reviewed | /5 · /8 |
| [ ] | 4 | [T10 essentials](../bee-essentials/T10-api-authentication.md) · [full](T10-api-authentication.md) | Basic · custom token · API key · cookie · OAuth 2.0 · bearer · 401 vs 403 · secrets in env vars | Essentials → self-check → OAuth GIF → cheat lines | /5 |
| [ ] | 5 | [T09 essentials](../bee-essentials/T09-api-styles-rest-vs-rpc-sync-vs-async.md) · [full](T09-api-styles-rest-vs-rpc-sync-vs-async.md) | REST vs RPC vs SOAP · where the verb and errors live · sync vs async · Catalyst Center (DNA Center) taskId polling | Essentials → self-check → async GIF → cheat lines | /5 |
| [ ] | 6 | [T11 essentials](../bee-essentials/T11-python-requests-scripting.md) · [full](T11-python-requests-scripting.md) | `params` · `json` vs `data` · `headers` · `auth` · `timeout` · `raise_for_status()` · `Session()` · retry on 429 · `verify=` | Essentials → self-check → 429 GIF → cheat lines | /5 |
| [ ] | 7 | [teach-back-2.md](../teach-back/teach-back-2.md) | All 5 cards | Teach them out loud against a 12-min timer (T07 → T10 → T11 → T08 → T09) | |
| [ ] | 8 | [teach-back-1.md](../teach-back/teach-back-1.md) + [teach-back-2.md](../teach-back/teach-back-2.md) | T07–T11 (plus T02–T06 if Teach-back 1 was skipped) | **Teach-back with Bob** | |
| [ ] | 9 | teach-back-2.md · [practice-log.csv](../data/practice-log.csv) | Weak topic IDs · scores | Write the weak IDs at the bottom of teach-back-2, add a score row | |

**Shaky after tonight:**

-

## Cycle 1 catch-up (T02, T04, T05, T06) · Mon 19 – Tue 20 Oct

These were due at Teach-back 1. Use the essentials: about 20 min each.

| Done | # | Read | Concepts to cover | Score |
|---|---|---|---|---|
| [x] | 10 | [T05 essentials](../bee-essentials/T05-unified-diffs.md) | `---`/`+++` · `/dev/null` · hunk headers (counts include context) · `-`/`+` prefixes · big deletion = run of `-` | /5 |
| [ ] | 11 | [T02 essentials](../bee-essentials/T02-functions-classes-modules.md) | `*args`/`**kwargs` · instance vs class attributes · `@classmethod`/`@staticmethod` · `super().__init__()` · `__main__` | /5 |
| [x] | 12 | [T04 essentials](../bee-essentials/T04-git-version-control.md) | 4 areas · `diff` vs `--staged` · `fetch` vs `pull` · conflict markers · `reset` vs `revert` · `rm --cached` | /5 |
| [x] | 13 | [T06 essentials](../bee-essentials/T06-data-formats-parsing.md) | XML vs JSON vs YAML · `json.loads`/`yaml.safe_load`/`xmltodict` · `@`/`#text` · `defusedxml` | /5 |

## Cycle 3 · Mon 19 – Sat 24 Oct · Teach-back 3 on Sun 25 Oct

| Done | # | Day | Read | Concepts to cover | Score |
|---|---|---|---|---|---|
| [ ] | 14 | Mon | [T43 Webhooks](../bee-essentials/T43-webhooks.md) | push vs poll · register · HMAC signature · reply 200 fast · retries + dedupe · public HTTPS / ngrok | /5 |
| [ ] | 15 | Mon | [T47 Sequence diagrams](../bee-essentials/T47-sequence-diagrams-with-api-calls.md) | lifelines · solid vs dashed arrows · `alt`/`opt`/`loop` · auth, async and webhook flows | /5 |
| [ ] | 16 | Tue | [T26 Deployment](../bee-essentials/T26-deployment-models-edge-computing.md) | cloud models · IaaS/PaaS/SaaS · edge vs fog · IOx · bare metal / VM / container | /5 |
| [ ] | 17 | Tue | Bob's cycle-1 notes | **Cross-study:** T01, T03, T12, T13, T35, T36, T39 | |
| [ ] | 18 | Wed | [T27 Docker](../bee-essentials/T27-docker.md) | image vs container · `-p HOST:CONTAINER` · CMD vs ENTRYPOINT · volumes vs bind mounts | /5 |
| [ ] | 19 | Wed | [T28 CI/CD](../bee-essentials/T28-ci-cd-devops-principles.md) | CI vs delivery vs deployment · build once, promote · NetDevOps · DevOps culture | /5 |
| [ ] | 20 | Thu | [T29 Secrets](../bee-essentials/T29-secrets-encryption-data-handling.md) | encode vs hash vs encrypt · symmetric vs asymmetric · TLS · salted hashing · RC4 is broken | /5 |
| [ ] | 21 | Thu | Bob's cycle-2 notes | **Cross-study:** T14–T19 | |
| [ ] | 22 | Fri–Sat | Full notes for T43, T47, T26–T29 | Practice questions on anything you got under 4/5 · `/teachback 3` | |

## Cycle 4 · Mon 26 – Sat 31 Oct · Teach-back 4 on Sun 1 Nov

| Done | # | Day | Read | Concepts to cover | Score |
|---|---|---|---|---|---|
| [ ] | 23 | Mon | [T30 OWASP](../bee-essentials/T30-owasp-xss-sqli-csrf.md) | SQL injection · XSS (stored/reflected/DOM) · CSRF · parameterised queries · output encoding · tokens + SameSite | /5 |
| [ ] | 24 | Mon | [T31 Bash](../bee-essentials/T31-bash.md) | quoting · `$@` · `>` vs `>>` · `2>&1` order · exit codes · `[ ]` vs `[[ ]]` · `pushd`/`popd` | /5 |
| [ ] | 25 | Tue | [T32 TDD](../bee-essentials/T32-tdd-python-unit-tests.md) | red → green → refactor · unittest asserts · setUp/tearDown · mocks · fail vs error | /5 |
| [ ] | 26 | Tue | Bob's cycle-3 notes | **Cross-study:** T20–T25, T37 | |
| [ ] | 27 | Wed | [T33 IaC](../bee-essentials/T33-iac-tool-comparison.md) | declarative vs imperative · push vs pull · agent vs agentless · idempotency · NSO | /5 |
| [ ] | 28 | Wed | [T34 Ansible](../bee-essentials/T34-ansible-playbook-interpretation.md) | play / task / module · `register` + `when` · handlers · `network_cli`/`netconf`/`httpapi` | /5 |
| [ ] | 29 | Thu | [T44 pyATS](../bee-essentials/T44-pyats-genie.md) | testbed · Unicon · Genie parse / learn / diff · AEtest | /5 |
| [ ] | 30 | Thu | [T46 Code review](../bee-essentials/T46-code-review-principles.md) | benefits · process · linters vs humans · feedback · metrics | /5 |
| [ ] | 31 | Fri | | **Swap quiz** with Bob | |
| [ ] | 32 | Sat | Full notes for cycle 4 | Practice questions on anything under 4/5 · `/teachback 4` | |

## Exam-sim weak spots (from `quizzes/exam-sim-review.md`)

Reread the **"Exam-sim gap"** block in each note's concept section, then retry the practice-test question. Do each one on the day its topic comes up above.

| Done | Note | Gap → what to know | Sim Q |
|---|---|---|---|
| [x] | [T05 Diffs](T05-unified-diffs.md) · T05.03 | G24 · big deletion = a run of `-` lines | Q27 |
| [x] | [T06 Data formats](T06-data-formats-parsing.md) · T06.10 | G01 · untrusted XML → `defusedxml` | Q49 |
| [x] | [T07 REST](T07-rest-fundamentals-http-codes.md) · T07.11 | G20 · build a request → Postman / curl | Q5 |
| [ ] | [T26 Deployment](T26-deployment-models-edge-computing.md) · T26.04 | G18 · signed, verified apps on devices → IOx | Q35 |
| [ ] | [T28 CI/CD](T28-ci-cd-devops-principles.md) · T28.06, T28.07 | G23 · pipeline = only route to prod; tickets (Jira) · G07 learning culture = continuous improvement | Q19, Q76, Q45 |
| [ ] | [T29 Secrets](T29-secrets-encryption-data-handling.md) · T29.02 | G22 · least secure in transit → RC4 | Q7 |
| [ ] | [T31 Bash](T31-bash.md) · T31.01 | G09 · `pushd` / `popd` | Q58 |
| [ ] | [T34 Ansible](T34-ansible-playbook-interpretation.md) · T34.03, T34.07 | G12 · one directory per project · `yum`/`apt`/`package` | Q86, Q96 |
| [ ] | [T46 Code review](T46-code-review-principles.md) · T46.01, T46.04 | G13 · set goals + metrics · learning benefit | Q13, Q44 |
| [ ] | [T47 Sequence diagrams](T47-sequence-diagrams-with-api-calls.md) · T47.01 | G14 · vertical lines = endpoints (user/provider) | Q52, Q81 |

**Bob's gaps** (G06, G16, G19, G21: YANG model types, star topology, SDK build env, CUCM AXL) are flagged under `## To verify` in his T12, T14, T18, T21 and T38.

## Open items

- [ ] **T30 full note:** only the essentials exist. Ask Claude to draft the full note (no attack lab) before cycle 4.
- [ ] **Docker:** start Docker Desktop so the T27 drill output can be filled in (before Sun 25 Oct).
- [ ] **`/verify`:** check `⚠ verify` items against Cisco docs on Fri–Sat of each cycle.
- [ ] **`status: verified`:** set it in a note's front matter once you score 6/8 or more on its full-note questions.
- [ ] **Break week (2–8 Nov):** mock exam Mon 2 Nov, joint review Tue, weak-domain Qs Wed–Thu, rapid-fire Fri, rest Sat–Sun. Exam **Mon 9 Nov**.
