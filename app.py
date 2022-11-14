from flask import Flask
from flask import render_template
import os
import time
import pandas as pd
import json
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from flask_sqlalchemy import SQLAlchemy

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DB_USER = "cn2544"
DB_PASSWORD = "6668"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"



# This line creates a database engine that knows how to connect to the URI above
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/')
def index():  # put application's code here
    return render_template("index.html")

@app.route('/index')
def home():
    return render_template("index.html")

@app.route('/Competition')
def Competition():
    print(request.args)
    cursor = g.conn.execute("SELECT * FROM Competitions order by cid")
    datalist = []
    for result in cursor:
        datalist.append(result[:])  # can also be accessed using result[0]
    cursor.close()
    return render_template("Competition.html", data=datalist)


@app.route('/Discussion')
def Discussion():
    print(request.args)
    cursor = g.conn.execute("SELECT * FROM dis_pos")
    datalist = []
    for result in cursor:
        datalist.append(result[:])  # can also be accessed using result[0]
    cursor.close()
    return render_template("Discussion.html", data=datalist)

@app.route('/Rank')
def Rank():
    print(request.args)
    cursor = g.conn.execute("with tmp as (select c.cid, sg.sub_id, sg.score, ss.tid from subm_grades sg, subm_sub ss, competitions c where sg.sub_id = ss.sub_id and ss.cid = c.cid) select *,rank() over(partition by cid order by score desc)from tmp")
    datalist = []
    for result in cursor:
        datalist.append(result[:])  # can also be accessed using result[0]
    cursor.close()
    return render_template("Rank.html", data=datalist)


@app.route('/Sponsor')
def Sponsor():
    print(request.args)
    cursor = g.conn.execute("SELECT * FROM Organizations")
    datalist = []
    for result in cursor:
        datalist.append(result[:])  # can also be accessed using result[0]
    cursor.close()
    return render_template("Sponsor.html", data=datalist)

@app.route('/hello')
def hello():
    cursor = g.conn.execute("select * from Users")
    names = []
    for result in cursor:
        names.append(result[:])
    cursor.close()
    return names

@app.route('/login', methods=["post"])
def login():
    user_name = request.form['username']
    email = request.form['password']
    cursor = g.conn.execute("SELECT uid, user_name, email from Users where user_name = %s and email = %s",
                   [user_name, email])
    user = cursor.fetchone()

    if user is None:
        return render_template('index.html', user = None, msg="Incorrect username name or email")
    else:
        d = {"id": user[0], "user_name": user[1], "email": user[2]}
        return render_template('index.html', user=json.dumps(d), msg = "Login successful!")


@app.route('/Team')
def Team():
    cursor = g.conn.execute(
        "SELECT teams.tid, teams.leader_id,count(distinct users.uid) FROM users,joins,teams where users.uid=joins.uid and joins.tid=teams.tid group by teams.tid")
    datalist = []
    for result in cursor:
        datalist.append(result[:])
    cursor.close()
    return render_template("Team.html", data=datalist)



@app.route('/joins', methods=["post"])
def joins():
    uid = request.form['uid']
    tid = request.form['tid']
    cursor = g.conn.execute("SELECT uid, tid from Joins where uid = %s and tid = %s",
                            [uid, tid])
    joins = cursor.fetchone()

    if joins is None:
        g.conn.execute("Insert into Joins(tid,uid,since) values (%s, %s, now())",
                       [tid, uid])

        return render_template('Team.html', joins={'uid':uid, 'tid':tid}, msg="Join the team successful")
    else:
        d = {"uid": joins[0], "tid": joins[1]}
        return render_template('Team.html', joins=json.dumps(d), msg="The user already in the team")

@app.route('/members', methods=["post"])
def members():
    tid = request.form['tid']
    cursor = g.conn.execute("SELECT tid, uid FROM Joins where tid = %s",[tid])

    datalist = []
    for result in cursor:
        datalist.append(result[1:])  # can also be accessed using result[0]
    d = {"tid":tid, "uid":datalist}
    cursor.close()
    return render_template("Team.html", members=json.dumps(d))

@app.route('/join_c', methods=["post"])
def join_c():
    cid = request.form['cid']
    tid = request.form['tid']
    cursor = g.conn.execute("SELECT cid, tid from Participates where cid = %s and tid = %s",
                            [cid, tid])
    joins = cursor.fetchone()

    if joins is None:
        try:
            g.conn.execute("Insert into Participates(tid,cid) values (%s, %s)",
                       [tid, cid])
            return render_template('Competition.html', joins={'cid':cid, 'tid':tid}, msg="Join the contest successful")
        except:
            return render_template('Competition.html', joins={'cid':cid, 'tid':tid}, msg="No such a team/contest")
    else:
        d = {"uid": joins[0], "tid": joins[1]}
        return render_template('Competition.html', joins=json.dumps(d), msg="The team already participated the contest")



@app.route('/Check_Teams', methods=["post"])
def Check_Teams():
    cid = request.form['cid']
    cursor = g.conn.execute("SELECT cid,tid FROM Participates where cid = %s",[cid])

    datalist = []
    for result in cursor:
        datalist.append(result[1:])  # can also be accessed using result[0]
    d = {"cid":cid, "tid":datalist}
    cursor.close()
    return render_template("Competition.html", teams=json.dumps(d))



if __name__ == "__main__":
  import click
  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)
  run()
