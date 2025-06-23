# This script executes after the project is generated from your cookiecutter.
# Details about hooks can be found in the cookiecutter documentation:
# https://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html
#
# An example of a post-hook would be to remove parts of the project
# directory tree based on some configuration values.

import os
import subprocess
import sys
from cookiecutter.utils import rmtree


class GitRepository(object):
    """ A context for the setup of a Git repository """
    def __init__(self):
        self.remotes = {}

    def __enter__(self):
        # Initialize the git repository
        subprocess.check_call("git init".split())
        subprocess.check_call("git checkout -b main".split())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Finalize by making an initial git commit
        subprocess.check_call("git add *".split())

        # Maybe run pre-commit
        if {{ have_precommit }}:
            subprocess.call("pre-commit run -a".split())
            subprocess.check_call("git add *".split())

        subprocess.check_call(["git", "commit", "-m", "Initial Commit"])
        subprocess.check_call(["git", "tag", "v0.0.1"])

    def add_remote(self, name, url):
        if self.remotes.get(name, url) != url:
            sys.stderr.write("Trying to add a remote repository twice with differing URL!")
            sys.exit(1)

        if name not in self.remotes:
            self.remotes[name] = url
            subprocess.check_call(["git", "remote", "add", name, url])


# Optionally remove files whose existence is tied to disabled features
def conditional_remove(condition, path):
    if condition:
        if os.path.isfile(path):
            os.remove(path)
        else:
            rmtree(path)


conditional_remove("{{ cookiecutter.license }}" == "None", "LICENSE.md")
conditional_remove("{{ cookiecutter.github_actions_ci }}" == "No", ".github")
conditional_remove("{{ cookiecutter.github_actions_ci }}" == "No", "codecov.yml")
conditional_remove("{{ cookiecutter.gitlab_ci }}" == "No", ".gitlab-ci.yml")
conditional_remove(not {{ have_precommit }}, ".pre-commit-config.yaml")
conditional_remove("{{ cookiecutter.notebooks }}" == "No", "notebooks")
conditional_remove("{{ cookiecutter.notebooks }}" == "No", "doc/demo.nblink")
conditional_remove("{{ cookiecutter.commandlineinterface }}" == "No", "{{ cookiecutter|modname }}/__main__.py")
conditional_remove("{{ cookiecutter.commandlineinterface }}" == "No", "tests/test_cli.py")
conditional_remove(os.stat("TODO.md").st_size == 0, "TODO.md")

# Set up a Git repository
with GitRepository() as repo:
{% if cookiecutter.remote_url != 'None' %}
    repo.add_remote("origin", "{{ cookiecutter.remote_url }}")
{% else %}
    pass
{% endif %}

# Print a message about success
print("The project {{ cookiecutter.project_slug }} was successfully generated!")
print("The file FILESTRUCTURE.md describes the purpose and content of all the generated files.")
if os.path.exists("TODO.md"):
    print("A TODO list for you to finalize the generation process was also generated, see TODO.md.")
