# T28 · CI/CD + DevOps principles: essentials

> Blueprint 4.4, 4.12, 5.4 · Full note: [bee/T28-ci-cd-devops-principles.md](../bee/T28-ci-cd-devops-principles.md) · Teach-back 2026-10-25

## In one picture
![T28 at a glance: CI, CD, pipeline components, NetDevOps and DevOps principles](../assets/T28/00-overview.png)
*The top row follows one commit left to right (Source → CI → Artifact → CD → Operate) with a red dashed feedback loop back; the bottom row covers NetDevOps, DevOps culture and tools, and red boxes are exam traps.*

## The big idea
- You already run pipelines for a living, so this topic is mostly about the exam's exact vocabulary: CI vs CD, delivery vs deployment, stage order, CALMS and the Three Ways.
- The one genuinely new part is **NetDevOps**: treating network config like application code, with Git as the source of truth and a pipeline that tests changes in a simulated network before touching real devices.
- Think of a pipeline as an assembly line with quality checkpoints. Any failed check stops the line, and the same finished product (the artifact) is what gets shipped to every store (environment).

## What you need to know

### 1. CI vs CD, and delivery vs deployment

![CI vs CD boundary](../assets/T28/01-ci-cd-boundary.png)
*Blue is CI, which ends with a tested, packaged artifact; green is CD, which moves that artifact through environments; the yellow gate is the only difference between delivery and deployment.*

- **Continuous integration (CI)** means every developer merges small changes into the main branch **at least daily**, and every push or merge request triggers an automated build that includes tests.
- CI exists to stop "integration hell" from long-lived branches. A bug is found minutes after the commit that caused it, by the person who wrote it, so main stays **green and releasable**.
- **Fail fast:** the first failing stage stops the run, and later stages are skipped. A broken main build is fixed immediately or the commit is reverted.
- CI is a practice, not a product. Running Jenkins on a branch nobody merges for a month is not CI.
- CI ends with a tested artifact. **CD** takes that same artifact and promotes it through dev → staging → prod.

| | Continuous **delivery** | Continuous **deployment** |
|---|---|---|
| Every change | Is built, tested and ready to deploy | Is built, tested **and deployed** |
| Prod deploy | A **human approves** (button, approval) | **Automatic** when all stages pass |
| GitLab | `when: manual` on the prod job | Remove that line |
| GitHub Actions | Environment with **Required reviewers** | No protection rule |
| Jenkins | An `input` step in the prod stage | Remove the `input` |
| Needs | Good tests | Excellent tests, monitoring and fast rollback |

- Both are called "CD", so read the scenario for the human. "Approval", "manual", "button", "business decides" → **delivery**. "Automatically to production", "no human" → **deployment**.

### 2. The parts of a pipeline and their order

![Pipeline components](../assets/T28/02-pipeline-components.png)
*Purple is stored in a repo, blue is the CI stages, green is the environments and monitoring, and the dotted line is the feedback loop.*

| Component | What it does | Examples |
|---|---|---|
| **Source repo** | Single source of truth for code and the pipeline file; a push or MR is the trigger | GitHub, GitLab, Bitbucket |
| **CI server and runner** | Reads the pipeline file and runs jobs in clean workers, often containers | GitLab runner, Jenkins agent |
| **Lint / static checks** | Cheapest checks first: syntax, style, schema, security and secret scans | pylint, yamllint, Bandit |
| **Build** | Compiles or packages, often into a container image | `docker build` |
| **Test** | **Unit** tests (one function, fast) in CI; **integration** tests (parts together) against a deployed env | pytest, pyATS |
| **Artifact repo** | Stores the versioned output so every env gets **the same bytes** | ECR, Harbor, Nexus, Artifactory |
| **Deploy stages** | dev → staging → prod, with gates before prod | Ansible, Helm, Terraform |
| **Notify and monitor** | Tells the committer, and watches prod | Webex/Slack bot, Prometheus, Grafana |

- **The order the exam wants:** source → build → test → store artifact → deploy dev → staging → (approval) → prod → monitor. Some diagrams merge lint into test, but tests always come **before** any deploy, and the artifact is created **before** the deploy stages.
- **Build once, promote many.** If you rebuild for each environment, prod runs bytes nobody tested.
- **Which stage catches what:** a syntax or bad-VLAN error → lint; a function returning the wrong value → unit test; two services not talking → integration test on staging; config applied but BGP down → post-change check.

