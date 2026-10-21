# T28 · CI/CD + DevOps principles: essentials

> Blueprint 4.4, 4.12, 5.4: components of a CI/CD pipeline (app deployment); principles of DevOps practices; CI/CD components and benefits for infrastructure automation · Full note: [bee/T28-ci-cd-devops-principles.md](../bee/T28-ci-cd-devops-principles.md) · Teach-back 2026-10-25

![T28 at a glance: CI, CD, pipeline components, NetDevOps and DevOps principles](../assets/T28/00-overview.png)

*The top row follows one commit left to right (Source → CI → Artifact → CD → Operate) with a red dashed feedback loop back; the bottom row covers NetDevOps, DevOps culture and tools, and red boxes are exam traps.*

## 🧭 The big idea

You already run pipelines for a living, so this topic is mostly the **exam's exact vocabulary**. It answers three questions:

| | Question | Answer options | Analogy |
|---|---|---|---|
| 🚦 | **Where does CI stop and CD start, and is there a human before prod?** | CI vs CD, delivery vs deployment | **a lorry at the gate.** Delivery = the lorry is loaded and waiting; a manager signs to open the gate. Deployment = the gate opens automatically when the checks pass. |
| 🏭 | **What are the parts of a pipeline, and in what order?** | source → build → test → artifact → deploy → monitor | **an assembly line with quality checkpoints.** Any failed check **stops the line**. The same finished product (the **artifact**) is what gets shipped to every store (environment). Nobody rebuilds the product at the last store. |
| 🤝 | **What do DevOps principles mean in a scenario?** | CALMS, the Three Ways, shift-left, blameless post-mortems | |

> 💡 The one genuinely new part is 🌐 **NetDevOps** (blueprint 5.4): network config treated like application code, with **Git as the source of truth** and a pipeline that tests changes in a simulated network before touching real devices.

- 🎯 **What the exam asks:** put stages in order, spot delivery vs deployment from the wording, name the benefit or DevOps principle a scenario describes, and pick the NetDevOps step (lint, simulate, deploy, post-check) that catches a problem.

## 🟥 Must know

### 1. 🔁 CI: merge small and often, and every push is built and tested

> 💡 **Continuous integration (CI)** = every developer merges small changes into the main branch **at least daily**, and **every push or merge request triggers an automated build that includes tests**.

| | |
|---|---|
| 🎯 Why it exists | to stop "integration hell" from long-lived branches. A bug is found minutes after the commit that caused it, by the person who wrote it, so main stays **green and releasable**. |
| 🛑 Fail fast | the first failing stage **stops the run**; later stages are **skipped**, not run "with warnings". A broken main build is fixed immediately or the commit is reverted. |
| 📦 Where it ends | **CI ends with a tested artifact.** It does not deploy to production. |
| ⚠️ Practice, not product | Running Jenkins on a branch nobody merges for a month is not CI. |

![CI vs CD boundary](../assets/T28/01-ci-cd-boundary.png)

*Blue is CI, which ends with a tested, packaged artifact; green is CD, which moves that artifact through environments; the yellow gate is the only difference between delivery and deployment.*

### 2. 🚦 CD: continuous delivery vs continuous deployment

> 💡 **CD** takes the **same artifact** CI produced and promotes it through **dev → staging → prod**. Both meanings abbreviate to "CD", so the exam spells them out. **Look for the human.**

| | 🧑‍💼 Continuous **delivery** | 🤖 Continuous **deployment** |
|---|---|---|
| Every change | built, tested and **releasable** (ready to deploy) | built, tested **and deployed** |
| Prod deploy | a **human approves** (button, approval). You **can** deploy any version on demand. | **automatic** when all stages pass. No human. Needs excellent tests, monitoring and fast rollback. |
| Lorry analogy | loaded and waiting for the manager's signature | the gate opens on its own |
| GitLab | `when: manual` on the prod job | remove that line |
| GitHub Actions | environment with **Required reviewers** | no protection rule |
| Jenkins | an `input` step in the prod stage | remove the `input` |
| Scenario words | "approval", "manual", "button", "business decides" | "automatically to production", "no human" |

