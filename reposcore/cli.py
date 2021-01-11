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
import csv
import os
import sys
import time

from criticality_score import run as cs_run


class RepoScore(object):
    def __init__(self):
        self.parser = None
        self.args = None
        self.retry = 3

        self.__init_constants()

    def __init_constants(self):
        # See more constants in:
        # https://github.com/ossf/criticality_score/blob/main/criticality_score/constants.py
        cs_run.CONTRIBUTOR_COUNT_WEIGHT = 1
        cs_run.ORG_COUNT_WEIGHT = 0.5
        cs_run.COMMIT_FREQUENCY_WEIGHT = 4
        cs_run.COMMENT_FREQUENCY_WEIGHT = 0.5
        cs_run.DEPENDENTS_COUNT_WEIGHT = 1

    def __create_parser(self):
        self.parser = argparse.ArgumentParser(
            description=
            'Generate a sorted criticality score list for input projects .')
        self.parser.add_argument("--projects_list",
                                 type=open,
                                 required=True,
                                 help="File name of projects url list.")
        self.parser.add_argument("--result_file",
                                 type=str,
                                 required=True,
                                 help="Result file name.")

    def run(self):
        self.__create_parser()
        self.args = self.parser.parse_args()

        repo_urls = set()
        repo_urls.update(self.args.projects_list.read().splitlines())

        csv_writer = csv.writer(sys.stdout)
        header = None
        stats = []
        for repo_url in repo_urls:
            output = None
            for _ in range(self.retry):
                try:
                    repo = cs_run.get_repository(repo_url)
                    output = cs_run.get_repository_stats(repo)
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
