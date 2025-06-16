from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///friendfinder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-password'
mail = Mail(app)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    paid = db.Column(db.Boolean, default=False)

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    q1 = db.Column(db.String(50))
    q2 = db.Column(db.String(50))
    q3 = db.Column(db.String(50))
    q4 = db.Column(db.String(50))
    q5 = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if 'user_id' not in session:
        return redirect('/login')
    r = Response(
        user_id=session['user_id'],
        q1=request.form['q1'],
        q2=request.form['q2'],
        q3=request.form['q3'],
        q4=request.form['q4'],
        q5=request.form['q5']
    )
    db.session.add(r)
    db.session.commit()
    return redirect('/matches')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = User(email=request.form['email'], password=request.form['password'], paid=False)
        db.session.add(u)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(email=request.form['email'], password=request.form['password']).first()
        if u:
            session['user_id'] = u.id
            return redirect('/')
    return render_template('login.html')

@app.route('/matches')
def matches():
    if 'user_id' not in session:
        return redirect('/login')
    u = User.query.get(session['user_id'])
    if not u.paid:
        return redirect('/paywall')
    current = Response.query.filter_by(user_id=u.id).first()
    all_responses = Response.query.filter(Response.user_id != u.id).all()
    matches = []
    for r in all_responses:
        score = sum([
            r.q1 == current.q1,
            r.q2 == current.q2,
            r.q3 == current.q3,
            r.q4 == current.q4,
            r.q5 == current.q5
        ])
        level = "Low"
        if score >= 3:
            level = "Medium"
        if score >= 4:
            level = "Strong"
        matches.append({'user_id': r.user_id, 'score': score, 'level': level})
    return render_template('matches.html', matches=matches)

@app.route('/paywall')
def paywall():
    return "<h2>Access Denied: Please Subscribe</h2>"

@app.route('/subscribe')
def subscribe():
    if 'user_id' in session:
        u = User.query.get(session['user_id'])
        u.paid = True
        db.session.commit()
    return redirect('/matches')

def send_weekly_match_summary():
    users = User.query.filter_by(paid=True).all()
    for user in users:
        msg = Message("Your Weekly Matches", sender="your-email@example.com", recipients=[user.email])
        msg.body = "Check out your new matches this week!"
        mail.send(msg)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
