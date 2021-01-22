# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from collections import defaultdict
import datetime
from functools import lru_cache, _make_key
import json
import re
import threading
import time
import urllib

from criticality_score import run as cs_run
from git import Repo
import requests

from reposcore.repo import token
from reposcore.utils import matrix


class GitLocalRepo():

    def __init__(self, repo, config):
        base_path = config.get('global', 'repos_location')

        self.local_name = repo.full_name.lower()
        self.local_path = base_path + '/' + repo.full_name.lower()
        self.main_language = repo.language

        try:
            self.local_repo = Repo(self.local_path)
        except Exception:
            raise Exception("No local git repo find: %s" % self.local_path)
        self.since_time = self._get_start_date()

    def threadsafe_lru(func):
        # Enable the LRU cache, that means *same func with same args*
        # in this class, will return *same result* directly
        func = lru_cache()(func)
        lock_pool = defaultdict(threading.Lock)

        def _threadsafe_lru(*args, **kwargs):
            key = str(_make_key((func.__name__,) + args, kwargs, typed=False))
            with lock_pool[key]:
                return func(*args, **kwargs)
        return _threadsafe_lru

    def _get_start_date(self):
        start_year = int(time.strftime('%Y', time.localtime(time.time()))) - 1
        month_day = time.strftime('%m-%d', time.localtime(time.time()))
        return '{}-{}'.format(start_year, month_day)

    @threadsafe_lru
    def _code_line_change_recent_year(self, match="*"):
        addition = 0
        deletion = 0

        def _count_code_line(repo, repo_name, repo_path):
            nonlocal addition
            nonlocal deletion

            changes = repo.git.log(
                '--since', self.since_time, '--shortstat', '--oneline',
                '--', match
                ).split('\n')
            for change in changes:
                if ('files changed' not in change and
                        'file changed' not in change):
                    continue
                if 'insertions' in change:
                    addition += int(
                        change.split(' insertions')[0].split(', ')[-1])
                if 'deletions' in change:
                    deletion += int(
                        change.split(' deletions')[0].split(', ')[-1])

            if repo_name in matrix.NEED_SUBMODULE_MAPPING:
                for module in repo.submodules:
                    m_name = module.path.lower()
                    m_path = repo_path + '/' + m_name
                    if m_name not in matrix.BROKEN_PROJECT_MAPPING[repo_name]:
                        module_repo = Repo(m_path)
                        _count_code_line(module_repo, m_name, m_path)

        _count_code_line(self.local_repo, self.local_name, self.local_path)
        return (addition, deletion)

    @property
    def code_effort(self):
        # if you write 20 loc everyday, 20*22*12=5280 line
        add = self._code_line_change_recent_year()[0]
        return '%.1f' % float(add / 5280)

    @property
    def code_line_change_recent_year(self):
        return "+%d, -%d" % self._code_line_change_recent_year()

    @property
    def core_effort(self):
        # if you write 20 loc everyday, 20*22*12=5280 line
        add = self._core_line_change_recent_year()[0]
        return '%.1f' % float(add / 5280)

    @property
    def core_line_change_recent_year(self):
        add, dele, detail = self._core_line_change_recent_year()
        return "+%d, -%d (%s)" % (add, dele, detail)

    def _core_line_change_recent_year(self):
        change = {}
        for match in matrix.LANGUAGE_MAPPING.get(self.main_language, ['*']):
            change[match] = self._code_line_change_recent_year('*.' + match)

        res = []
        addition, deletion = 0, 0
        for (k, v) in change.items():
            # code have some change
            if v[0] or v[1]:
                res.append("%s: +%d, -%d" % (k, v[0], v[1]))
                addition += v[0]
                deletion += v[1]

        return (addition, deletion, ' '.join(res))

    @property
    def activity_contributor_count_recent_year(self):
        author_dict = defaultdict(int)
        active_count = 0
        # Note(yikun): the same name contributors will be one record.
        out_format = '--pretty=format:%an'
        authors = self.local_repo.git.log(
            '--since', self.since_time, out_format
            ).replace('\\', '').split('\n')
        for author_raw in authors:
            author_dict[author_raw] += 1
        for value in author_dict.values():
            if value >= 20:
                active_count += 1
        return active_count


# TODO: Remove all cs_run related code in future
class GitHubRepository(cs_run.GitHubRepository, GitLocalRepo):
    def __init__(self, repo, config):
        cs_run.GitHubRepository.__init__(self, repo)
        GitLocalRepo.__init__(self, repo, config)
        self.retry = int(config.get('global', 'retry'))

    # TODO(yikun): Re-implementation in GitLocalRepo
    def get_first_commit_time(self):
        def _parse_links(response):
            link_string = response.headers.get('Link')
            if not link_string:
                return None

            links = {}
            for part in link_string.split(','):
                match = re.match(r'<(.*)>; rel="(.*)"', part.strip())
                if match:
                    links[match.group(2)] = match.group(1)
            return links

        headers = {'Authorization': f'token {token._CACHED_GITHUB_TOKEN}'}
        for i in range(self.retry):
            result = requests.get(f'{self._repo.url}/commits', headers=headers)
            links = _parse_links(result)
            if links and links.get('last'):
                result = requests.get(links['last'], headers=headers)
                if result.status_code == 200:
                    commits = json.loads(result.content)
                    if commits:
                        last_commit_time_string = (
                            commits[-1]['commit']['committer']['date'])
                        return datetime.datetime.strptime(
                            last_commit_time_string, "%Y-%m-%dT%H:%M:%SZ")
            time.sleep(2**i)

        return None


# TODO: Remove all cs_run related code in future
class GitLabRepository(cs_run.GitLabRepository, GitLocalRepo):
    def __init__(self, repo):
        cs_run.GitLabRepository.__init__(self, repo)
        GitLocalRepo.__init__(self, repo)


def get_repository(url, config):
    """Return repository object, given a url."""
    if '://' not in url:
        url = 'https://' + url

    parsed_url = urllib.parse.urlparse(url)
    repo_url = parsed_url.path.strip('/')
    if parsed_url.netloc.endswith('github.com'):
        repo = GitHubRepository(
            token.get_github_auth_token().get_repo(repo_url), config)
        return repo
    if 'gitlab' in parsed_url.netloc:
        host = parsed_url.scheme + '://' + parsed_url.netloc
        token_obj = token.get_gitlab_auth_token(host)
        repo_url_encoded = urllib.parse.quote_plus(repo_url)
        repo = GitLabRepository(token_obj.projects.get(repo_url_encoded))
        return repo

    raise Exception('Unsupported url!')
