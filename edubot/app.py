from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash,request
import os
import json
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)  # 64-character random key

# File paths
RESOURCES_FILE = 'resources.json'
USERS_FILE = 'users.json'
LEADERBOARD_DIR = 'data/leaderboards'
os.makedirs(LEADERBOARD_DIR, exist_ok=True)  # Create directory if it doesn't exist





def get_leaderboard_file(subject, quiz_type):
    """Get the path to the leaderboard JSON file for a specific subject and quiz type"""
    filename = f"leaderboard_{subject.lower()}_{quiz_type.lower()}.json"
    return os.path.join(LEADERBOARD_DIR, filename)

def save_leaderboard_entry(subject, quiz_type, username, score):
    """Save a new entry to the leaderboard"""
    filepath = get_leaderboard_file(subject, quiz_type)
    
    # Load existing data or create new
    try:
        with open(filepath, 'r') as f:
            leaderboard = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        leaderboard = []
    
    # Add new entry
    new_entry = {
        'username': username,
        'score': score,
        'timestamp': datetime.now().isoformat()
    }
    leaderboard.append(new_entry)
    
    # Save back to file
    with open(filepath, 'w') as f:
        json.dump(leaderboard, f, indent=2)
    
    return leaderboard

def load_leaderboard(subject, quiz_type):
    """Load leaderboard data from JSON file"""
    filepath = get_leaderboard_file(subject, quiz_type)
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def load_resources():
    """Load resources from JSON file."""
    if os.path.exists(RESOURCES_FILE):
        with open(RESOURCES_FILE, 'r') as f:
            return json.load(f)
    return {}

def load_users():
    """Load users from JSON file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_resources():
    """Save resources to JSON file."""
    with open(RESOURCES_FILE, 'w') as f:
        json.dump(resources, f, indent=4)

def save_users():
    """Save users to JSON file."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Load initial data
resources = load_resources()
users = load_users()

# Admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'Learn Lab')
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get('ADMIN_PASSWORD', '9059'))

# Helper function to check authentication

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session and 'admin' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/protected')
@login_required
def protected_route():
    return "This is protected content"


@app.template_filter('format_timestamp')
def format_timestamp(timestamp):
    """Format timestamp for display."""
    if timestamp is None:
        return "N/A"
    if isinstance(timestamp, str):
        try:
            return datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M')
        except ValueError:
            return timestamp  # Return as-is if not ISO format
    elif hasattr(timestamp, 'strftime'):
        return timestamp.strftime('%Y-%m-%d %H:%M')
    return str(timestamp)

