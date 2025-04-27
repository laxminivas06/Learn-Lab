from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use an environment variable for security

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

# Hardcoded admin credentials (hashed password)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'Learn Lab')  # Use environment variable
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get('ADMIN_PASSWORD', '9059'))  # Use environment variable

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
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin'] = True
            return redirect(url_for('upload'))  # Redirect to upload page after login
        return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

@app.route('/admin_subjects', methods=['GET'])
def admin_subjects():
    if 'admin' not in session:
        return redirect(url_for('admin'))  # Redirect to admin login if not logged in
    return render_template('admin_subjects.html', resources=resources)

@app.route('/delete_subject', methods=['POST'])
def delete_subject():
    if 'admin' not in session:
        return redirect(url_for('admin'))  # Redirect to admin login if not logged in

    subject = request.form.get('subject', '').lower()
    if subject in resources:
        del resources[subject]  # Remove the subject from resources
        save_resources()  # Save the updated resources to the JSON file
        return jsonify({"message": "Subject deleted successfully."})
    return jsonify({"error": "Subject not found."}), 404

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'admin' not in session:
        return redirect(url_for('admin'))  # Redirect to admin login if not logged in

    if request.method == 'POST':
        subject = request.form['subject'].lower()

        # Collect links as lists
        notes_links = request.form.getlist('notes[]')
        lab_manual_links = request.form.getlist('lab_manual[]')
        videos_links = request.form.getlist('videos[]')
        projects_links = request.form.getlist('projects[]')
        assignments_links = request.form.getlist('assignments[]')
        question_papers_links = request.form.getlist('question_papers[]')
        imp_questions_links = request.form.getlist('imp_questions[]')
        research_papers_links = request.form.getlist('research_papers[]')
        subject_description = request.form.get('description')

        # Create a new subject if it doesn't exist
        if subject not in resources:
            resources[subject] = {
                "notes": [],
                "videos": [],
                "projects": [],
                "lab_manual": [],
                "assignments": [],
                "question_papers": [],
                "imp_questions": [],
                "research_papers": [],
                "description": ""
            }

        # Update links if provided
        if notes_links:
            resources[subject]['notes'] = notes_links

        if lab_manual_links:
            resources[subject]['lab_manual'] = lab_manual_links

        if videos_links:
            resources[subject]['videos'] = videos_links

        if projects_links:
            resources[subject]['projects'] = projects_links

        if assignments_links:
            resources[subject]['assignments'] = assignments_links

        if question_papers_links:
            resources[subject]['question_papers'] = question_papers_links

        if imp_questions_links:
            resources[subject]['imp_questions'] = imp_questions_links

        if research_papers_links:
            resources[subject]['research_papers'] = research_papers_links

        if subject_description:
            resources[subject]['description'] = subject_description

        # Save resources to JSON file
        save_resources()

        return jsonify({"message": "Resources updated successfully."})

    # Always load the latest resources for the dropdown
    return render_template('upload.html', subjects=resources.keys())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)