**In a pipeline file**, the difference is one line (GitLab example from the full note):

```yaml
deploy-prod:
  stage: deploy
  needs: [deploy-staging, package]   # runs after staging, using the same packaged artifact
  script:
    - python3 ci/deploy.py --env prod --artifact dist/netinv.pyz --out .
  environment:
    name: prod
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual                   # continuous DELIVERY: a human clicks "play"
                                     # delete this line = continuous DEPLOYMENT
```

### 3. 📦 What is an artifact?

> 💡 **An artifact is the finished, packaged output of a build**: the file (or image) that actually gets deployed. Your **source code** is the recipe; the **artifact** is the cooked dish, boxed and labelled, ready to ship.

**Code vs artifact:**

| | 📚 Source code | 📦 Artifact |
|---|---|---|
| What it is | the files you write and edit | the **output** the build stage produces from them |
| Who makes it | a developer, by hand | the **pipeline**, automatically |
| Where it lives | **Git** (source repo) | an **artifact repository**: a registry (Docker Hub, ECR, Harbor) or Nexus / Artifactory |
| Changes? | every commit | **never**: once built, it's frozen. A new commit makes a **new** artifact. |
| Gets deployed? | ❌ no, not directly | ✅ **yes**: this is what dev, staging and prod receive |

**What an artifact looks like in practice:**

