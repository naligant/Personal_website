# Author: Prof. MM Ghassemi <ghassem3@msu.edu>
from flask import current_app as app
from flask import jsonify
from flask import render_template, redirect, request, session, url_for, copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from .utils.database.database  import database
from werkzeug.datastructures   import ImmutableMultiDict
from pprint import pprint
import json
import random
import functools
from . import socketio
db = database()


#######################################################################################
# AUTHENTICATION RELATED
#######################################################################################
def login_required(func):
    @functools.wraps(func)
    def secure_function(*args, **kwargs):
        if "email" not in session:
            return redirect(url_for("login", next=request.url))
        return func(*args, **kwargs)
    return secure_function

def getUser():
	return db.reversibleEncrypt('decrypt', session['email']) if 'email' in session else 'Unknown'

@app.route('/login')
def login():
	return render_template('login.html', user=getUser())

@app.route('/logout')
def logout():
	session.pop('email', default=None)
	return redirect('/')

@app.route('/processlogin', methods=["POST", "GET"])
def processlogin():
    form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
    check = db.authenticate(form_fields['email'], form_fields['password'])
    if check['success'] == 1:
        response = {'success': 1}
        session['email'] = db.reversibleEncrypt('encrypt', form_fields['email'])
        return json.dumps(response)
    else:
        response = {'success': 0}
        return json.dumps(response)
        


#######################################################################################
# CHATROOM RELATED
#######################################################################################
@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', user=getUser())

@socketio.on('joined', namespace='/chat')
def joined(message):
    print('here')
    join_room('main')
    if getUser() == 'owner@email.com':
        emit('status', {'msg': getUser() + ' has entered the room.', 'style': 'width: 100%;color:blue;text-align: right'}, room='main')
    else:
        emit('status', {'msg': getUser() + ' has entered the room.', 'style': 'width: 100%;color:grey;text-align: left'}, room='main')

@socketio.on('left', namespace="/chat")
def left(message):
    if getUser() == 'owner@email.com':
        emit('status', {'msg': getUser() + 'has left the chat.', 'style': 'width: 100%;color:blue;text-align: right'}, room='main')
    else:
        emit('status', {'msg': getUser() + 'has left the chat.', 'style': 'width: 100%;color:grey;text-align: left'}, room='main')
    leave_room('main')

@socketio.on('text_message', namespace='/chat')
def text(message):
    if getUser() == 'owner@email.com':
        emit('status', {'msg': message['msg'], 'style': 'width: 100%;color:blue;text-align: right'}, room='main')
    else:
         emit('status', {'msg': message['msg'], 'style': 'width: 100%;color:grey;text-align: left'}, room='main')
     


#######################################################################################
# OTHER
#######################################################################################
@app.route('/')
def root():
	return redirect('/home')

@app.route('/home')
def home():
	print(db.query('SELECT * FROM users'))
	x = random.choice(['I started university when I was a wee lad of 15 years.','I have a pet sparrow.','I write poetry.'])
	return render_template('home.html', user=getUser(), fun_fact = x)

@app.route('/projects')
def projects():
    # print(db.query('SELECT * FROM users'))
    return render_template('projects.html', user=getUser())

@app.route('/resume')
def resume():
	resume_data = db.getResumeData()
	pprint(resume_data)
	return render_template('resume.html', resume_data = resume_data, user=getUser())

@app.route('/piano')
def piano():
    	return render_template('piano.html')

@app.route('/processfeedback', methods = ['POST'])
def processfeedback():
    feedback = request.form
	# gather name from form
    name = feedback.get('name')
	#gather email from form
    email = feedback.get('email')
	#gather comment from form
    comment = feedback.get('comment')
	#insert only name, email, and comment columns into feedback table
    db.insertRows(table='feedback', columns=['name', 'email', 'comment'], parameters=[[name, email, comment]])
	#make a query to get feedback data
    feedback_query = "SELECT * FROM feedback"
	#execute query
    feedbacks = db.query(query=feedback_query)
	#place the lists into a dictionary
    feedback_dict = {row['comment_id']: {'name': row['name'], 'email': row['email'], 'comment': row['comment']} for row in feedbacks}
	#pass in the dictionary to feedback variable
    return render_template('processfeedback.html', feedback=feedback_dict)

@app.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r
