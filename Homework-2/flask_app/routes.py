# Author: Prof. MM Ghassemi <ghassem3@msu.edu>
from flask import current_app as app
from flask import render_template, redirect, request
from .utils.database.database  import database
from werkzeug.datastructures import ImmutableMultiDict
from pprint import pprint
import json
import random
db = database()

@app.route('/')
def root():
	return redirect('/home')

@app.route('/home')
def home():
	x     = random.choice(['I started university when I was a wee lad of 15 years.','I have a pet sparrow.','I write poetry.'])
	return render_template('home.html', fun_fact = x)

@app.route('/resume')
def resume():
	resume_data = db.getResumeData()
	pprint(resume_data)
	return render_template('resume.html', resume_data = resume_data)

@app.route('/projects')
def projects():
    return render_template('projects.html')

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
