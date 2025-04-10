from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use an environment variable for security
UPLOAD_FOLDER = 'uploads'  # Folder to save uploaded files
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load resources from a JSON file
def load_resources():
    if os.path.exists('resources.json'):
        with open('resources.json', 'r') as f:
            return json.load(f)
    return {}

# Save resources to a JSON file
def save_resources():
    with open('resources.json', 'w') as f:
        json.dump(resources, f, indent=4)

# Load resources at startup
resources = load_resources()

# Hardcoded admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')  # Use environment variable
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'password')  # Use environment variable

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    subject = request.json.get('subject', '').lower()
    if subject in resources:
        return jsonify(resources[subject])
    return jsonify({"error": "Subject not found."}), 404

@app.route('/suggestions', methods=['GET'])
def suggestions():
    query = request.args.get('query', '').lower()
    matched_subjects = [subject for subject in resources.keys() if query in subject]
    return jsonify(matched_subjects)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('upload'))  # Redirect to upload page after login
        return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve the uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'admin' not in session:
        return redirect(url_for('admin'))  # Redirect to admin login if not logged in

    if request.method == 'POST':
        subject = request.form['subject'].lower()
        notes_file = request.files.get('notes')
        lab_manual_file = request.files.get('lab_manual')
        videos_link = request.form.get('videos')
        projects_link = request.form.get('projects')
        
        # Create a new subject if it doesn't exist
        if subject not in resources:
            resources[subject] = {
                "notes": "",
                "videos": "",
                "projects": "",
                "quizzes": [],
                "lab_manual": ""
            }
        
        # Update videos and projects links if provided
        if videos_link:
            resources[subject]['videos'] = videos_link
            
        if projects_link:
            resources[subject]['projects'] = projects_link

        # Handle file uploads
        if notes_file and notes_file.filename:
            notes_filename = secure_filename(notes_file.filename)
            notes_file.save(os.path.join(app.config['UPLOAD_FOLDER'], notes_filename))
            resources[subject]['notes'] = url_for('uploaded_file', filename=notes_filename, _external=True)

        if lab_manual_file and lab_manual_file.filename:
            lab_manual_filename = secure_filename(lab_manual_file.filename)
            lab_manual_file.save(os.path.join(app.config['UPLOAD_FOLDER'], lab_manual_filename))
            resources[subject]['lab_manual'] = url_for('uploaded_file', filename=lab_manual_filename, _external=True)

        # Save resources to JSON file
        save_resources()

        return jsonify({"message": "Resources updated successfully."})

    return render_template('upload.html', subjects=resources.keys())

@app.route('/add_quiz', methods=['GET', 'POST'])
def add_quiz():
    if 'admin' not in session:
        return redirect(url_for('admin'))  # Redirect to admin login if not logged in
        
    if request.method == 'POST':
        subject = request.form['subject'].lower()
        question = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        answer = request.form['answer']
        
        # Ensure the subject exists
        if subject not in resources:
            resources[subject] = {
                "notes": "",
                "videos": "",
                "projects": "",
                "quizzes": [],
                "lab_manual": ""
            }
        
        new_quiz = {
            "question": question,
            "options": [
                f"A: {option_a}",
                f"B: {option_b}",
                f"C: {option_c}",
                f"D: {option_d}"
            ],
            "answer": answer
        }
        
        resources[subject]['quizzes'].append(new_quiz)
        
        # Save resources to JSON file
        save_resources()

        return jsonify({"message": "Quiz added successfully"})
        
    return render_template('add_quiz.html', subjects=resources.keys())

@app.route('/subjects', methods=['GET'])
def list_subjects():
    return jsonify(list(resources.keys()))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))  # Redirect to home after logout

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)