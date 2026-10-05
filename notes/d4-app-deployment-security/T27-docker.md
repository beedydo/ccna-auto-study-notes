---
id: T27
title: "Docker"
owner: Beedy
blueprint: "4.3, 4.6, 4.7"
primary_domain: D4
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-13
teach_back: 2026-10-16
cross_study: 2026-10-22
---

# T27 · Docker

> Owner: **Beedy** · Blueprint: **4.3, 4.6, 4.7** · CBT coverage: **Full** · Learn by 2026-10-13 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T27.01 · Concepts

**Must cover:**

- [ ] Image: read-only template made of layers
- [ ] Container: running instance of an image (adds a writable layer)
- [ ] Registry: stores images (Docker Hub, private registries); repo:tag naming (python:3.12-slim)
- [ ] Docker Engine/daemon builds and runs containers

**Notes:**

<!-- TODO -->

### T27.02 · Dockerfile

**Must cover:**

- [ ] FROM base image (first instruction)
- [ ] RUN executes a command at build time (new layer)
- [ ] COPY src dest copies local files; ADD can also fetch URLs and unpack tar files
- [ ] WORKDIR sets the working directory; ENV sets environment variables; ARG = build-time variable
- [ ] EXPOSE documents the listening port (does not publish it)
- [ ] USER sets the run-as user; LABEL adds metadata
- [ ] CMD default command/args at run time; ENTRYPOINT fixed executable

**Notes:**

<!-- TODO -->

### T27.03 · Dockerfile

**Must cover:**

- [ ] RUN = build time; CMD/ENTRYPOINT = when the container starts
- [ ] Only the last CMD counts; docker run args override CMD but are appended to ENTRYPOINT
- [ ] Order instructions from least to most frequently changing to use layer cache

**Notes:**

<!-- TODO -->

### T27.04 · Commands

**Must cover:**

- [ ] docker build -t myapp:1.0 . (dot = build context)
- [ ] docker images; docker pull nginx; docker push repo/myapp:1.0
- [ ] docker rmi <image>; docker tag

**Notes:**

<!-- TODO -->

### T27.05 · Commands

**Must cover:**

- [ ] docker run -d (detached) -it (interactive terminal) --name web --rm
- [ ] -p 8080:80 = host port 8080 → container port 80
- [ ] -v /host/path:/container/path or -v volname:/path
- [ ] -e KEY=value
- [ ] docker ps (running), docker ps -a (all); docker stop / start / rm

**Notes:**

<!-- TODO -->

### T27.06 · Commands

**Must cover:**

- [ ] docker exec -it <container> /bin/bash (shell inside)
- [ ] docker logs <container> (-f to follow)
- [ ] docker inspect <container> (JSON details)

**Notes:**

<!-- TODO -->

### T27.07 · Networking/storage

**Must cover:**

- [ ] -p host:container (host side first)
- [ ] Bind mount (host path) vs named volume (managed by Docker)
- [ ] Default bridge network; --network host shares the host network

**Notes:**

<!-- TODO -->

### T27.08 · Local dev

**Must cover:**

- [ ] Same environment for every developer (no "works on my machine")
- [ ] Run dependencies (DB, test tools) locally in containers
- [ ] docker compose: multi-container apps defined in YAML (awareness)

**Notes:**

<!-- TODO -->

### T27.09 · Exam angle

**Must cover:**

- [ ] Read a Dockerfile: base image, what is installed, which port, what runs
- [ ] Pick the command for a task (run detached with port mapping, open a shell)

**Notes:**

<!-- TODO -->

## Exam traps

<!-- Easily confused pairs, exact syntax, scenario → answer mappings. -->

## Examples

<!-- Full, runnable commands/code. No partial commands. -->

## Practice questions

<!-- 5-8 exam-style Qs. Answers in <details>. -->

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T27.1 | Video | Containerize Your App with a Dockerfile (2x) | 5 | CBT: Understand the Basics of Docker |

- Skip / low priority: Whole video

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
