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
import math
import threading


class Stat():
    def __init__(self, conf, repo):
        self.params = [
            'created_since', 'updated_since',
            'contributor_count', 'org_count',
            'commit_frequency', 'recent_releases_count',
            'updated_issues_count', 'closed_issues_count',
            'comment_frequency', 'dependents_count'
        ]
        # the etra params but not sum in score
        self.extra_params = [
            'code_line_change_recent_year',
            'code_effort',
            'core_line_change_recent_year',
            'core_effort',
            'activity_contributor_count_recent_year',
        ]
        self.conf = conf
        self.repo = repo

    def get_score(self, s, max_value, weigt):
        # map score between [0, 1]
        return (math.log(1 + s) / math.log(1 + max(s, max_value))) * weigt

    def _get_repository_stats(self):
        """Return repository stats, including criticality score."""

        def _worker(repo, param, return_dict):
            """worker function"""
            return_dict[param] = getattr(repo, param)

        threads = []
        return_dict = {}

        all_params = self.params + self.extra_params

        for param in all_params:
            thread = threading.Thread(
                target=_worker, args=(self.repo, param, return_dict))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        # Guarantee insertion order.
        result_dict = {
            'name': self.repo.name,
            'url': self.repo.url,
            'language': self.repo.language,
        }
        for param in all_params:
            result_dict[param] = return_dict[param]
        return result_dict

    def get_stats(self):
        res = self._get_repository_stats()

        total_weight = sum([float(
            self.conf.get('weight', s+"_weight")) for s in self.params]
            )

        score = 0
        for s in self.params:
            score += self.get_score(
                res[s],
                float(self.conf.get('threshold', s+"_threshold")),
                float(self.conf.get('weight', s+"_weight"))
            )

        score = round(score/total_weight, 5)

        # Make sure score between 0 (least-critical) and 1 (most-critical).
        score = max(min(score, 1), 0)

        res['criticality_score'] = score
        return res