| Kind of project | Its artifact |
|---|---|
| 🐳 containerised app | a **container image**, e.g. pushed to ECR or Harbor (T27) |
| 🐍 Python tool (this note's lab) | a zipped Python app, `dist/netinv.pyz` |
| ☕ Java service | a `.jar` / `.war` file (`mvn package`) |

**🏭 Analogy, in pipeline order:**

1. 📚 **Source** = the recipe in the cookbook (Git).
2. 🔨 **Build** = cooking the dish **once** in the central kitchen.
3. 🧪 **Test** = the taste test. If it fails, nothing gets boxed.
4. 📦 **Artifact** = the dish, sealed in a labelled box (name + version) and put in the cold store (artifact repo).
5. 🚀 **Deploy** = delivering **that same sealed box** to the dev, staging and prod restaurants. Nobody re-cooks it on arrival.

**🔍 In the lab, step by step** (`labs/T28/.gitlab-ci.yml`, trimmed to the artifact lines):

```yaml
package:
  stage: build
  script:
    - mkdir -p dist
    - python3 -m zipapp src --main "build_inventory:main" --output dist/netinv.pyz   # ← BUILD: turn src/ into ONE file
  artifacts:                        # ← tell GitLab: save this file and hand it to later jobs
    paths:
      - dist/netinv.pyz             # ← the artifact itself
    expire_in: 1 week               # ← GitLab deletes the saved copy after a week
```

```yaml
deploy-dev:
  script:
    - python3 ci/deploy.py --env dev --artifact dist/netinv.pyz --out .       # ← deploy the SAME file
deploy-staging:
  script:
    - python3 ci/deploy.py --env staging --artifact dist/netinv.pyz --out .   # ← same file again
```

Real output from the local run of the same pipeline (`labs/T28/pipeline.sh`):

```
=== stage 3: build + package the artifact (once) ===
  artifact: dist/netinv.pyz (7041 bytes, built once, reused below)
  deployed dist/netinv.pyz -> envs/dev/netinv.pyz
  deployed dist/netinv.pyz -> envs/staging/netinv.pyz
```

- Built **once** in stage 3, then **copied unchanged** into each environment.
- If the unit tests fail, the `package` job never runs, so **there is no artifact** and nothing can be deployed.

**🏆 Why the exam cares: three rules all hang on the artifact:**

| | Rule | Why |
|---|---|---|
| 🔁 | **CI ends with a tested artifact; CD moves it.** | the artifact is the hand-over point between CI and CD |
| 🎯 | **Build once, promote the same artifact.** | the bytes tested in dev and staging are exactly the bytes in prod. Rebuilding for prod could pull different dependencies or code = **untested bytes in prod**. |
| ⏪ | **Rollback = redeploy the previous artifact.** | it's already built and tested, so rollback takes minutes, with no rebuild |

> 🎯 **Exam cue:** "Where are build outputs stored?" → **artifact repository** (registry, Nexus, Artifactory), **not** Git. Git holds the code and the pipeline file.

### 4. 🏭 Pipeline components and their order

**The parts, in the order a commit meets them:**

| | Component | Examples | Job |
|---|---|---|---|
| 📚 | **Source repo** | GitHub, GitLab, Bitbucket | the single source of truth for code **and** the pipeline file. A push or MR is the **trigger**. |
| 🏃 | **CI server and runner** | GitLab runner, Jenkins agent | reads the pipeline file and runs jobs in clean workers, often containers |
| 🧹 | **Lint / static checks** | pylint, yamllint, Bandit | the cheapest checks first: syntax, style, schema, security and secret scans |
| 🔨 | **Build** | `docker build` | compile or package, often into a container image |
| 🧪 | **Test** | pytest, pyATS | **unit** tests (one function, fast) run in CI on every push; **integration** tests (parts together) run against a **deployed** environment such as staging |
| 📦 | **Artifact repo** | ECR, Harbor, Nexus, Artifactory | stores the versioned build output so every environment gets **the same bytes**. This is **not** Git: Git holds code and the pipeline file. |
| 🚀 | **Deploy stages** | Ansible, Helm, Terraform | dev → staging → prod, with **gates** before prod |
| 📣 | **Notify and monitor** | Webex/Slack bot, Prometheus, Grafana | tells the committer, watches prod, and feeds back to the start |

> 🎯 **The order the exam wants:** source → build → test → store artifact → deploy dev → staging → (approval) → prod → monitor.
>
> Some diagrams merge lint into test, or put lint before build. Either way, **tests always come before any deploy**, and the **artifact is created before the deploy stages**.

> 📦 **Build once, promote many.** Assembly-line analogy: the same product goes to every store. If you rebuild for each environment, prod runs bytes nobody tested.

**🔍 Which stage catches what:**

| Problem | Caught by |
|---|---|
| a syntax error or a bad VLAN ID | 🧹 **lint** |
| a function returning the wrong value | 🧪 **unit test** |
| two services not talking | 🧪 **integration test** on staging |
| config applied but BGP down | ✅ **post-change check** |

**📜 Pipeline as code:** the pipeline definition lives in the **same repo** as the app, so it gets code review, history and an audit trail like any other code. Example (GitLab, from the full note, trimmed):

```yaml
stages:            # stages run in THIS order; jobs in the same stage run in parallel
  - lint
  - test
  - build
  - deploy

default:
  image: python:3.12-slim          # every job runs in a fresh container from this image

lint:
  stage: lint
  script:
    - python3 -m py_compile src/build_inventory.py src/netlib/*.py   # syntax check
    - python3 ci/validate_intent.py intent/vlans.json                 # validate the network intent

unit-test:
  stage: test
  script:
    - python3 -m unittest discover --start-directory tests            # unit tests; a failure stops the pipeline

package:
  stage: build
  script:
    - mkdir -p dist
    - python3 -m zipapp src --main "build_inventory:main" --output dist/netinv.pyz
  artifacts:                        # built ONCE, saved and passed to every deploy job
    paths:
      - dist/netinv.pyz
```

- Read it like the exam: order lint → test → build → deploy; a failed `unit-test` means nothing is packaged or deployed.

![Pipeline components](../assets/T28/02-pipeline-components.png)

*Purple is stored in a repo, blue is the CI stages, green is the environments and monitoring, and the dotted line is the feedback loop.*

![Animated pipeline run](../assets/T28/05-pipeline-run.gif)

*Push → lint → test → package once → dev → staging → prod waits for approval; the next commit fails a test and every later stage is skipped.*

### 5. 🏆 Benefits: match the scenario wording

> 💡 Each benefit follows from a mechanism above.

| | Mechanism | Benefit | Scenario wording |
|---|---|---|---|
| ⚡ | small changes merged often | **faster, smaller, more frequent releases** (smaller blast radius) | "release weekly instead of quarterly", "small changes" |
| 🤖 | scripted steps instead of a runbook | **fewer manual errors, repeatable deploys** | "no more copy-paste deploy runbook" |
| 🐞 | every push tested | **early defect detection**, which is cheaper to fix | "the bug was found 5 minutes after the commit" |
| ⏪ | every artifact kept | **quick rollback** by redeploying the **previous artifact** (already built and tested) | "the bad release was undone in 2 minutes" |
| 👀 | pipeline status per commit | **visibility and feedback** | "everyone sees which commit broke it" |

### 6. 🌐 CI/CD for the network (NetDevOps, blueprint 5.4)

| ❌ The old way | ✅ NetDevOps |
|---|---|
| An engineer SSHes into each device and types config. No review, no test, devices drift apart, and the only record of the change is the device itself. | CI/CD applied to the network. The desired state, called **intent** (VLANs, interfaces, BGP neighbours, ACLs), is stored as **data in Git**, e.g. a JSON file or Ansible `host_vars/`. **Git is the source of truth**; devices should match it. A manual CLI change is **drift** the pipeline will overwrite. |

> 🏭 Assembly-line analogy: the intent file is the product spec; the pipeline checks the spec, builds a test copy, and only then changes the real network.

**The five steps of an infrastructure pipeline:**

1. 🧹 **Lint and validate** the intent: JSON/YAML syntax, schema, and rules such as "VLAN IDs must be 1–4094 with no duplicates".
2. 🧪 **Test in simulation:** push the change to a virtual copy of the network in **Cisco Modeling Labs (CML)** and check it with **pyATS** (pre-checks, `genie learn` and `diff`).
3. 👥 **Review and approve:** a peer-reviewed merge request; the change window is the gate.
4. 🚀 **Deploy** with a tool that pushes config: **Ansible**, Cisco **NSO**, **Terraform**, or controller APIs over RESTCONF/NETCONF.
5. ✅ **Post-change checks:** pyATS diff, ping, routing neighbours up, interfaces up. If they fail, **roll back** by redeploying the previous commit's intent.

- ⚠ verify: the stage list is the common NetDevOps pattern from Cisco DevNet material; check the exact blueprint 5.4 wording in the PDF.

**Example: the lint stage rejecting bad intent** (real output from the full note):

```text
=== stage 1: lint / validate (source + network intent) ===
  OK syntax: build_inventory.py netlib/
  FAIL /tmp/claude-501/bad-vlans.json: VLAN 4095 out of range 1-4094      ← rule check
  FAIL /tmp/claude-501/bad-vlans.json: VLAN 10 has no name
  FAIL /tmp/claude-501/bad-vlans.json: duplicate VLAN IDs in [10, 4095, 10]

PIPELINE FAILED in stage lint: later stages did not run                    ← fail fast: nothing built or deployed
```

**🏆 Benefits for infrastructure:** consistency (every device from the same template), an **audit trail** (`git log` shows who changed what, when and why), peer review, testing before prod, **fewer outages**, fast rollback.

> 🔐 **Exam-sim gap: one door to prod.** CI/CD for NSO (or any network change) only works if the pipeline is the **only** path to production. If engineers can still change devices by hand, the devices drift from Git and nothing is repeatable or auditable.
>
> 🎯 Cue: "best practice for CI/CD with NSO" → single pipeline to prod, no manual side doors.

> 🔐 **Exam-sim gap: plan the work in a tracking system too.** Changes start as tickets (for example **Jira**), each linked to the branch or MR that implements it, so ticket → branch → pipeline → deploy gives traceability.
>
> 🎯 Cue: "what else does the setup need?" → issue tracking alongside Git and the CI server.

![NetDevOps pipeline](../assets/T28/03-netdevops-pipeline.png)

*Same shape as an app pipeline, but the "code" is network intent and "deploy" changes devices; red is the rollback path when post-change checks fail.*

### 7. 🤝 DevOps principles: CALMS, the Three Ways and the practices (blueprint 4.12)

> 💡 **DevOps** = a culture plus a set of practices that joins **development** (which wants change) and **operations** (which wants stability) into one team with shared goals, so change is fast **and** safe. It is not a job title or a tool: "buy Jenkins" ≠ DevOps.

**🧩 CALMS** (Jez Humble), one letter per pillar:

| | CALMS | Means | Spot it (scenario) |
|---|---|---|---|
| 🫂 | **C**ulture | collaboration, shared ownership, no blame | dev and ops in the same stand-up; a blameless post-mortem |
| 🤖 | **A**utomation | automate build, test, deploy and infra | pipelines, IaC |
| 🪶 | **L**ean | small batches, limit work in progress (WIP), remove waste | ship small MRs often. (Not "Logging".) |
| 📊 | **M**easurement | measure everything, decide with data | dashboards, DORA metrics. (Not "Monitoring"; monitoring is one way to measure.) |
| 📖 | **S**haring | share knowledge, tools and responsibility | shared runbooks, wikis, demos |

**🛤️ The Three Ways** (Gene Kim), in a fixed order. Assembly-line analogy:

| | Way | Means | Assembly line |
|---|---|---|---|
| 1️⃣ | **Flow** | optimise the **whole** dev-to-ops flow, not one silo, and never pass a known defect downstream | the line moves fast left to right |
| 2️⃣ | **Feedback** | failing tests, monitoring, alerts; fix them where they are found | problems travel back right to left fast |
| 3️⃣ | **Continual learning and experimentation** | take risks, learn from failure, practise | the whole line keeps improving |

> 🔐 **Exam-sim gap:** a learning culture means **continuous improvement**. Blameless post-mortems, sharing what broke and small experiments improve the process after each failure.
>
> 🎯 Cue: "why does a learning culture matter?" → continuous improvement, not "fewer meetings" or "less testing".

**The practices to recognise:**

| | Practice | Means |
|---|---|---|
| 🤖 | **Automate everything repeatable** | if a task is done twice, script it |
| 🪶 | **Small batches, frequent releases** | easy to review, easy to roll back, smaller blast radius |
| ⬅️ | **Shift-left** | move testing and security **earlier** in the lifecycle (into CI and onto the developer's laptop). "Run security scans only before the yearly audit" is the opposite. Not "hand it to ops". |
| 📣 | **Monitoring and fast feedback** | the pipeline and production both report problems within minutes |
| 🫂 | **Blameless post-mortem** | after an incident, ask "what in the system let this happen?", not "who did it?" |
| 🔧 | **Shared responsibility, "you build it, you run it"** | the team that writes the code is on call for it |

![The Three Ways](../assets/T28/04-three-ways.png)

*The 1st Way is work flowing left to right fast, the 2nd Way is information flowing right to left fast, and the 3rd Way is the whole loop improving.*

## ⚠️ Exam traps

| ❌ Looks like… | ✅ Actually… |
|---|---|
| 🚦 "Manual approval before prod" is continuous deployment; CI deploys to prod | **Continuous delivery.** Deployment has no human gate. CI alone never deploys to prod; it ends at a tested artifact. |
| 📦 Rebuild for each environment; the artifact lives in Git | **Build once, promote the same artifact.** Rebuilding for prod = untested bytes. The artifact repo (registry, Nexus, Artifactory) is separate from Git. |
| 🏭 Deploy, then test; a failed stage runs the rest "with warnings" | **Order: build → test → deploy.** Unit tests before any deploy; integration tests on staging; monitoring after prod. A failed stage **skips** everything after it. |
| 🤝 CALMS L = Logging, M = Monitoring; shift-left = hand it to ops | **L = Lean, M = Measurement.** Three Ways order: Flow, Feedback, Continual learning. Shift-left = test and secure **earlier**. |
| 🌐 NetDevOps still allows manual device changes | **Git is the source of truth**, the pipeline is the **only** path to prod (no manual side doors), and work starts as a tracked ticket (Jira). |

<details><summary><b>🟨 Should know (second pass)</b></summary>

### 🛠️ Pipeline tools (awareness)

> 💡 Match the file name to the tool, and read the stage order from a snippet.

| | 🦊 GitLab CI | 🐙 GitHub Actions | 🤵 Jenkins |
|---|---|---|---|
| File | `.gitlab-ci.yml` at the repo **root** | `.github/workflows/*.yml` | `Jenkinsfile` (Groovy) |
| Order | a `stages:` list sets the order; jobs in the same stage run in **parallel** and the next stage waits | **all jobs run in parallel** unless ordered with `needs:` (they do **not** run in file order) | stages run in sequence |
| Runs on | the `image:` on a runner | `runs-on: ubuntu-latest` | an `agent` |
| Manual gate | `when: manual` | environment with Required reviewers | an `input` step |
| Extra | default stages if none are defined: `.pre`, `build`, `test`, `deploy`, `.post` | | |

- "Pipeline as code" means the pipeline is versioned in the **app's** repo, not "the pipeline is written in Python".

### 🧪 Where each kind of test runs

| Test | Runs |
|---|---|
| lint and unit tests | in **CI** on every push (seconds) |
| integration / end-to-end tests | against a **deployed** env (staging) |
| smoke / post-deploy checks | right after each deploy |

- Example from the full note: a change passed every unit test, then the **post-deploy check failed in dev**, so it never reached staging or prod. That's why each environment has its own checks.

### 📊 DORA metrics (the "Measurement" in CALMS)

- Change lead time, deployment frequency, failed deployment recovery time and change fail rate (DORA now also lists deployment rework rate).

### 🚦 Delivery vs deployment wording (Fowler)

| 🧑‍💼 Delivery | 🤖 Deployment |
|---|---|
| you **can** deploy any version on demand ("push-button") | every change **does** go to production |

</details>

> 📚 **Recognise only, details in the full note:** GitLab `when: manual` inside `rules:` vs job level (`allow_failure`), GitLab deployment tiers, passing files between jobs (`upload-artifact`, `stash`, `archiveArtifacts`), declarative vs scripted Jenkinsfile, `workflow: rules:` trigger syntax, the deployment rework rate metric.

## ✍️ Quick self-check
<details><summary>Q1. A pipeline deploys every passing commit to prod with no human step. Delivery or deployment?</summary>Continuous deployment, because there is no approval gate.</details>
<details><summary>Q2. Which file name tells you the pipeline is GitHub Actions?</summary><code>.github/workflows/*.yml</code>.</details>
<details><summary>Q3. Config was applied but BGP neighbours are down. Which stage catches this?</summary>The post-change check, which then triggers a rollback to the previous intent.</details>
<details><summary>Q4. Name the Three Ways in order.</summary>Flow, feedback, continual learning and experimentation.</details>
<details><summary>Q5. What is the best practice for CI/CD with NSO?</summary>Make the pipeline the only path to production, with no manual side doors.</details>
<details><summary>Q6. <code>stages: [build, test, deploy]</code>; jobs <code>unit</code> and <code>lint</code> are both in <code>test</code>, and <code>prod</code> has no <code>when: manual</code>. What runs in parallel, and what if <code>unit</code> fails?</summary><code>unit</code> and <code>lint</code> run in parallel (same stage). If <code>unit</code> fails, the test stage fails and <code>prod</code> doesn't run. With no manual gate, passing commits go straight to prod: continuous deployment.</details>
<details><summary>Q7. A release is bad. What is the fastest CI/CD rollback?</summary>Redeploy the previous artifact, which is already built and tested. Don't rebuild.</details>

## 🗣️ Say it out loud
- 🔁📦 "CI ends at the artifact; CD moves the artifact."
- 🚦 "Look for the human: approval means delivery, no human means deployment."
- 🏭 "Build once, promote many."
- 🌐 "In NetDevOps, Git is the truth and the pipeline is the only door to prod."
- 🤝 "CALMS is Culture, Automation, Lean, Measurement, Sharing; the Three Ways are flow, feedback, learning."
