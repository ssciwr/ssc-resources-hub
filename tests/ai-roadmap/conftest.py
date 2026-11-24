"""Serve the real MkDocs build under a project prefix for browser regression tests."""

import functools
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "/ssc-resources-hub/"


def pytest_addoption(parser):
    parser.addoption(
        "--roadmap-site-dir",
        help="Reuse an existing MkDocs build instead of building into a temporary directory",
    )


class ProjectSiteHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith(PREFIX):
            self.send_error(404)
            return
        self.path = self.path[len(PREFIX) - 1:]
        super().do_GET()

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="session")
def roadmap_url(pytestconfig, tmp_path_factory):
    configured = pytestconfig.getoption("--roadmap-site-dir")
    if configured:
        site = Path(configured).resolve()
    else:
        site = tmp_path_factory.mktemp("roadmap-site")
        result = subprocess.run(
            [sys.executable, "-m", "mkdocs", "build", "--site-dir", str(site)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            pytest.fail(f"MkDocs build failed:\n{result.stdout}\n{result.stderr}")
    if not (site / "learn/ai-roadmap/index.html").is_file():
        pytest.fail(f"No built AI roadmap found in {site}")

    handler = functools.partial(ProjectSiteHandler, directory=str(site))
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}{PREFIX}learn/ai-roadmap/"
        finally:
            server.shutdown()
            thread.join(timeout=5)


@pytest.fixture(scope="session")
def base_url(roadmap_url):
    return roadmap_url


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1440, "height": 1000}}
