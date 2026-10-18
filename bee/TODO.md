# Beedy · catch-up to-do (Sat 17 – Sun 18 Oct)

Goal: be able to **teach T07–T11 from the cards** at Teach-back 2 (Sun 18 Oct), and catch up on T02, T04, T05 and T06.

**Routine for each topic:** overview sheet → skim the bold lines, tables and diagrams → lab or GIF → 8 practice questions on paper, closed book → reread only what you missed → say the card out loud.

Tick `[x]` when a task is done. Put your score as `x/8` in the Score column.

## Saturday 17 Oct

| Done | # | Document | Concepts to cover | Task | Score |
|---|---|---|---|---|---|
| [x] | 1 | [teach-back-2.md](../teach-back/teach-back-2.md) | Your cards for T07–T11 | Ask Claude to fill the cards | |
| [x] | 2 | [T07 REST + HTTP codes](T07-rest-fundamentals-http-codes.md) | URL parts · REST's 6 constraints · CRUD methods · safe vs idempotent · request and response parts · `Content-Type` vs `Accept` · status code classes and key codes · curl flags | Overview sheet → skim → `bash labs/T07/run_lab.sh` → CRUD GIF → 8 questions → say the card | /8 |
| [ ] | 3 | [T10 API authentication](T10-api-authentication.md) | Basic auth · custom token · API key · session cookie · OAuth 2.0 flow · bearer token · 401 vs 403 · secrets in env vars | Overview sheet → skim → OAuth GIF → 8 questions → say the card | /8 |
| [ ] | 4 | [T11 Python requests](T11-python-requests-scripting.md) | `get`/`post` · `params` · `json` · `headers` · `auth` · `timeout` · `.json()` · `raise_for_status()` · `Session()` · retry on 429 · exceptions · `verify=` | Overview sheet → skim → `bash labs/T11/run_lab.sh` → 429 GIF → 8 questions → say the card | /8 |
| [x] | 5 | [T08 API limits](T08-api-consumption-constraints.md) | 429 + `Retry-After` · backoff · 3 paging styles · request size limit (413) · timeouts and 504 · 202 async jobs · token expiry · API versions · ETag/304 | Overview sheet → skim → `bash labs/T08/run_lab.sh` → 8 questions → say the card | /8 |
| [ ] | 6 | [T09 API styles](T09-api-styles-rest-vs-rpc-sync-vs-async.md) | REST vs RPC vs SOAP · where the verb and errors live · sync vs async · Catalyst Center taskId polling | Overview sheet → skim → async GIF → 8 questions → say the card | /8 |
| [ ] | 7 | [teach-back-2.md](../teach-back/teach-back-2.md) | All 5 cards (T07–T11) | Say each from memory; list the shaky ones below | |

**Shaky after Saturday:**

-

## Sunday 18 Oct

| Done | # | Document | Concepts to cover | Task | Score |
|---|---|---|---|---|---|
| [ ] | 8 | [T05 Unified diffs](T05-unified-diffs.md) | `---`/`+++` · `/dev/null` · hunk headers (counts include context lines) · the space/`-`/`+` prefixes · 3 lines of context | Overview sheet → skim → 8 questions → say the card | /8 |
| [ ] | 9 | [T02 Functions, classes, modules](T02-functions-classes-modules.md) | `*args`/`**kwargs` · instance vs class attributes · `@classmethod`/`@staticmethod` · `super().__init__()` · `__main__` | Overview sheet → `super()` GIF → 8 questions → say the card | /8 |
| [ ] | 10 | [T04 Git](T04-git-version-control.md) | The 4 areas · `diff` vs `diff --staged` · `fetch` vs `pull` · conflict markers · `reset` vs `revert` · `rm --cached` | Overview sheet → workflow GIF → 8 questions → say the card | /8 |
| [ ] | 11 | [T06 Data formats](T06-data-formats-parsing.md) | XML vs JSON vs YAML rules · `json.loads`/`yaml.safe_load`/`xmltodict.parse` · the `@` and `#text` keys · navigating with `["key"][0]` | Overview sheet → 8 questions → say the card | /8 |
| [ ] | 12 | Notes T02–T11 | The questions you got wrong | Redo only those | |
| [ ] | 13 | [teach-back-2.md](../teach-back/teach-back-2.md) | All 5 cards (T07–T11) | Teach them out loud against a 12-minute timer | |
| [ ] | 14 | [teach-back-1.md](../teach-back/teach-back-1.md) + [teach-back-2.md](../teach-back/teach-back-2.md) | T02, T04–T11 | Teach-back with Bob (plus a 10-minute T02–T06 round if Teach-back 1 was skipped) | |
| [ ] | 15 | teach-back-2.md · [practice-log.csv](../data/practice-log.csv) · each note's front matter | Weak topic IDs · scores · status | Write the weak IDs in teach-back-2, add a score row, set `status: verified` on every topic scoring 6/8 or more | |

## Exam-sim weak spots (from `quizzes/exam-sim-review.md`)

Each row now has an **"Exam-sim gap"** block in the note's concept section, plus a new exam trap. Reread the block, then try the practice question again.

| Done | Note | Gap → what to know | Sim Q |
|---|---|---|---|
| [ ] | [T05 Diffs](T05-unified-diffs.md) · T05.03 | G24 · big deletion = a run of `-` lines | Q27 |
| [ ] | [T06 Data formats](T06-data-formats-parsing.md) · T06.10 | G01 · untrusted XML → `defusedxml` | Q49 |
| [ ] | [T07 REST](T07-rest-fundamentals-http-codes.md) · T07.11 | G20 · build a request → Postman / curl | Q5 |
| [ ] | [T26 Deployment](T26-deployment-models-edge-computing.md) · T26.04 | G18 · signed, verified apps on devices → IOx | Q35 |
| [ ] | [T28 CI/CD](T28-ci-cd-devops-principles.md) · T28.06, T28.07 | G23 · pipeline = only route to prod; tickets (Jira) · G07 learning culture = continuous improvement | Q19, Q76, Q45 |
| [ ] | [T29 Secrets](T29-secrets-encryption-data-handling.md) · T29.02 | G22 · least secure in transit → RC4 | Q7 |
| [ ] | [T31 Bash](T31-bash.md) · T31.01 | G09 · `pushd` / `popd` | Q58 |
| [ ] | [T34 Ansible](T34-ansible-playbook-interpretation.md) · T34.03, T34.07 | G12 · one directory per project · `yum`/`apt`/`package` | Q86, Q96 |
| [ ] | [T46 Code review](T46-code-review-principles.md) · T46.01, T46.04 | G13 · set goals + metrics · learning benefit | Q13, Q44 |
| [ ] | [T47 Sequence diagrams](T47-sequence-diagrams-with-api-calls.md) · T47.01 | G14 · vertical lines = endpoints (user/provider) | Q52, Q81 |

**Bob's gaps** (G06, G16, G19, G21: YANG model types, star topology, SDK build env, CUCM AXL) were added under `## To verify` in his T12, T14, T18, T21 and T38.

## Deferred (next week, cycle 3)

- [ ] `/verify` T07–T11 against Cisco docs (cycle-3 check days, 23–24 Oct)
- [ ] T30 OWASP: Claude drafts it without an attack lab (due Sat 31 Oct)
- [ ] Start Docker Desktop so the T27 drill can run (before Sun 25 Oct)
- [ ] Cross-study Bob's cycle-1 notes (Tue 20 Oct) and cycle-2 notes (Thu 22 Oct)
