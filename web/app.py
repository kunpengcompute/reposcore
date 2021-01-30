from flask import Flask, render_template, request

from reposcore.cli import SingleRepoScore

app = Flask(__name__)

rs = SingleRepoScore("../etc/reposcore.conf")


@app.route('/', methods=['GET', 'POST'])
def login():
    output = {}
    query_ok = True
    repo_url = ''
    if request.method == 'POST':
        try:
            repo_url = request.form['reponame']
            output = rs.get_score(repo_url)
            print("OK: %s" % repo_url)
        except Exception:
            print("Failed: %s" % repo_url)
            query_ok = False

    return render_template(
        'index.html',
        query_ok=query_ok,
        name=output.get('name', ''),
        url=output.get('url', repo_url),
        language=output.get('language', '无'),
        score=output.get('criticality_score')
    )
