# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from scripts.smoke_test_container import smoke_test


def test_smoke_test_runs_container_checks_health_and_cleans_up(monkeypatch) -> None:
    """The smoke test should verify /health and remove its temporary container."""
    response = MagicMock()
    response.__enter__.return_value.status = 200
    response.__enter__.return_value.read.return_value = json.dumps({"status": "ok"}).encode()
    urlopen = MagicMock(return_value=response)
    monkeypatch.setattr("scripts.smoke_test_container.urllib.request.urlopen", urlopen)
    monkeypatch.setattr("scripts.smoke_test_container.shutil.which", lambda _name: "docker")

    def run_docker(command: list[str], **_kwargs: object) -> SimpleNamespace:
        if command[1] == "run":
            return SimpleNamespace(stdout="container-id\n")
        if command[1] == "port":
            return SimpleNamespace(stdout="127.0.0.1:49153\n")
        if command[1] == "rm":
            return SimpleNamespace(stdout="")
        raise AssertionError(f"Unexpected Docker command: {command}")

    docker_run = MagicMock(side_effect=run_docker)
    monkeypatch.setattr("scripts.smoke_test_container.subprocess.run", docker_run)

    smoke_test("weather-provider-api:smoke")

    urlopen.assert_called_once_with("http://127.0.0.1:49153/health", timeout=2)
    assert docker_run.call_args_list[-1].args[0] == ["docker", "rm", "--force", "container-id"]