@app.route('/')
def home():
    """Redirect to login or index based on session."""
    if 'username' in session or 'admin' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    """Render the index page."""
    return render_template('index.html', 
                         logged_in=True,
                         username=session.get('username'),
                         is_admin='admin' in session)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        # Check admin login
        if username == ADMIN_USERNAME:
            if check_password_hash(ADMIN_PASSWORD_HASH, password):
                session['admin'] = True
                session['username'] = username
                flash('Admin login successful', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid admin credentials', 'error')
                return render_template('login.html')
        
        # Check regular user login
        user_data = users.get(username)
        if user_data and check_password_hash(user_data['password'], password):
            session['username'] = username
            flash('Login successful', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if 'username' in session or 'admin' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if not all([username, password, email]):
            return render_template('register.html', error="All fields are required")
        
        if username in users:
            return render_template('register.html', error="Username already exists")
        
        users[username] = {
            'password': generate_password_hash(password),
            'email': email,
            'favorites': []
        }
        save_users()
        
        session['username'] = username
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('username', None)
    session.pop('admin', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Profile routes
@app.route('/profile')
@login_required
def profile():
    """Render user profile page."""
    username = session.get('username')
    user_data = users.get(username)
    
    if not user_data:
        session.pop('username', None)
        flash('User data not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    return render_template('profile.html',
                         username=username,
                         email=user_data.get('email', ''),
                         favorites=user_data.get('favorites', []))

@app.route('/add_favorite', methods=['POST'])
@login_required
def add_favorite():
    """Add a subject to user's favorites."""
    username = session['username']
    subject = request.json.get('subject')
    if not subject:
        return jsonify({"error": "Subject required"}), 400
    if subject not in users[username]['favorites']:
        users[username]['favorites'].append(subject)
        save_users()
    return jsonify({"message": "Favorite added"})

@app.route('/remove_favorite', methods=['POST'])
@login_required
def remove_favorite():
    """Remove a subject from user's favorites."""
    username = session['username']
    subject = request.json.get('subject')
    if not subject:
        return jsonify({"error": "Subject required"}), 400
    if subject in users[username]['favorites']:
        users[username]['favorites'].remove(subject)
        save_users()
    return jsonify({"message": "Favorite removed"})

# Resource query routes
@app.route('/query', methods=['POST'])
@login_required
def query():
    """Query resources based on subject."""
    subject = request.json.get('subject', '').lower()
    if subject in resources:
        return jsonify(resources[subject])
    return jsonify({"error": "Subject not found"}), 404

@app.route('/suggestions', methods=['GET'])
@login_required
def suggestions():
    """Provide suggestions based on user query."""
    query = request.args.get('query', '').lower()
    matches = [s for s in resources.keys() if query in s]
    return jsonify(matches)

# Quiz routes
@app.route('/quiz')
@login_required
def quiz_home():
    """Render quiz home page."""
    return render_template('quiz_home.html', subjects=resources.keys())

@app.route('/quiz/select', methods=['POST'])
@login_required
def quiz_select():
    """Select quiz type for a subject."""
    subject = request.form.get('subject')
    if not subject or subject not in resources:
        flash('Invalid subject selection', 'error')
        return redirect(url_for('quiz_home'))
    
    quiz_types = []
    if 'quiz' in resources[subject]:
        quiz_types = list(resources[subject]['quiz'].keys())
    
    if not quiz_types:
        flash('No quiz types available for this subject', 'error')
        return redirect(url_for('quiz_home'))
    
    return render_template('quiz_select.html', 
                         subject=subject, 
                         quiz_types=quiz_types)

@app.route('/quiz/start', methods=['POST'])
@login_required
def quiz_start():
    """Start the selected quiz."""
    subject = request.form.get('subject')
    quiz_type = request.form.get('quiz_select')
    
    if not subject or not quiz_type:
        flash('Subject and quiz type are required.', 'error')
        return redirect(url_for('quiz_home'))

    if subject not in resources:
        flash('Subject not found.', 'error')
        return redirect(url_for('quiz_home'))
    
    if 'quiz' not in resources[subject] or quiz_type not in resources[subject]['quiz']:
        flash('No questions available for this quiz type.', 'error')
        return redirect(url_for('quiz_home'))
    
    questions = resources[subject]['quiz'][quiz_type]
    
    if not questions:
        flash('No questions available for this quiz type.', 'error')
        return redirect(url_for('quiz_home'))
    
    # Set time limit (default 10 seconds per question)
    time_limit = len(questions) * 10
    
    return render_template('quiz_questions.html',
                         subject=subject,
                         quiz_type=quiz_type,
                         questions=enumerate(questions, 1),
                         time_limit=time_limit)


@app.route('/quiz/submit', methods=['POST'])
@login_required
def quiz_submit():
    """Submit the quiz and calculate the score."""
    try:
        # Check if user is logged in
        if 'username' not in session:
            flash('You need to be logged in to submit a quiz', 'error')
            return redirect(url_for('login'))

        answers = request.form.to_dict()
        username = session['username']
        subject = answers.pop('subject', None)
        quiz_type = answers.pop('quiz_type', None)
        time_spent = answers.pop('time_spent', 0)

        # Validate required fields
        if not subject or not quiz_type:
            flash('Invalid quiz submission data', 'error')
            return redirect(url_for('quiz_home'))

        # Check if subject and quiz type exist
        if (subject not in resources or 
            'quiz' not in resources[subject] or 
            quiz_type not in resources[subject]['quiz']):
            flash('Invalid quiz configuration', 'error')
            return redirect(url_for('quiz_home'))

        questions = resources[subject]['quiz'][quiz_type]
        total = len(questions)
        correct = 0

        # Calculate score
        for i, question in enumerate(questions, 1):
            if answers.get(f'q{i}') == question['correct']:
                correct += 1

        score = (correct / total) * 100 if total > 0 else 0

        # Update leaderboard
        leaderboard = save_leaderboard_entry(subject, quiz_type, username, score)

        # Calculate position
        sorted_leaderboard = sorted(
            leaderboard,
            key=lambda x: x['score'],
            reverse=True
        )
        
        position = next(
            (i+1 for i, entry in enumerate(sorted_leaderboard) if entry['username'] == username),
            len(sorted_leaderboard)+1
        )

        return render_template('quiz_results.html',
                            subject=subject,
                            quiz_type=quiz_type,
                            score=score,
                            correct=correct,
                            total=total,
                            position=position,
                            time_spent=time_spent,
                            leaderboard=sorted_leaderboard[:10])

    except Exception as e:
        app.logger.error(f"Error submitting quiz: {str(e)}")
        flash('An error occurred while processing your quiz submission', 'error')
        return redirect(url_for('quiz_home'))

@app.route('/leaderboard/<subject>/<quiz_type>')
@login_required
def leaderboard(subject, quiz_type):
    """Display the leaderboard for a specific quiz."""
    leaderboard_data = load_leaderboard(subject, quiz_type)
    
    # Sort by score (highest first)
    sorted_leaderboard = sorted(
        leaderboard_data,
        key=lambda x: x['score'],
        reverse=True
    )
    
    return render_template('leaderboard.html',
                         subject=subject,
                         quiz_type=quiz_type,
                         leaderboard=sorted_leaderboard,
                         users=users)

# Admin routes
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Admin login page."""
    if 'admin' in session:
        return redirect(url_for('upload'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin'] = True
            return redirect(url_for('upload'))
        
        return render_template('admin_login.html', error="Invalid admin credentials")
    
    return render_template('admin_login.html')

@app.route('/admin_subjects')
@login_required
def admin_subjects():
    """Render admin subjects management page."""
    if 'admin' not in session:
        return redirect(url_for('index'))
    return render_template('admin_subjects.html', resources=resources)

@app.route('/delete_subject', methods=['POST'])
@login_required
def delete_subject():
    """Delete a subject from resources and its leaderboard files."""
    if 'admin' not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    subject = request.form.get('subject', '').lower()
    if subject in resources:
        # Delete all leaderboard files for this subject
        for quiz_type in resources[subject].get('quiz', {}):
            filepath = get_leaderboard_file(subject, quiz_type)
            try:
                os.remove(filepath)
            except FileNotFoundError:
                pass
        
        # Delete the subject from resources
        del resources[subject]
        save_resources()
        return jsonify({"message": "Subject deleted"})
    return jsonify({"error": "Subject not found"}), 404

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload resources for a subject."""
    if 'admin' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        subject = request.form['subject'].lower()
        
        # Initialize subject structure
        if subject not in resources:
            resources[subject] = {
                "notes": [], "videos": [], "projects": [], "lab_manual": [],
                "assignments": [], "question_papers": [], "imp_questions": [],
                "research_papers": [], "description": "", "quiz": {}
            }
        
        # Update resources
        for field in ['notes', 'videos', 'projects', 'lab_manual', 
                     'assignments', 'question_papers', 'imp_questions', 
                     'research_papers']:
            if field in request.form:
                resources[subject][field] = request.form.getlist(field + '[]')
        
        if 'description' in request.form:
            resources[subject]['description'] = request.form['description']
        
        # Handle quiz questions if provided
        quiz_data = request.form.get('quiz_data')
        if quiz_data:
            try:
                quiz_json = json.loads(quiz_data)
                for quiz_type, questions in quiz_json.items():
                    resources[subject]['quiz'][quiz_type] = questions
            except json.JSONDecodeError:
                flash('Invalid quiz data format', 'error')
        
        save_resources()
        flash('Resources updated successfully.', 'success')
        return redirect(url_for('upload'))
    
    return render_template('upload.html', subjects=resources.keys())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)