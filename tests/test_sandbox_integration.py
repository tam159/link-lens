import json
import os
import pytest
from link_lens.sandbox import PythonJob, execute_job

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_DOCKER_TESTS") != "1",
        reason="Set RUN_DOCKER_TESTS=1; uses isolated Docker execution containers",
    ),
]


def test_boundary_and_cleanup():
    import docker

    code = """import os,socket,json,pathlib
checks={"uid":os.getuid(),"secret":os.getenv("OPENAI_API_KEY"),"socket":pathlib.Path("/var/run/docker.sock").exists(),"repository":pathlib.Path("/app/.env").exists()}
for name,address in [("internet",("1.1.1.1",443)),("database",("172.17.0.1",5439))]:
 s=socket.socket();s.settimeout(.3)
 try:s.connect(address);checks[name]="reachable"
 except OSError:checks[name]="blocked"
print(json.dumps(checks))"""
    result = execute_job(PythonJob(code=code, discovery=[], documentation=""))
    checks = json.loads(result["output"])
    assert checks == {
        "uid": 1000,
        "secret": None,
        "socket": False,
        "repository": False,
        "internet": "blocked",
        "database": "blocked",
    }
    client = docker.from_env()
    try:
        assert not client.containers.list(
            all=True, filters={"label": "kind=ephemeral-exploration"}
        )
    finally:
        client.close()


def test_output_bound():
    result = execute_job(
        PythonJob(code='print("x"*500000)', discovery=[], documentation="")
    )
    assert result["truncated"] and len(result["output"]) == 100000


def test_timeout_cleanup():
    import docker

    result = execute_job(
        PythonJob(code="while True: pass", discovery=[], documentation="")
    )
    assert result["exit_code"] == 124 and result["seconds"] < 75
    client = docker.from_env()
    try:
        assert not client.containers.list(
            all=True, filters={"label": "kind=ephemeral-exploration"}
        )
    finally:
        client.close()


def test_enforced_cgroup_limits_and_read_only_root():
    code = """import json,pathlib
limits={k:pathlib.Path('/sys/fs/cgroup/'+k).read_text().strip() for k in ['memory.max','pids.max','cpu.max']}
try:pathlib.Path('/root-write-test').write_text('x');limits['root']='writable'
except OSError:limits['root']='blocked'
print(json.dumps(limits))"""
    result = execute_job(PythonJob(code=code, discovery=[], documentation=""))
    limits = json.loads(result["output"])
    assert limits["memory.max"] == "1073741824" and limits["pids.max"] == "64"
    quota, period = map(int, limits["cpu.max"].split())
    assert quota == period
    assert limits["root"] == "blocked"
