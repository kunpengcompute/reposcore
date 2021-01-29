from flask import Flask, request

from reposcore.cli import SingleRepoScore

app = Flask(__name__)

rs = SingleRepoScore("../etc/reposcore.conf")


@app.route('/', methods=['GET', 'POST'])
def login():
    content = '''
        <h3>开源项目健康度查询：</h3>
        <form method="post">
            <input type=text name=reponame placeholder=
            "请键入github url，例如：https://github.com/kunpengcompute/kunpeng">
            <input type=submit value=提交>
        </form>
    '''
    style = '''
body {
  font-family: Helvetica, arial, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  padding-top: 10px;
  padding-bottom: 10px;
  background-color: white;
  padding: 30px;
}
table {
  padding: 0;
}
table tr {
border-top: 1px solid #cccccc;
background-color: white;
margin: 0;
padding: 0;
}
table tr:nth-child(2n) {
    background-color: #f8f8f8;
}
table tr th {
    font-weight: bold;
    border: 1px solid #cccccc;
    text-align: left;
    margin: 0;
    padding: 6px 13px;
}
table tr td {
    border: 1px solid #cccccc;
    text-align: left;
    margin: 0;
    padding: 6px 13px;
}
table tr th :first-child, table tr td :first-child {
    margin-top: 0;
}
table tr th :last-child, table tr td :last-child {
    margin-bottom: 0;
}
input[type=submit] {
    height: 32px;
}
input[type=text] {
    width: 430px;
    height: 32px;
}
h1, h2, h3, h4, h5, h6 {
  margin: 20px 0 10px;
  padding: 0;
  font-weight: bold;
  -webkit-font-smoothing: antialiased;
  cursor: text;
  position: relative; }
'''
    if request.method == 'POST':
        repo_url = request.form['reponame']
        output = rs.get_score(repo_url)
        result = "<h3>查询结果：</h3>"
        for k, v in output.items():
            v = '' if v is None else v
            if k in ['name', 'url', 'language', 'criticality_score']:
                result += "<tr><td>%s</td><td>%s</td></tr>" % (k, v)
        return ''.join([
            '<style type="text/css">', style, '</style>',
            content,
            '<table>', result, '</table>'])
    return ''.join(['<style type="text/css">', style, '</style>', content])
