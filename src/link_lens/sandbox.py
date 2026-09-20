"""A small trusted broker; user code never sees the Docker socket or broker network."""

import io
import base64
import json
import os
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import docker
import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from .settings import settings

app = FastAPI(title="Link Lens sandbox controller")


class PythonJob(BaseModel):
    code: str = Field(min_length=1, max_length=30_000)
    discovery: list[dict] = Field(max_length=500)
    documentation: str = Field(max_length=50_000)


@app.get("/health")
def health():
    return {"status": "ok"}


def archive(files):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o444
            info.uid = 1000
            info.gid = 1000
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def execute_job(job):
    # Arguments never come from the model, other than code and capped data payloads.
    client = docker.from_env(timeout=10)
    container = None
    started = time.monotonic()
    try:
        container = client.containers.run(
            os.getenv("SANDBOX_IMAGE", "link-lens-sandbox:local"),
            ["sleep", "120"],
            detach=True,
            user="1000:1000",
            network_mode="none",
            read_only=True,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges:true"],
            mem_limit="1g",
            memswap_limit="1g",
            nano_cpus=1_000_000_000,
            pids_limit=64,
            log_config=docker.types.LogConfig(type="none"),
            init=True,
            tmpfs={
                "/work": "rw,nosuid,nodev,size=128m,uid=1000,gid=1000,mode=0700",
                "/tmp": "rw,nosuid,nodev,size=32m",
            },
            environment={
                "PATH": "/opt/venv/bin:/usr/local/bin:/usr/bin:/bin",
                "HOME": "/work",
                "PYTHONDONTWRITEBYTECODE": "1",
                "MPLCONFIGDIR": "/work/.matplotlib",
            },
            working_dir="/work",
            labels={"app": "link-lens", "kind": "ephemeral-exploration"},
        )
        data = json.dumps(
            {"records": job.discovery, "documentation": job.documentation},
            ensure_ascii=False,
        ).encode()
        if len(data) > 2_000_000:
            raise ValueError("Discovery input exceeds 2 MB")
        # Docker's archive upload rejects a read-only root even for tmpfs destinations.
        # Copy trusted JSON in bounded argv chunks, then materialize only fixed paths.
        payload = json.dumps({"code": job.code, "input": data.decode()}).encode()
        for offset in range(0, len(payload), 40_000):
            encoded = base64.b64encode(payload[offset : offset + 40_000]).decode()
            copied = container.exec_run(
                [
                    "python",
                    "-c",
                    "import base64; open('/work/payload.json','ab').write(base64.b64decode('"
                    + encoded
                    + "'))",
                ],
                user="1000:1000",
            )
            if copied.exit_code:
                raise RuntimeError("Could not supply exploration input")
        container.exec_run(
            [
                "python",
                "-c",
                "import json; p=json.load(open('/work/payload.json')); open('/work/main.py','w').write(p['code']); open('/work/input.json','w').write(p['input'])",
            ],
            user="1000:1000",
        )
        # Redirect output into a capped file so untrusted stdout cannot fill daemon logs.
        command = [
            "sh",
            "-c",
            "ulimit -f 2048; exec python /work/main.py > /work/output.txt 2>&1",
        ]
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(
            container.exec_run, command, workdir="/work", user="1000:1000"
        )
        try:
            result = future.result(timeout=60)
            # Read from the live tmpfs through exec; Docker archive APIs inspect rootfs.
            captured = container.exec_run(
                [
                    "python",
                    "-c",
                    "import sys; sys.stdout.buffer.write(open('/work/output.txt','rb').read(100001))",
                ],
                user="1000:1000",
            )
            output = (
                captured.output if captured.exit_code == 0 else result.output[:100001]
            )
            return {
                "exit_code": result.exit_code,
                "output": output[:100_000].decode(errors="replace"),
                "truncated": len(output) > 100_000,
                "seconds": time.monotonic() - started,
            }
        except FutureTimeout:
            container.kill()
            return {
                "exit_code": 124,
                "output": "Execution exceeded 60 seconds and was killed",
                "truncated": False,
                "seconds": time.monotonic() - started,
            }
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
    finally:
        if container is not None:
            try:
                container.remove(force=True)
            except docker.errors.NotFound:
                pass
        client.close()


@app.post("/execute")
def execute(job: PythonJob, x_sandbox_token: str = Header(default="")):
    import hmac

    if not hmac.compare_digest(x_sandbox_token, settings().sandbox_token):
        raise HTTPException(403, "Invalid broker token")
    try:
        return execute_job(job)
    except Exception as exc:
        raise HTTPException(
            422, f"Sandbox execution failed: {type(exc).__name__}: {str(exc)[:300]}"
        ) from exc


def explore(code, discovery, documentation):
    with httpx.Client(timeout=80) as client:
        response = client.post(
            settings().sandbox_url + "/execute",
            headers={"X-Sandbox-Token": settings().sandbox_token},
            json={
                "code": code,
                "discovery": discovery[:500],
                "documentation": documentation[:50_000],
            },
        )
        response.raise_for_status()
        return response.json()
