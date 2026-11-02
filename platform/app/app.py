#!/usr/bin/env python3
"""CloudOps lab application.

Deliberately small, dependency-light and easy to break:
  /              instance identity
  /health        liveness (ALB health check)
  /ready         readiness + DB check
  /db            PostgreSQL connectivity check via Secrets Manager
  /error         500 + ERROR log (metric filter / alarm labs)
  /log           emit a log line with a chosen level
  /load          spawn CPU workers (CPU alarm / ASG labs)
  /stop          stop CPU workers
  /slow          sleep, to trigger ALB target response time alarms
  /config        non-secret runtime configuration

Logs are JSON lines in /var/log/cloudops/app.log so CloudWatch Logs Insights
and metric filters can query `level`, `event`, `path`, `instance_id`.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get("PORT", "8080"))
DB_HOST = os.environ.get("DB_HOST", "")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "cloudops")
DB_USER = os.environ.get("DB_USER", "cloudops")
DB_SECRET_ARN = os.environ.get("DB_SECRET_ARN", "")
LOG_GROUP = os.environ.get("LOG_GROUP", "")
AWS_REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", ""))
LOG_FILE = os.environ.get("LOG_FILE", "/var/log/cloudops/app.log")

LOAD_LOCK = threading.Lock()
LOAD_PROCS: list[subprocess.Popen] = []
LOAD_TIMER: threading.Timer | None = None
SECRET_CACHE: dict[str, object] = {"value": None, "expires": 0.0}


def imds(path: str, default: str = "unknown") -> str:
    """IMDSv2-only metadata read. The launch template requires tokens."""
    try:
        token_req = urllib.request.Request(
            "http://169.254.169.254/latest/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
        )
        with urllib.request.urlopen(token_req, timeout=1) as resp:
            token = resp.read().decode()
        req = urllib.request.Request(
            f"http://169.254.169.254/latest/meta-data/{path}",
            headers={"X-aws-ec2-metadata-token": token},
        )
        with urllib.request.urlopen(req, timeout=1) as resp:
            return resp.read().decode()
    except Exception:
        return default


INSTANCE_ID = imds("instance-id", socket.gethostname())
AVAILABILITY_ZONE = imds("placement/availability-zone")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "instance_id": INSTANCE_ID,
        }
        for key in ("event", "path", "status", "duration_ms", "error_type"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def build_logger() -> logging.Logger:
    logger = logging.getLogger("cloudops")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = JsonFormatter()

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=1)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


LOG = build_logger()


def get_db_secret() -> dict:
    """Fetch and cache the RDS managed master secret."""
    now = time.time()
    if SECRET_CACHE["value"] and now < float(SECRET_CACHE["expires"]):
        return SECRET_CACHE["value"]  # type: ignore[return-value]

    if not DB_SECRET_ARN:
        raise RuntimeError("DB_SECRET_ARN is not set")

    import boto3  # imported lazily so /health works during boot

    client = boto3.client("secretsmanager", region_name=AWS_REGION or None)
    raw = client.get_secret_value(SecretId=DB_SECRET_ARN)["SecretString"]
    value = json.loads(raw)
    SECRET_CACHE["value"] = value
    SECRET_CACHE["expires"] = now + 300
    return value


def db_check() -> tuple[bool, str]:
    try:
        import pg8000.native

        secret = get_db_secret()
        user = secret.get("username") or DB_USER
        password = secret.get("password")
        host = secret.get("host") or DB_HOST
        port = int(secret.get("port") or DB_PORT)
        database = secret.get("dbname") or DB_NAME
        if not password:
            raise RuntimeError("password missing from secret")

        conn = pg8000.native.Connection(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
            timeout=3,
        )
        try:
            value = conn.run("SELECT 1")
        finally:
            conn.close()
        return True, f"select_1={value}"
    except Exception as exc:  # noqa: BLE001 - lab wants the error class
        LOG.error(
            "database check failed",
            extra={"event": "db_check_failed", "error_type": type(exc).__name__},
        )
        return False, f"{type(exc).__name__}: {exc}"


def start_load(seconds: int, workers: int) -> int:
    global LOAD_TIMER
    stop_load()
    workers = max(1, min(workers, 4))
    with LOAD_LOCK:
        for _ in range(workers):
            LOAD_PROCS.append(
                subprocess.Popen(
                    [sys.executable, "-c", "while True: pass"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            )
    if seconds > 0:
        LOAD_TIMER = threading.Timer(seconds, stop_load)
        LOAD_TIMER.daemon = True
        LOAD_TIMER.start()
    LOG.info(
        "cpu load started",
        extra={"event": "load_started", "status": f"workers={workers},seconds={seconds}"},
    )
    return workers


def stop_load() -> int:
    global LOAD_TIMER
    if LOAD_TIMER:
        LOAD_TIMER.cancel()
        LOAD_TIMER = None
    stopped = 0
    with LOAD_LOCK:
        for proc in LOAD_PROCS:
            if proc.poll() is None:
                proc.terminate()
                stopped += 1
        LOAD_PROCS.clear()
    if stopped:
        LOG.info("cpu load stopped", extra={"event": "load_stopped", "status": stopped})
    return stopped


class Handler(BaseHTTPRequestHandler):
    server_version = "CloudOpsLab/1.0"

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        # Keep the access log in the same JSON format.
        LOG.info(
            fmt % args,
            extra={"event": "access", "path": self.path, "status": "-"},
        )

    def _send(self, status: int, payload: dict | str) -> None:
        body = payload if isinstance(payload, str) else json.dumps(payload)
        raw = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        started = time.time()
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        try:
            if path == "/":
                self._send(
                    200,
                    {
                        "service": "cloudops-lab-app",
                        "instance_id": INSTANCE_ID,
                        "az": AVAILABILITY_ZONE,
                        "message": "Break me. That is the point.",
                    },
                )
            elif path == "/health":
                self._send(200, {"status": "ok", "instance_id": INSTANCE_ID})
            elif path == "/ready":
                ok, detail = db_check()
                self._send(200 if ok else 503, {"ready": ok, "db": detail})
            elif path == "/db":
                ok, detail = db_check()
                self._send(200 if ok else 503, {"db": ok, "detail": detail})
            elif path == "/config":
                self._send(
                    200,
                    {
                        "port": PORT,
                        "db_host": DB_HOST,
                        "db_port": DB_PORT,
                        "db_name": DB_NAME,
                        "region": AWS_REGION,
                        "log_group": LOG_GROUP,
                        "instance_id": INSTANCE_ID,
                    },
                )
            elif path == "/error":
                LOG.error(
                    "simulated application failure",
                    extra={"event": "simulated_error", "path": path, "status": 500},
                )
                self._send(500, {"error": "simulated", "instance_id": INSTANCE_ID})
            elif path == "/log":
                level = (query.get("level", ["INFO"])[0] or "INFO").upper()
                message = query.get("msg", ["manual log line"])[0]
                logger = LOG.error if level == "ERROR" else LOG.warning if level == "WARN" else LOG.info
                logger(message, extra={"event": "manual_log", "path": path})
                self._send(200, {"logged": level, "message": message})
            elif path == "/slow":
                ms = max(0, min(int(query.get("ms", ["2000"])[0]), 30_000))
                time.sleep(ms / 1000)
                self._send(200, {"slept_ms": ms})
            elif path == "/load":
                seconds = max(0, min(int(query.get("seconds", ["120"])[0]), 1800))
                workers = max(1, min(int(query.get("workers", ["2"])[0]), 4))
                started_workers = start_load(seconds, workers)
                self._send(202, {"load": True, "workers": started_workers, "seconds": seconds})
            elif path == "/stop":
                stopped = stop_load()
                self._send(200, {"stopped": stopped})
            else:
                LOG.warning(
                    "not found",
                    extra={"event": "not_found", "path": path, "status": 404},
                )
                self._send(404, {"error": "not found", "path": path})
        except Exception as exc:  # noqa: BLE001
            LOG.exception(
                "unhandled request error",
                extra={"event": "unhandled_error", "path": path, "status": 500},
            )
            self._send(500, {"error": type(exc).__name__, "detail": str(exc)})
        finally:
            duration = int((time.time() - started) * 1000)
            if duration > 1000:
                LOG.info(
                    "slow request",
                    extra={
                        "event": "slow_request",
                        "path": path,
                        "duration_ms": duration,
                        "status": "-",
                    },
                )


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    LOG.info(
        "server started",
        extra={"event": "startup", "status": f"port={PORT}", "path": "/"},
    )

    def shutdown(signum, _frame):  # noqa: ANN001
        LOG.info("shutdown", extra={"event": "shutdown", "status": signum})
        stop_load()
        server.shutdown()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    try:
        server.serve_forever()
    finally:
        stop_load()


if __name__ == "__main__":
    main()
