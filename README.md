## 项目说明
给github和gitlab上面的工程评分， 基于[criticality_score](https://github.com/ossf/criticality_score)，增加了批量统计的功能

## 使用方法
设置GitHub Token：
- 如果你还没有Token,[创建一个Github Token](https://docs.github.com/en/free-pro-team@latest/developers/apps/about-apps#personal-access-tokens)
,设置环境变量 `GITHUB_AUTH_TOKEN`.
这样可以避免Github的[api用量限制](https://developer.github.com/v3/#rate-limiting)

```shell
export GITHUB_AUTH_TOKEN=<your access token>
```
如果你统计的项目里有GitLab的项目，还需要设置GitLab的Token：
- 如果你还没有，[创建一个Gitlab Token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)
,设置环境变量 `GITLAB_AUTH_TOKEN`.

准备工程的url列表文件，一行一个url, 格式可以参考本项目reposcore目录下的projects.txt文件

```shell
pip3 uninstall python-gitlab PyGithub
pip3 install python-gitlab PyGithub
git clone https://github.com/kunpengcompute/reposcore
cd reposcore
python3 setup.py install
reposcore --projects_list projects_url_file --result_file result.csv
```

最终输出为csv格式的文件

## Project Description 
Score github or gitlab's projects, based on [criticality_score](https://github.com/ossf/criticality_score), added batch function.
## Usage
Before running, you need to:

For GitHub repos, you need to [create a GitHub access token](https://docs.github.com/en/free-pro-team@latest/developers/apps/about-apps#personal-access-tokens) and set it in environment variable `GITHUB_AUTH_TOKEN`. 
```shell
export GITHUB_AUTH_TOKEN=<your access token>
```
For GitLab repos, you need to [create a GitLab access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html) and set it in environment variable `GITLAB_AUTH_TOKEN`. 


Prepare a projects url file, one url per line, please refer to projects.txt under directory reposcore.
```shell
pip3 uninstall python-gitlab PyGithub
pip3 install python-gitlab PyGithub
git clone https://github.com/kunpengcompute/reposcore
cd reposcore
python3 setup.py install
reposcore --projects_list projects_url_file --result_file result.csv
```
The final output is a csv format file.

