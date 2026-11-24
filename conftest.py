"""Register project-wide pytest options before test discovery."""


def pytest_addoption(parser):
    parser.addoption(
        "--roadmap-site-dir",
        help="Reuse an existing MkDocs build instead of building into a temporary directory",
    )
