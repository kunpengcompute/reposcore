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
import configparser
import csv
import git
import os
import sys
import urllib

from reposcore.utils import git_utils
from reposcore.utils import matrix
from reposcore.repo import repo as rs_repo
from reposcore.stat import stat as rs_stat


class RepoScore(object):
    def __init__(self):
        self.parser = self._create_parser()
        self.args = self.parser.parse_args()
        self.config = self._initConfig()
        self.retry = int(self.config.get('global', 'retry'))

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

    def _auto_update_repo(self, repo_urls):
        for repo_url in repo_urls:
            repo_name = urllib.parse.urlparse(repo_url).path.strip('/').lower()
            try:
                local_repo = git.Repo(
                    self.config.get('global', 'repos_location') + '/'
                    + repo_name)
            except git.exc.NoSuchPathError:
                # Clone
                local_repo = git.Repo.clone_from(
                    repo_url,
                    self.config.get(
                        'global', 'repos_location') + '/' + repo_name,
                    progress=git_utils.Progress(repo_name))
                # Submodule init
                args = ['update', '--init']
                if matrix.BROKEN_PROJECT_MAPPING.get(repo_name):
                    for project in matrix.BROKEN_PROJECT_MAPPING[repo_name]:
                        args.append('-c')
                        args.append('submodule."%s".update=none' % project)
                local_repo.git.submodule(*args)
            else:
                # Update
                print('Start updating %s' % repo_name)

                local_repo.git.pull()
                args = ['update']
                if matrix.BROKEN_PROJECT_MAPPING.get(repo_name):
                    for project in matrix.BROKEN_PROJECT_MAPPING[repo_name]:
                        args.append('-c')
                        args.append('submodule."%s".update=none' % project)
                local_repo.git.submodule(*args)

                print('Success updating %s' % repo_name)

    def run(self):
        repo_urls = set()
        repo_urls.update(self.args.project_list.read().splitlines())

        csv_writer = csv.writer(sys.stdout)
        header = None
        stats = []
        if self.args.auto_update:
            self._auto_update_repo(repo_urls)
        for repo_url in repo_urls:
            if not repo_url:
                continue
            output = None
            for _ in range(self.retry):
                try:
                    repo = rs_repo.get_repository(repo_url, self.config)
                    stat = rs_stat.Stat(self.config, repo)
                    output = stat.get_stats()
                    break
                except Exception as exp:
                    print('Failed reading repo %s\n. Detail: %s' % (
                        repo_url, exp))
            if not output:
                continue
            if not header:
                header = output.keys()
                csv_writer.writerow(header)
            csv_writer.writerow(output.values())
            stats.append(output)

        with open(self.args.result_file, 'w') as file_handle:
            csv_writer = csv.writer(file_handle)
            csv_writer.writerow(header)
            for i in sorted(stats,
                            key=lambda i: i['criticality_score'],
                            reverse=True):
                csv_writer.writerow(i.values())
        print('Finished, the results file is: %s' % self.args.result_file)


def main():
    rs = RepoScore()
    rs.run()
