"""T43 webhook receiver: YOUR app, the HTTP server the platform calls (Python stdlib only).

Run:  python3 -u labs/T43/receiver.py          -> http://127.0.0.1:8144/webhook
1. read the raw body   2. verify X-Spark-Signature (HMAC-SHA1, shared secret)
3. drop duplicates      4. answer 200 at once   5. work in the background:
   follow-up GET /v1/messages/{id} for the text, then act on it.
Knobs for the break-it runs (env vars): WEBHOOK_SECRET, FAIL_FIRST, INLINE_WORK_SECONDS.
"""
import hashlib
import hmac
import json
import os
import queue
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", 8144
PLATFORM = os.environ.get("PLATFORM_API", "http://127.0.0.1:8143/v1")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "bot-token-T43")
SECRET = os.environ.get("WEBHOOK_SECRET", "s3cr3t-T43-demo").encode()   # must equal the secret you registered
FAIL_FIRST = int(os.environ.get("FAIL_FIRST", "0"))                      # break-it: answer 500 to the first N POSTs
INLINE_WORK = float(os.environ.get("INLINE_WORK_SECONDS", "0"))          # break-it: slow work BEFORE replying

lock = threading.Lock()
seen = set()                    # data.id values already accepted (idempotency)
jobs = queue.Queue()
posts = {"count": 0}


def log(text):
    print(f"[receiver] {text}", flush=True)


def signature_ok(raw_body, received):
    expected = hmac.new(SECRET, raw_body, hashlib.sha1).hexdigest()
    return hmac.compare_digest(expected, received or "")


def fetch_message(msg_id):
    """The webhook carried IDs only, so ask the API for the full message (with the bot's token)."""
    request = urllib.request.Request(f"{PLATFORM}/messages/{msg_id}",
                                     headers={"Authorization": f"Bearer {BOT_TOKEN}"})
    with urllib.request.urlopen(request, timeout=5) as reply:
        return json.load(reply)


def act(event):
    msg = fetch_message(event["data"]["id"])
    log(f"  follow-up GET /v1/messages/{msg['id']} -> text={msg['text']!r}")
    if msg["text"].lower().startswith("show"):
        log(f"  ACTION: run '{msg['text']}' and post the result back to {msg['roomId']}")
    else:
        log("  ACTION: none (not a command)")


def worker():
    while True:
        event = jobs.get()
        try:
            act(event)
        except Exception as err:                       # keep the worker alive
            log(f"  follow-up GET for {event['data']['id']} failed: {err}")
        jobs.task_done()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def reply(self, code, text):
        data = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except BrokenPipeError:                        # the platform's delivery timeout already fired
            log(f"  reply {code} never arrived: the platform had already hung up")

    def do_POST(self):
        if self.path != "/webhook":
            return self.reply(404, "not found")
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))       # 1. raw bytes
        with lock:
            posts["count"] += 1
            count = posts["count"]
        if count <= FAIL_FIRST:
            log(f"POST /webhook #{count}: simulated crash -> 500")
            return self.reply(500, "internal error")
        if not signature_ok(raw, self.headers.get("X-Spark-Signature")):         # 2. verify BEFORE parsing
            log(f"POST /webhook #{count}: signature mismatch -> 401, payload ignored")
            return self.reply(401, "bad signature")
        event = json.loads(raw)
        if event.get("resource") != "messages" or "id" not in event.get("data", {}):  # validate the shape
            log(f"POST /webhook #{count}: unexpected payload -> 400")
            return self.reply(400, "unexpected payload")
        msg_id = event["data"]["id"]
        with lock:
            duplicate = msg_id in seen
            seen.add(msg_id)
        if duplicate:                                                            # 3. idempotency
            log(f"POST /webhook #{count}: {msg_id} already handled (retry) -> 200, no second action")
            return self.reply(200, "duplicate")
        log(f"POST /webhook #{count}: signature OK, {event['resource']}/{event['event']} "
            f"data.id={msg_id} from {event['data']['personEmail']}")
        if INLINE_WORK:                                                          # the anti-pattern
            log(f"  doing {INLINE_WORK}s of work BEFORE replying (anti-pattern)")
            time.sleep(INLINE_WORK)
        jobs.put(event)                                                          # 5. hand off
        return self.reply(200, "ok")                                             # 4. ack fast


if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    log(f"listening on http://{HOST}:{PORT}/webhook")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
