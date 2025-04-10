from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import json

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

# Hardcoded admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'Learn Lab')  # Use environment variable
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '9059')  # Use environment variable

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
        notes_link = request.form.get('notes')
        lab_manual_link = request.form.get('lab_manual')
        videos_link = request.form.get('videos')
        projects_link = request.form.get('projects')
        assignments_link = request.form.get('assignments')
        question_papers_link = request.form.get('question_papers')
        imp_questions_link = request.form.get('imp_questions')
        research_papers_link = request.form.get('research_papers')
        subject_description = request.form.get('description')
        
        # Create a new subject if it doesn't exist
        if subject not in resources:
            resources[subject] = {
                "notes": "",
                "videos": "",
                "projects": "",
                "quizzes": [],
                "lab_manual": "",
                "assignments": "",
                "question_papers": "",
                "imp_questions": "",
                "research_papers": "",
                "description": ""
            }
        
        # Update links if provided
        if notes_link:
            resources[subject]['notes'] = notes_link
            
        if lab_manual_link:
            resources[subject]['lab_manual'] = lab_manual_link
            
        if videos_link:
            resources[subject]['videos'] = videos_link
            
        if projects_link:
            resources[subject]['projects'] = projects_link
            
        if assignments_link:
            resources[subject]['assignments'] = assignments_link
            
        if question_papers_link:
            resources[subject]['question_papers'] = question_papers_link
            
        if imp_questions_link:
            resources[subject]['imp_questions'] = imp_questions_link
            
        if research_papers_link:
            resources[subject]['research_papers'] = research_papers_link
            
        if subject_description:
            resources[subject]['description'] = subject_description

        # Save resources to JSON file
        save_resources()

        return jsonify({"message": "Resources updated successfully."})

    # Always load the latest resources for the dropdown
    return render_template('upload.html', subjects=resources.keys())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)