![Animated pipeline run](../assets/T28/05-pipeline-run.gif)
*Push → lint → test → package once → dev → staging → prod waits for approval; the next commit fails a test and every later stage is skipped.*

### 3. Pipeline tools and pipeline as code (awareness level)

| | GitLab CI | GitHub Actions | Jenkins |
|---|---|---|---|
| File | `.gitlab-ci.yml` at the repo **root** | `.github/workflows/*.yml` | `Jenkinsfile` (Groovy) |
| How order works | `stages:` list; jobs in the same stage run in parallel | All jobs parallel unless ordered with `needs:` | Stages run in sequence |
| Where it runs | `image:` on a runner | `runs-on: ubuntu-latest` | `agent` |
| Manual gate | `when: manual` | Required reviewers | `input` step |

- **Pipeline as code** means the pipeline definition lives in the **same repo** as the app. It gets code review, history and an audit trail like any other code.
- GitLab's default stages, if you don't define any, are `.pre`, `build`, `test`, `deploy`, `.post`.
- At exam level you only need to match a file name to its tool and read the stage order from a snippet.

### 4. Why bother (benefits)

| Scenario wording | Benefit |
|---|---|
| "Release weekly instead of quarterly", "small changes" | Faster, smaller, more frequent releases (smaller blast radius) |
| "No more copy-paste deploy runbook" | Fewer manual errors and repeatable deploys |
| "The bug was found 5 minutes after the commit" | Early defect detection, which is cheaper to fix |
| "The bad release was undone in 2 minutes" | Quick rollback by redeploying the **previous artifact** |
| "Everyone sees which commit broke it" | Visibility and feedback |

### 5. CI/CD for the network (NetDevOps)
- **The old way:** an engineer SSHes into each device and types config. There is no review and no test, devices drift apart, and the only record of the change is the device itself.
- **NetDevOps** applies CI/CD to the network. The desired state, called **intent** (VLANs, interfaces, BGP neighbours, ACLs), is stored as data in Git, for example a JSON file or Ansible `host_vars/`. **Git is the source of truth**, and devices should match it.

![NetDevOps pipeline](../assets/T28/03-netdevops-pipeline.png)
*Same shape as an app pipeline, but the "code" is network intent and "deploy" changes devices; red is the rollback path when post-change checks fail.*

- The infrastructure pipeline runs in five steps:
  1. **Lint and validate** the intent: JSON/YAML syntax, schema, and rules such as "VLAN IDs must be 1–4094 with no duplicates".
  2. **Test in simulation** by pushing the change to a virtual copy of the network in **Cisco Modeling Labs (CML)** and checking it with **pyATS** (pre-checks, `genie learn` and `diff`).
  3. **Review and approve** through a peer-reviewed merge request; the change window is the gate.
  4. **Deploy** with a tool that pushes config: **Ansible**, Cisco **NSO**, **Terraform**, or controller APIs over RESTCONF/NETCONF.
  5. **Post-change checks** such as a pyATS diff, ping, routing neighbours up and interfaces up. If they fail, **roll back** by redeploying the previous commit's intent.
- The benefits for infrastructure are consistency, an **audit trail** (`git log` shows who changed what, when and why), peer review, testing before prod, fewer outages and fast rollback.
- ⚠ verify: the stage list is the common NetDevOps pattern from Cisco DevNet material; the exact blueprint 5.4 wording should be checked in the PDF.
- **Exam-sim gap:** CI/CD for NSO (or any network change) only works if the pipeline is the **only** path to production. If engineers can still change devices by hand, the devices drift from Git and nothing is repeatable or auditable.
- **Exam-sim gap:** plan the work in a tracking system too. Changes start as tickets (for example **Jira**), each linked to the branch or MR that implements it, so ticket → branch → pipeline → deploy gives traceability. Cue: "what else does the setup need?" → issue tracking alongside Git and the CI server.

### 6. DevOps culture: CALMS and the Three Ways
- **DevOps** is a culture plus a set of practices that joins **development** (which wants change) and **operations** (which wants stability) into one team with shared goals, so change is fast and safe. It is not a job title or a tool.

