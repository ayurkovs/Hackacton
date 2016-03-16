from flask import Flask, render_template, session, redirect, url_for, request, g
import sqlite3

app = Flask(__name__)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('Sportner.db')
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def main():
    if session.get('logged_in'):
        return render_template('main.html')
    else:
        return redirect(url_for('login_page'))


@app.route('/login_page', methods=['GET', 'POST'])
def login_page():
    if session.get('logged_in'):
        return redirect(url_for('main'))

    error = None
    cur = get_db().cursor()
    error = ''
    for user in query_db('select * from Cities'):
        error += '{}: <h1>{}</h1> <br/>'.format(user[0], user[1])
    # if request.method == 'POST':
    # if request.form['username'] != app.config['USERNAME']:
    #     error = 'Invalid username'
    # elif request.form['password'] != app.config['PASSWORD']:
    #     error = 'Invalid password'
    # else:
    #     session['logged_in'] = True
    #     # flash('You were logged in')
    #     return redirect(url_for('main'))
    return render_template('login_page.html', error=error)


@app.route('/hello')
def hello():
    return render_template('main.html')


if __name__ == '__main__':
    app.run()
