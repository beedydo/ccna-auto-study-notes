# Beedy · to-do (updated Sat 24 Oct)

**Done = verified.** Tick a box only once you've reviewed the note against sources, done its practice questions, and set `status: verified` in its front matter. Tell me the topic and I'll set the status.

**Routine per topic (~20 min):** read **🟥 Must know** in the essentials → close it, say "Say it out loud" from memory → self-check, answers hidden → open **🟨** only if you did well, otherwise reread the 🟥 parts you missed → verify against `## Sources` → do the full note's practice questions → tell me to set `status: verified`.

## Topics left to cover (10 of 22)

| Done | Topic | Note |
|---|---|---|
| [ ] | T30 OWASP | **drafted 25 Oct** — full note + labs/T30/defences.py ready, needs your first pass |
| [ ] | T43 Webhooks | essentials still unread |
| [ ] | T47 Sequence diagrams | essentials still unread |
| [ ] | T11 Python requests scripting | |
| [ ] | T29 Secrets, encryption, data handling | essentials unread |
| [ ] | T31 Bash | |
| [ ] | T32 TDD + unit tests | |
| [ ] | T44 pyATS + Genie | |
| [ ] | T46 Code review principles | |
| [ ] | T27 Docker | Docker Desktop not running — needed for the drill output |

## ✅ Verified (12 of 22)

T02, T04, T05, T06, T07, T08, T09, T10, T26, T28, T33, T34.

## 🔁 Cross-study Bob's notes (not started)

| Done | Cycle | Topics |
|---|---|---|
| [ ] | 1 | T01, T03, T12, T13, T35, T36, T39 |
| [ ] | 2 | T14–T19 |
| [ ] | 3 | T20–T25, T37 |

## Exam-sim weak spots still open

Reread the **"Exam-sim gap"** block in each note, then retry its practice-test question.

| Done | Note | Gap → what to know | Sim Q |
|---|---|---|---|
| [ ] | [T26 Deployment](T26-deployment-models-edge-computing.md) · T26.04 | G18 · signed, verified apps on devices → IOx | Q35 |
| [ ] | [T28 CI/CD](T28-ci-cd-devops-principles.md) · T28.06, T28.07 | G23 · pipeline = only route to prod; tickets (Jira) · G07 learning culture = continuous improvement | Q19, Q76, Q45 |
| [ ] | [T29 Secrets](T29-secrets-encryption-data-handling.md) · T29.02 | G22 · least secure in transit → RC4 | Q7 |
| [ ] | [T31 Bash](T31-bash.md) · T31.01 | G09 · `pushd` / `popd` | Q58 |
| [ ] | [T34 Ansible](T34-ansible-playbook-interpretation.md) · T34.03, T34.07 | G12 · one directory per project · `yum`/`apt`/`package` | Q86, Q96 |
| [ ] | [T46 Code review](T46-code-review-principles.md) · T46.01, T46.04 | G13 · set goals + metrics · learning benefit | Q13, Q44 |
| [ ] | [T47 Sequence diagrams](T47-sequence-diagrams-with-api-calls.md) · T47.01 | G14 · vertical lines = endpoints (user/provider) | Q52, Q81 |

Done already: T05.03, T06.10, T07.11.

**Bob's gaps** (G06, G16, G19, G21: YANG model types, star topology, SDK build env, CUCM AXL) are flagged under `## To verify` in his T12, T14, T18, T21 and T38 — his to fix.

## Open items

- [x] **T30 OWASP drafted 25 Oct.** Full note, overview sheet, 4 diagrams, defensive lab, 8 practice Qs. Review it and tell me to set `status: verified`.
- [ ] **Docker Desktop isn't running.** Needed to fill in the T27 drill output.
- [ ] **`practice-log.csv` is empty.** No scores logged all cycle.
- [ ] **`/verify`:** check `⚠ verify` items against Cisco docs — none done yet this cycle.
- [ ] **Share with Bob:** `assets/T06/02-cisco-api-formats.png` (data format + first parse step for every Cisco API in his topics).
- [ ] **Ask Bob:** where `quizzes/question-bank/` (≈500 MB, a `dump/` folder) came from. Remove it if it's exam dumps.
- [ ] **Review (optional):** the "Looks like…" column in every essentials trap table is new wording written by Claude; skim it while studying.
- [ ] **Break week (2–8 Nov):** mock exam Mon 2 Nov, joint review Tue, weak-domain Qs Wed–Thu, rapid-fire Fri, rest Sat–Sun. Exam **Mon 9 Nov**.
