from flask import Flask, render_template, request

from reposcore.cli import SingleRepoScore

app = Flask(__name__)

rs = SingleRepoScore("../etc/reposcore.conf")


@app.route('/', methods=['GET', 'POST'])
def login():
    output = {}
    if request.method == 'POST':
        repo_url = request.form['reponame']
        output = rs.get_score(repo_url)

    return render_template(
        'index.html',
        name=output.get('name'),
        url=output.get('url'),
        language=output.get('language'),
        score=output.get('score')
    )
