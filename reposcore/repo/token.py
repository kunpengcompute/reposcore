import datetime
import os
import sys
import time

import github
import gitlab
import requests


_CACHED_GITHUB_TOKEN = None
_CACHED_GITHUB_TOKEN_OBJ = None


# TODO(yikun): Move token related code into separated class
def get_github_token_info(token_obj):
    """Return expiry information given a github token."""
    rate_limit = token_obj.get_rate_limit()
    near_expiry = rate_limit.core.remaining < 50
    wait_time = (rate_limit.core.reset - datetime.datetime.utcnow()).seconds
    return near_expiry, wait_time


# TODO(yikun): Move token related code into separated class
def get_github_auth_token():
    """Return an un-expired github token if possible from a list of tokens."""
    global _CACHED_GITHUB_TOKEN
    global _CACHED_GITHUB_TOKEN_OBJ
    if _CACHED_GITHUB_TOKEN_OBJ:
        near_expiry, _ = get_github_token_info(_CACHED_GITHUB_TOKEN_OBJ)
        if not near_expiry:
            return _CACHED_GITHUB_TOKEN_OBJ

    github_auth_token = os.getenv('GITHUB_AUTH_TOKEN')
    assert github_auth_token, 'GITHUB_AUTH_TOKEN needs to be set.'
    tokens = github_auth_token.split(',')

    min_wait_time = None
    token_obj = None
    for token in tokens:
        token_obj = github.Github(token)
        near_expiry, wait_time = get_github_token_info(token_obj)
        if not min_wait_time or wait_time < min_wait_time:
            min_wait_time = wait_time
        if not near_expiry:
            _CACHED_GITHUB_TOKEN = token
            _CACHED_GITHUB_TOKEN_OBJ = token_obj
            return token_obj

    print(f'Rate limit exceeded, sleeping till reset: {round(min_wait_time / 60, 1)} minutes.',
          file=sys.stderr)
    time.sleep(min_wait_time)
    return token_obj


# TODO(yikun): Move token related code into separated class
def get_gitlab_auth_token(host):
    """Return a gitlab token object."""
    gitlab_auth_token = os.getenv('GITLAB_AUTH_TOKEN')
    try:
        token_obj = gitlab.Gitlab(host, gitlab_auth_token)
        token_obj.auth()
    except gitlab.exceptions.GitlabAuthenticationError:
        print("Auth token didn't work, trying un-authenticated. "
              "Some params like comment_frequency will not work.")
        token_obj = gitlab.Gitlab(host)
    return token_obj