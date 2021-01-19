from criticality_score import run as cs_run

import argparse
import csv
import datetime
import json
import math
import os
import sys
import threading
import time
import urllib

import github
import gitlab
import requests

from reposcore.repo import token


class GitLocalRepo():
    def __init__(self, repo):
        self.repo = repo


# TODO: Remove all cs_run related code in future
class GitHubRepository(cs_run.GitHubRepository, GitLocalRepo):
    def __init__(self, repo):
        cs_run.GitHubRepository.__init__(self, repo)
        GitLocalRepo.__init__(self, repo)


# TODO: Remove all cs_run related code in future
class GitLabRepository(cs_run.GitLabRepository, GitLocalRepo):
    def __init__(self, repo):
        cs_run.GitLabRepository.__init__(self, repo)
        GitLocalRepo.__init__(self, repo)


def get_repository(url):
    """Return repository object, given a url."""
    if not '://' in url:
        url = 'https://' + url

    parsed_url = urllib.parse.urlparse(url)
    repo_url = parsed_url.path.strip('/')
    if parsed_url.netloc.endswith('github.com'):
        repo = GitHubRepository(token.get_github_auth_token().get_repo(repo_url))
        return repo
    if 'gitlab' in parsed_url.netloc:
        host = parsed_url.scheme + '://' + parsed_url.netloc
        token_obj = token.get_gitlab_auth_token(host)
        repo_url_encoded = urllib.parse.quote_plus(repo_url)
        repo = GitLabRepository(token_obj.projects.get(repo_url_encoded))
        return repo

    raise Exception('Unsupported url!')