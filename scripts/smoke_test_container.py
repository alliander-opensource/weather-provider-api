# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Run a container and verify its health endpoint responds successfully."""

import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from uuid import uuid4


def _run_docker(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run the Docker CLI without invoking a shell."""
    docker_executable = shutil.which("docker")
    if docker_executable is None:
        raise FileNotFoundError("Docker CLI is required to smoke-test container images.")

    return subprocess.run(  # noqa: S603
        [docker_executable, *arguments],
        check=check,
        capture_output=True,
        text=True,
    )


def smoke_test(image: str) -> None:
    """Start an image and verify its /health endpoint."""
    container_name = f"wpla-smoke-{uuid4().hex}"
    if not image or image.startswith("-"):
        raise ValueError(f"Invalid container image reference: {image!r}")

    run_result = _run_docker(
            "run",
            "--detach",
            "--name",
            container_name,
            "--publish",
            "127.0.0.1::8000",
            image,
    )
    container_id = run_result.stdout.strip()

    try:
        port_result = _run_docker("port", container_id, "8000/tcp")
        host_port = int(port_result.stdout.strip().rsplit(":", maxsplit=1)[1])
        health_url = f"http://127.0.0.1:{host_port}/health"
        last_error = "Container did not become healthy before the timeout."

        for _ in range(30):
            try:
                with urllib.request.urlopen(health_url, timeout=2) as response:
                    body = json.loads(response.read())
                    if response.status == 200 and body == {"status": "ok"}:
                        print(f"{image}: health check passed")
                        return
                    last_error = f"Unexpected health response: HTTP {response.status}, {body!r}"
                    break
            except (TimeoutError, urllib.error.URLError) as error:
                last_error = str(error)
                time.sleep(1)

        logs_result = _run_docker("logs", container_id, check=False)
        raise RuntimeError(
            f"{image}: health check failed: {last_error}\n"
            f"Container logs:\n{logs_result.stdout}{logs_result.stderr}"
        )
    finally:
        _run_docker("rm", "--force", container_id)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/smoke_test_container.py IMAGE")
    smoke_test(sys.argv[1])
