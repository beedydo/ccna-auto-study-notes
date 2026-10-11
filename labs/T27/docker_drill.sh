#!/usr/bin/env bash
# T27 Docker drill: build the mock-API image, then exercise run / ps / logs / exec / inspect,
# port mapping, env vars, CMD vs ENTRYPOINT, bind mount vs named volume, stop vs rm, clean up.
# Run from the repo root:  bash labs/T27/docker_drill.sh
# Only host port 8127 is published. Everything it creates is prefixed t27- and removed at the end.
set -u
LAB="$(cd "$(dirname "$0")" && pwd)"
VIEWER="Authorization: Bearer tok-viewer-91c2"
ADMIN="Authorization: Bearer tok-admin-7f3a"
step() { printf '\n== %s ==\n' "$1"; }
wait_up() {   # wait_up <container> <port>: poll from INSIDE the container until the API answers
  for _ in $(seq 1 40); do
    docker exec "$1" curl --silent --output /dev/null "http://127.0.0.1:$2/api/v1/devices" && return 0
    sleep 0.25
  done
  echo "$1 did not come up on port $2"
}

step "1. Build the image (build context = labs/T27)"
docker build --quiet --tag t27-mock-api:1.0 "$LAB" > /dev/null
docker tag t27-mock-api:1.0 t27-mock-api:latest
docker images t27-mock-api --format '{{.Repository}}:{{.Tag}}  {{.ID}}'

step "2. Run detached, publish host 8127 -> container 8080"
docker run --detach --name t27-api --publish 8127:8080 t27-mock-api:1.0 > /dev/null
wait_up t27-api 8080
docker ps --filter name=t27-api --format '{{.Names}}  {{.Image}}  {{.Ports}}'
curl --silent --header "$VIEWER" "http://127.0.0.1:8127/api/v1/devices/1"; echo

step "3. Logs (stdout/stderr of PID 1)"
docker logs t27-api

step "4. Exec a command in the running container"
docker exec t27-api whoami
docker exec t27-api pwd
docker exec t27-api printenv API_PORT ACCESS_LOG

step "5. Inspect (JSON) with a Go template"
docker inspect --format '{{.Config.Entrypoint}} {{.Config.Cmd}} {{.Config.User}} {{.Config.ExposedPorts}}' t27-api
docker inspect --format '{{json .NetworkSettings.Ports}}' t27-api

step "6. Args after the image REPLACE CMD and are APPENDED to ENTRYPOINT"
docker run --rm t27-mock-api:1.0 --help | head -n 1
docker run --rm --entrypoint python3 t27-mock-api:1.0 --version

step "7. --env overrides ENV; EXPOSE alone publishes nothing"
docker run --detach --name t27-env --env API_PORT=9000 t27-mock-api:1.0 > /dev/null
wait_up t27-env 9000
docker logs t27-env | head -n 1
docker ps --filter name=t27-env --format '{{.Names}}  ports: {{.Ports}}'

step "8a. Bind mount: host folder labs/T27/seed, read-only"
docker run --detach --name t27-bind --env DEVICES_FILE=/data/devices.json \
  --volume "$LAB/seed":/data:ro t27-mock-api:1.0 > /dev/null
wait_up t27-bind 8080
docker exec t27-bind curl --silent --header "$VIEWER" "http://127.0.0.1:8080/api/v1/devices"; echo

step "8b. Named volume: survives docker rm"
docker volume create t27-data > /dev/null
docker run --detach --name t27-vol --env DEVICES_FILE=/data/devices.json \
  --volume t27-data:/data t27-mock-api:1.0 > /dev/null
wait_up t27-vol 8080
docker exec t27-vol curl --silent --output /dev/null --write-out 'DELETE /devices/3 -> %{http_code}\n' \
  --request DELETE --header "$ADMIN" "http://127.0.0.1:8080/api/v1/devices/3"
docker stop t27-vol > /dev/null
docker rm t27-vol > /dev/null
docker volume ls --filter name=t27-data --format 'volume still here: {{.Name}}'
docker run --detach --name t27-vol2 --env DEVICES_FILE=/data/devices.json \
  --volume t27-data:/data t27-mock-api:1.0 > /dev/null
wait_up t27-vol2 8080
docker logs t27-vol2 | head -n 1
docker exec t27-vol2 curl --silent --header "$VIEWER" "http://127.0.0.1:8080/api/v1/devices" \
  | python3 -c 'import json,sys; print("hostnames:", [d["hostname"] for d in json.load(sys.stdin)["response"]])'

step "9. Stop keeps the container, rm deletes it"
docker stop t27-api > /dev/null
docker ps --all --filter name=t27-api --format '{{.Names}}  {{.Status}}'
docker start t27-api > /dev/null
docker ps --filter name=t27-api --format '{{.Names}}  {{.Status}}'

step "10. Clean up"
docker rm --force t27-api t27-env t27-bind t27-vol2 > /dev/null
docker volume rm t27-data > /dev/null
docker rmi t27-mock-api:1.0 t27-mock-api:latest > /dev/null
echo "t27 containers left: $(docker ps --all --quiet --filter name=t27- | wc -l | tr -d ' ')"
