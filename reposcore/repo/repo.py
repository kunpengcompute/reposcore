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
import datetime
import json
import re
import time
import urllib

from criticality_score import run as cs_run
from git import Repo
import requests

from reposcore.repo import token


class GitLocalRepo():
    def __init__(self, repo, config):
        base_path = config.get('global', 'repos_location')
        repo_location = base_path + '/' + repo.full_name
        try:
            self.local_repo = Repo(repo_location)
        except Exception:
            raise Exception("No local git repo find: %s" % repo_location)
        self.since_time = self._get_start_date()

    def _get_start_date(self):
        start_year = int(time.strftime('%Y', time.localtime(time.time()))) - 1
        month_day = time.strftime('%m-%d', time.localtime(time.time()))
        return '{}-{}'.format(start_year, month_day)

    def _name_fix(self, author_raw):
        if 'freedom"' in author_raw:
            author_raw = author_raw.replace('freedom"', 'freedom')
        if '"henyxia"' in author_raw:
            author_raw = author_raw.replace('"henyxia"', 'henyxia')
        if '"Tempa Kyouran"' in author_raw:
            author_raw = author_raw.replace('"Tempa Kyouran"', 'Tempa Kyouran')
        if '"TBBle"' in author_raw:
            author_raw = author_raw.replace('"TBBle"', 'TBBle')
        return author_raw

    def _code_line_change_recent_year(self, match="*"):
        addition = 0
        deletion = 0

        changes = self.local_repo.git.log(
            '--since', self.since_time, '--shortstat', '--oneline',
            '--', match
            ).split('\n')
        for change in changes:
            if 'files changed' not in change and 'file changed' not in change:
                continue
            if 'insertions' in change:
                addition += int(change.split(' insertions')[0].split(', ')[-1])
            if 'deletions' in change:
                deletion += int(change.split(' deletions')[0].split(', ')[-1])
        return (addition, deletion)

    @property
    def code_line_change_recent_year(self):
        return "+%d, -%d" % self._code_line_change_recent_year()

    @property
    def activity_contributor_count_recent_year(self):
        author_list = {}
        active_count = 0

        out_format = '--pretty=format:{"name": "%an","email": "%ae"}'
        authors = self.local_repo.git.log(
            '--since', self.since_time, out_format
            ).replace('\\', '').split('\n')
        for author_raw in authors:
            author_raw = self._name_fix(author_raw)
            author = json.loads(author_raw)
            if not author_list.get(author['name']):
                author_list[author['name']] = {
                    "email": author['email'],
                    "commit_count": 1
                }
            else:
                author_list[author['name']]['commit_count'] += 1
        for key, value in author_list.items():
            if value['commit_count'] >= 20:
                active_count += 1

        return active_count


# TODO: Remove all cs_run related code in future
class GitHubRepository(cs_run.GitHubRepository, GitLocalRepo):
    def __init__(self, repo, config):
        cs_run.GitHubRepository.__init__(self, repo)
        GitLocalRepo.__init__(self, repo, config)
        self.retry = int(config.get('global', 'retry'))

    @property
    def core_line_change_recent_year(self):
        # TODO(yikun): language file extension map should be more complete
        lang_map = {
            "C": ['c', 'h'],
            "C++": ['cc', 'c', 'cpp', 'h', 'cxx', 'hxx'],
            "Java": ['java', 'scala'],
            "Go": ['go'],
            "Python": ['py', 'cfg'],
            "Scala": ['java', 'scala']
        }
        lang = self._repo.language
        change = {}
        for match in lang_map.get(lang, ['*']):
            change[match] = self._code_line_change_recent_year('*.' + match)

        res = []
        addition, deletion = 0, 0
        for (k, v) in change.items():
            # code have some change
            if v[0] or v[1]:
                res.append("%s: +%d, -%d" % (k, v[0], v[1]))
                addition += v[0]
                deletion += v[1]

        return "+%d, -%d (%s)" % (addition, deletion, ' '.join(res))

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
