---
id: T28
title: "CI/CD + DevOps principles"
owner: Beedy
blueprint: "4.4, 4.12, 5.4"
primary_domain: D4
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-13
teach_back: 2026-10-16
cross_study: 2026-10-22
---

# T28 · CI/CD + DevOps principles

> Owner: **Beedy** · Blueprint: **4.4, 4.12, 5.4** · CBT coverage: **Full** · Learn by 2026-10-13 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T28.01 · CI

**Must cover:**

- [ ] Developers merge to the main branch frequently (at least daily)
- [ ] Each push triggers an automated build and tests
- [ ] Catches integration bugs early, keeps main releasable

**Notes:**

<!-- TODO -->

### T28.02 · CD

**Must cover:**

- [ ] Continuous delivery: every change is releasable; production deploy needs a manual approval
- [ ] Continuous deployment: every passing change goes to production automatically

**Notes:**

<!-- TODO -->

### T28.03 · Pipeline components

**Must cover:**

- [ ] Source control repo (trigger on commit/PR)
- [ ] Build (compile, package, container image)
- [ ] Test: unit, integration, security/lint
- [ ] Artifact repository (image registry, Nexus/Artifactory)
- [ ] Deploy stages: dev → test/staging → production, with approvals/gates
- [ ] Notifications and monitoring/feedback

**Notes:**

<!-- TODO -->

### T28.04 · Tools (awareness)

**Must cover:**

- [ ] Jenkins (Jenkinsfile), GitLab CI (.gitlab-ci.yml), GitHub Actions (workflows YAML)
- [ ] Pipeline as code: pipeline definition version-controlled with the app

**Notes:**

<!-- TODO -->

### T28.05 · Benefits

**Must cover:**

- [ ] Faster, smaller, more frequent releases
- [ ] Fewer manual errors; repeatable deploys
- [ ] Early defect detection; quick rollback

**Notes:**

<!-- TODO -->

### T28.06 · Infra CI/CD

**Must cover:**

- [ ] Network config/intent stored in Git (source of truth)
- [ ] Pipeline: lint/validate → test in simulation (CML, pyATS) → deploy (Ansible, NSO, Terraform) → post-change checks
- [ ] Same benefits for infrastructure: consistency, audit trail, fewer outages

**Notes:**

<!-- TODO -->

### T28.07 · DevOps

**Must cover:**

- [ ] DevOps = culture + practices that join development and operations
- [ ] CALMS: Culture, Automation, Lean, Measurement, Sharing
- [ ] Three Ways: flow (fast left-to-right), feedback (right-to-left), continual learning/experimentation

**Notes:**

<!-- TODO -->

### T28.08 · DevOps practices

**Must cover:**

- [ ] Automate everything repeatable
- [ ] Small batch sizes, frequent releases
- [ ] Shift-left: test and secure early
- [ ] Monitoring and fast feedback; blameless post-mortems
- [ ] Shared responsibility ("you build it, you run it")

**Notes:**

<!-- TODO -->

### T28.09 · Exam angle

**Must cover:**

- [ ] Put pipeline stages in the correct order
- [ ] Pick the benefit or DevOps principle a scenario describes
- [ ] Delivery vs deployment distinction

**Notes:**

<!-- TODO -->

## Exam traps

<!-- Easily confused pairs, exact syntax, scenario → answer mappings. -->

## Examples

<!-- Full, runnable commands/code. No partial commands. -->

## Practice questions

<!-- 5-8 exam-style Qs. Answers in <details>. -->

## Study aids

- Practice Qs only (known topic or no dedicated aid).

- Skip / low priority: Whole video

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
