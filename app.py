from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///votes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phrase = db.Column(db.String(200), nullable=False)
    normalized_phrase = db.Column(db.String(200), nullable=False)
    player_id = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    if not os.path.exists('votes.db'):
        db.create_all()

end_time = None

@app.route('/')
def index():
    return render_template('index.html', end_time=end_time)

@app.route('/submit', methods=['POST'])
def submit():
    global end_time
    if end_time and datetime.utcnow() > end_time:
        return jsonify({'error': 'Voting period has ended.'})

    player_id = session.get('player_id', None)
    if not player_id:
        return jsonify({'error': 'Player ID not found in session.'})

    existing_submission = Submission.query.filter_by(player_id=player_id).first()
    if existing_submission:
        return jsonify({'error': 'You have already submitted a phrase.'})

    phrase = request.form['phrase'].strip().lower()
    normalized_phrase = ''.join(e for e in phrase if e.isalnum())

    new_submission = Submission(phrase=phrase, normalized_phrase=normalized_phrase, player_id=player_id)
    db.session.add(new_submission)
    db.session.commit()

    socketio.emit('update_results', broadcast=True)
    return jsonify({'success': 'Phrase submitted successfully.'})

@app.route('/results')
def results():
    submissions = Submission.query.all()
    phrase_counts = {}
    for submission in submissions:
        if submission.normalized_phrase in phrase_counts:
            phrase_counts[submission.normalized_phrase] += 1
        else:
            phrase_counts[submission.normalized_phrase] = 1

    sorted_phrases = sorted(phrase_counts.items(), key=lambda item: item[1], reverse=True)
    return render_template('results.html', submissions=sorted_phrases, end_time=end_time)

@app.route('/reset', methods=['POST'])
def reset():
    global end_time
    db.session.query(Submission).delete()
    db.session.commit()
    end_time = None
    socketio.emit('reset_results', broadcast=True)
    return redirect(url_for('results'))

@app.route('/start_timer', methods=['POST'])
def start_timer():
    global end_time
    duration = int(request.form['duration'])
    end_time = datetime.utcnow() + timedelta(seconds=duration)
    socketio.emit('start_timer', {'end_time': end_time.isoformat()})
    return redirect(url_for('results'))

@socketio.on('connect')
def handle_connect():
    if end_time:
        emit('start_timer', {'end_time': end_time.isoformat()})

if __name__ == '__main__':
    socketio.run(app)
