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
"""Main python script for calculating Repo Score."""

import argparse
from collections import defaultdict
import configparser
import csv
from functools import lru_cache, _make_key
import git
import os
import shutil
import sys
import threading
import time
import urllib

from reposcore.utils import git_utils
from reposcore.utils import matrix
from reposcore.repo import repo as rs_repo
from reposcore.stat import stat as rs_stat


class FakeArgs(object):
    def __init__(self, conf, auto_update, enable_local):
        self.config = conf
        self.auto_update = auto_update
        self.enable_local = enable_local


class RepoScore(object):
    def __init__(self):
        self.parser = self._create_parser()
        self.args = self.parser.parse_args()
        self.config = self._initConfig()
        self.retry = int(self.config.get('global', 'retry'))
        self.enable_local = self.args.enable_local

    def _create_parser(self):
        parser = argparse.ArgumentParser(
            description='Generate a sorted score list for input projects.')
        parser.add_argument(
            '-c', dest='config',
            help='path to config file')
        parser.add_argument(
            "--project-list",
            type=open, required=True, help="File name of projects url list.")
        parser.add_argument(
            "--result-file",
            type=str, required=True, help="Result file name.")
        parser.add_argument(
            "--auto-update",
            action='store_true', default=False,
            help='Auto clone or update the source code')
        parser.add_argument(
            "--with-time",
            action='store_true', default=False,
            help='auto add a time column'),
        parser.add_argument(
            "--enable-local",
            action='store_true', default=False,
            help='with local repo offline analysis')
        return parser

    def _initConfig(self):
        config = configparser.ConfigParser()
        if self.args.config:
            location = self.args.config
        else:
            location = '/etc/reposcore/reposcore.conf'

        if os.path.exists(os.path.expanduser(location)):
            config.read(os.path.expanduser(location))
            return config

        raise Exception("Unable to locate config file in %s" % location)

    def _init_clone_repo(self, repo_url, repo_name):
        # Clone
        local_repo = git.Repo.clone_from(
            repo_url,
            self.config.get(
                'global', 'repos_location') + '/' + repo_name,
            progress=git_utils.Progress(repo_name))
        # Submodule init
        repos = matrix.SUBMODULE_MAPPING.get(repo_name)
        if repos:
            cmds = ['update', '--init']
            cmds.extend(repos)
            local_repo.git.submodule(*cmds)

    def _update_repo(self, local_repo, repo_url, repo_name):
        # Update
        print('Start updating %s' % repo_name)
        try:
            local_repo.git.pull()
            repos = matrix.SUBMODULE_MAPPING.get(repo_name)
            if repos:
                cmds = ['update']
                cmds.extend(repos)
                local_repo.git.submodule(*cmds)
        except git.exc.GitCommandError:
            # Cleanup local repo and re-clone
            print('Updating failed, re-clone %s' % repo_name)
            shutil.rmtree(local_repo.working_dir)
            self._init_clone_repo(repo_url, repo_name)

        print('Success updating %s' % repo_name)

    def _auto_update_repo(self, repo_urls):
        if not self.args.enable_local:
            return
        for repo_url in repo_urls:
            repo_name = urllib.parse.urlparse(repo_url).path.strip('/').lower()
            try:
                local_repo = git.Repo(
                    self.config.get('global', 'repos_location') + '/'
                    + repo_name)
            except git.exc.NoSuchPathError:
                self._init_clone_repo(repo_url, repo_name)
            else:
                self._update_repo(local_repo, repo_url, repo_name)

    def _insert_val(self, arr, v):
        if self.args.with_time:
            return [v] + list(arr)
        else:
            return arr

    def run(self):
        repo_urls = set()
        repo_urls.update(self.args.project_list.read().splitlines())

        csv_writer = csv.writer(sys.stdout)
        header = None
        stats = []
        if self.args.auto_update:
            self._auto_update_repo(repo_urls)
        t = time.strftime("%Y-%m-%dT%H:00:00+0800")
        for repo_url in repo_urls:
            if not repo_url:
                continue
            output = None
            for _ in range(self.retry):
                try:
                    repo = rs_repo.get_repository(
                        repo_url, self.config, self.args.enable_local)
                    stat = rs_stat.Stat(self.config, repo)
                    output = stat.get_stats()
                    break
                except Exception as exp:
                    print('Failed reading repo %s\n. Detail: %s' % (
                        repo_url, exp))
            if not output:
                continue
            if not header:
                header = self._insert_val(output.keys(), 'created_at')
                csv_writer.writerow(header)
            csv_writer.writerow(
                self._insert_val(output.values(), t))
            stats.append(output)

        with open(self.args.result_file, 'w') as file_handle:
            csv_writer = csv.writer(file_handle)
            csv_writer.writerow(header)
            for i in sorted(stats,
                            key=lambda i: i['criticality_score'],
                            reverse=True):
                csv_writer.writerow(
                    self._insert_val(i.values(), t))
        print('Finished, the results file is: %s' % self.args.result_file)


class SingleRepoScore(RepoScore):
    def __init__(self, conf, auto_update=True, enable_local=False):
        self.args = FakeArgs(
            conf, auto_update=auto_update, enable_local=enable_local)
        self.config = self._initConfig()

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

    @threadsafe_lru
    def get_score(self, repo_url):
        self._auto_update_repo([repo_url])
        repo = rs_repo.get_repository(
            repo_url, self.config, self.args.enable_local)
        stat = rs_stat.Stat(self.config, repo)
        output = stat.get_stats()
        return output


def main():
    rs = RepoScore()
    rs.run()