| CALMS letter | Meaning | How it shows up in a scenario |
|---|---|---|
| **Culture** | Collaboration, shared ownership, no blame | Dev and ops in the same stand-up; blameless post-mortem |
| **Automation** | Automate build, test, deploy and infra | Pipelines, IaC |
| **Lean** | Small batches, limit work in progress, remove waste | Ship small MRs often |
| **Measurement** | Measure everything and decide with data | DORA metrics, dashboards |
| **Sharing** | Share knowledge, tools and responsibility | Shared runbooks, wikis, demos |

![The Three Ways](../assets/T28/04-three-ways.png)
*The 1st Way is work flowing left to right fast, the 2nd Way is information flowing right to left fast, and the 3rd Way is the whole loop improving.*

- **The Three Ways** (Gene Kim) come in a fixed order:
  1. **Flow:** optimise the whole dev-to-ops flow, not one silo, and never pass a known defect downstream.
  2. **Feedback:** get information back fast from failing tests, monitoring and alerts, and fix problems where they are found.
  3. **Continual learning and experimentation:** take risks, learn from failure and practise.
- **DORA metrics** (awareness): change lead time, deployment frequency, failed deployment recovery time and change fail rate (DORA now also lists deployment rework rate).
- **Exam-sim gap:** a learning culture means **continuous improvement**. Blameless post-mortems, sharing what broke and small experiments improve the process after each failure. Cue: "why does a learning culture matter?" → continuous improvement, not "fewer meetings" or "less testing".

### 7. DevOps practices to recognise
- **Automate everything repeatable:** if a task is done twice, script it.
- **Small batches, frequent releases:** a small change is easy to review, easy to roll back and has a smaller blast radius.
- **Shift-left:** move testing and security **earlier** in the lifecycle, into CI and onto the developer's laptop. "Run security scans only before the yearly audit" is the opposite.
- **Monitoring and fast feedback:** both the pipeline and production should tell you about problems within minutes.
- **Blameless post-mortem:** after an incident, ask "what in the system let this happen?", not "who did it?".
- **Shared responsibility,** or "**you build it, you run it**": the team that writes the code is on call for it.

## Exam traps (the ones that catch people)
- Looks like continuous deployment, but "manual approval before prod" is actually **continuous delivery**, because deployment has no human gate.
- Looks like CI deploys to prod, but CI actually ends at a tested artifact; only CD moves it to environments.
- Looks like you should rebuild for prod, but you actually **promote the same artifact**, because a rebuild is untested bytes.
- Looks like the artifact lives in Git, but the artifact repo (registry, Nexus, Artifactory) is actually separate; Git holds code and the pipeline file.
- Looks like GitHub Actions runs jobs in file order, but jobs actually run in **parallel** unless you add `needs:`.
- Looks like the L in CALMS is "Logging" and the M is "Monitoring", but they are actually **Lean** and **Measurement**.
- Looks like shift-left means handing work to ops, but it actually means testing and securing **earlier**.
- Looks like the device's running config is the truth in NetDevOps, but **Git** is actually the source of truth; a manual CLI change is drift the pipeline will overwrite.

## Quick self-check
<details><summary>Q1. A pipeline deploys every passing commit to prod with no human step. Delivery or deployment?</summary>Continuous deployment, because there is no approval gate.</details>
<details><summary>Q2. Which file name tells you the pipeline is GitHub Actions?</summary>`.github/workflows/*.yml`.</details>
<details><summary>Q3. Config was applied but BGP neighbours are down. Which stage catches this?</summary>The post-change check, which then triggers a rollback to the previous intent.</details>
<details><summary>Q4. Name the Three Ways in order.</summary>Flow, feedback, continual learning and experimentation.</details>
<details><summary>Q5. What is the best practice for CI/CD with NSO?</summary>Make the pipeline the only path to production, with no manual side doors.</details>

## Cheat lines to say out loud
- "CI ends at the artifact; CD moves the artifact."
- "Look for the human: approval means delivery, no human means deployment."
- "Build once, promote many."
- "In NetDevOps, Git is the truth and the pipeline is the only door to prod."
- "CALMS is Culture, Automation, Lean, Measurement, Sharing; the Three Ways are flow, feedback, learning."
