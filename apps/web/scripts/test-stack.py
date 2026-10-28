"""Owned, temporary PostgreSQL/API/web processes for browser tests only."""

import argparse
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

import psycopg
from alembic.config import Config
from psycopg import sql
from pydantic import SecretStr
from sqlalchemy.engine import make_url

from alembic import command

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services" / "api"
WEB = ROOT / "apps" / "web"
sys.path.insert(0, str(API))
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.core.database import build_engine  # noqa: E402
from app.seed import seed_demo  # noqa: E402


def stop(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def wait_for(url: str, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 100
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Test server exited before becoming ready")
        try:
            with opener.open(url, timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(0.2)
    raise RuntimeError("Test server startup timed out")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-port", type=int, required=True)
    parser.add_argument("--web-port", type=int, required=True)
    args = parser.parse_args()
    for port in (args.api_port, args.web_port):
        with socket.socket() as probe:
            probe.bind(
                ("127.0.0.1", port)
            )  # Refuse occupied ports; never adopt/kill user servers.
    source = make_url(Settings().database_url.get_secret_value())
    if source.drivername != "postgresql+psycopg" or source.host not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise ValueError("Browser tests require local PostgreSQL")
    name = "sih26263_m1_test_" + uuid4().hex
    url = source.set(database=name).render_as_string(hide_password=False)
    admin = source.set(drivername="postgresql", database="postgres").render_as_string(
        hide_password=False
    )
    processes: list[subprocess.Popen[bytes]] = []
    logs = ROOT / ".local"
    logs.mkdir(exist_ok=True)
    with psycopg.connect(admin, autocommit=True, connect_timeout=3) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        try:
            os.environ["DATABASE_URL"] = url
            config = Config(str(API / "alembic.ini"))
            config.set_main_option("script_location", str(API / "alembic"))
            command.upgrade(config, "head")
            auth_key, matching_key = (
                secrets.token_urlsafe(48),
                secrets.token_urlsafe(48),
            )
            origin = f"http://127.0.0.1:{args.web_port}"
            settings = Settings(
                _env_file=None,
                database_url=SecretStr(url),
                app_env="local",
                demo_auth=True,
                demo_auth_secret=SecretStr(auth_key),
                apaar_matching_key=SecretStr(matching_key),
                cors_origins=[origin],
            )
            engine = build_engine(settings)
            try:
                with Session(engine) as session, session.begin():
                    seed_demo(session, settings)
            finally:
                engine.dispose()
            environment = {
                **os.environ,
                "DATABASE_URL": url,
                "APP_ENV": "local",
                "DEMO_AUTH": "true",
                "DEMO_AUTH_SECRET": auth_key,
                "APAAR_MATCHING_KEY": matching_key,
                "CORS_ORIGINS": json.dumps([origin]),
            }
            with (
                (logs / "5a-api.log").open("wb") as api_log,
                (logs / "5a-web.log").open("wb") as web_log,
            ):
                api = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "app.main:create_app",
                        "--factory",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(args.api_port),
                        "--no-proxy-headers",
                        "--no-access-log",
                    ],
                    cwd=API,
                    env=environment,
                    stdout=api_log,
                    stderr=subprocess.STDOUT,
                    start_new_session=os.name != "nt",
                )
                processes.append(api)
                wait_for(f"http://127.0.0.1:{args.api_port}/api/v1/ready", api)
                node = shutil.which("node")
                if node is None:
                    raise RuntimeError("Node.js is required")
                web_env = {
                    **os.environ,
                    "NEXT_PUBLIC_API_BASE_URL": f"http://127.0.0.1:{args.api_port}/api/v1",
                    "NEXT_PUBLIC_DEMO_UI_ENABLED": "true",
                    "NEXT_DIST_DIR": ".next-test",
                    "NEXT_TELEMETRY_DISABLED": "1",
                }
                web = subprocess.Popen(
                    [
                        node,
                        str(WEB / "node_modules" / "next" / "dist" / "bin" / "next"),
                        "dev",
                        "--hostname",
                        "127.0.0.1",
                        "--port",
                        str(args.web_port),
                    ],
                    cwd=WEB,
                    env=web_env,
                    stdout=web_log,
                    stderr=subprocess.STDOUT,
                    start_new_session=os.name != "nt",
                )
                processes.append(web)
                wait_for(origin + "/login", web)
                if any(process.poll() is not None for process in processes):
                    raise RuntimeError("An owned test server exited during startup")
                print(json.dumps({"ready": True}), flush=True)
                # EOF also cleans up if the parent test process is interrupted.
                sys.stdin.readline()
        finally:
            for process in reversed(processes):
                stop(process)
            connection.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Never print credentials, tokens or driver exception payloads.
        print(
            f"Isolated browser stack failed ({type(error).__name__}). "
            "Check local PostgreSQL/tooling and .local/5a-*.log.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
