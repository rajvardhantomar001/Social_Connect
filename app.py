import os
import re
from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS
from werkzeug.utils import secure_filename


app = Flask(__name__)
CORS(app)

@app.route('/api/register_user', methods=['POST'])
def register_user():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port="3306",
            user="root",
            password="",
            database="connectify"
        )
    except mysql.connector.Error as error:
        return jsonify(register_status='Error connecting to MySQL: {}'.format(error)), 400

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    mobile = request.form['mobile']
    location = request.form['location']
    interest = request.form['interest']

    # Email validation using regex
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify(register_status='Invalid email'), 400
    
    if not re.match(r"^\d{10}$", mobile):
        return jsonify(register_status='Invalid mobile number'), 400

    if not name or not email or not password:
        return jsonify(register_status='Missing required fields'), 400

    try:
        cursor = conn.cursor()
        # Check if email already exists
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify(register_status='Email already registered'), 400

        # Insert new user
        cursor.execute('INSERT INTO users (Name, email,	Mobile, location, interest, password) VALUES (%s, %s, %s, %s, %s, %s)', (name, email, mobile, location, interest, password))
        conn.commit()
    except mysql.connector.Error as error:
        return jsonify(register_status='Error registering user in MySQL: {}'.format(error)), 400

    conn.close()

    return jsonify(register_status='success'), 200

@app.route('/api/login_user', methods=['POST'])
def login_user():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port="3306",
            user="root",
            password="",
            database="connectify"
        )
    except mysql.connector.Error as error:
        return jsonify(login_status='Error connecting to MySQL: {}'.format(error)), 400

    email = request.form['email']
    password = request.form['password']

    if not email or not password:
        return jsonify(login_status='Missing required fields'), 400

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
    except mysql.connector.Error as error:
        return jsonify(login_status='Error retrieving credentials from MySQL: {}'.format(error)), 400

    conn.close()

    if user and user['password'] == password:
        return jsonify(login_status='success', user_id=user['user_id'])
    else:
        return jsonify(login_status='Invalid email or password'), 400

@app.route('/api/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port="3306",
            user="root",
            password="",
            database="connectify"
        )
    except mysql.connector.Error as error:
        return jsonify(feedback_status='Error connecting to MySQL: {}'.format(error)), 400

    feedback_text = request.form['feedback']
    email = request.form['email']  # Assuming you have a way to identify the user submitting the feedback

    if not feedback_text or not email:
        return jsonify(feedback_status='Missing required fields'), 400
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify(feedback_status='Invalid email'), 400

    try:
        cursor = conn.cursor()
        # Insert feedback into the database
        cursor.execute('INSERT INTO feedback (feedback_text, email) VALUES (%s, %s)', (feedback_text, email))
        conn.commit()
    except mysql.connector.Error as error:
        return jsonify(feedback_status='Error submitting feedback to MySQL: {}'.format(error)), 400

    conn.close()

    return jsonify(feedback_status='success'), 200

@app.route('/api/dashboard_data',methods=['POST'])
def get_dashboard_data():
    user_id = request.form['user_id']

    try: 
        # Connect to the database
        conn = mysql.connector.connect(
            host="localhost",
            port="3306",
            user="root",
            password="",
            database="connectify"
        )

        if not user_id:
            return jsonify(message='User not logged in'), 401

        # Fetch user profile
        user_profile = fetch_user_profile(conn, int(user_id))

        # Fetch provider profiles
        provider_profiles = fetch_provider_profiles(conn, int(user_id))

        # Close the database connection
        conn.close()

        # Prepare response
        dashboard_data = {
            'user_profile': user_profile,
            'provider_profiles': provider_profiles
        }

        return jsonify(dashboard_data), 200
    except Exception as e:
        return jsonify(message=str(e)), 500

def fetch_user_profile(conn, user_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
    user_profile = cursor.fetchone()
    return user_profile

def fetch_provider_profiles(conn, user_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
    user_profile = cursor.fetchone()

    query = """
        SELECT * 
        FROM users 
        WHERE location = %s AND interest = %s
    """
    values = (user_profile['location'], user_profile['interest'])
    cursor.execute(query, values)
    provider_profiles = cursor.fetchall()
    return provider_profiles

@app.route('/api/events')
def get_events(user_id):
    try:
        # Connect to the database
        conn = mysql.connector.connect(
            host="localhost",
            port="3306",
            user="root",
            password="",
            database="connectify"
        )

        if not user_id:
            return jsonify(message='User not logged in'), 401

        
        user_profile = fetch_user_profile(conn, user_id)
        # Fetch events based on interest and location
        events = fetch_events(conn, user_profile['location'], user_profile['interest'])

        # Close the database connection
        conn.close()

        return jsonify(events), 200
    except Exception as e:
        return jsonify(message=str(e)), 500

def fetch_events(conn, location, interest):
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT * 
        FROM events 
        WHERE interest = %s AND location = %s
    """
    values = (interest, location)
    cursor.execute(query, values)
    events = cursor.fetchall()
    return events

@app.route('/api/update_profile', methods=['POST'])
def update_profile(user_id):
    try:
        # Connect to the database
        conn = mysql.connector.connect(
            host="localhost",
            port="3306",
            user="root",
            password="",
            database="connectify"
        )
        if not user_id:
            return jsonify(message='User not logged in'), 401
        
        # Retrieve form data from the request
        name = request.form['name']
        location = request.form['location']
        profile_photo = request.files['profilePhoto']
        # Save the profile photo to a directory or database and get the file path

        # Update user profile in the database
        update_user_profile(conn, name, location, profile_photo.filename, user_id)

        # Close the database connection
        conn.close()

        return jsonify(message='Profile updated successfully'), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

def update_user_profile(conn, name, location, profile_photo, user_id):
    cursor = conn.cursor()
    query = """
        UPDATE users 
        SET name = %s, location = %s, bio = %s, profile_photo = %s
        WHERE user_id = %s
    """
    # Execute the query with parameters
    cursor.execute(query, (name, location, profile_photo.filename, user_id))
    # Commit the changes
    conn.commit()

# Directory to store uploaded images
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed extensions for image files
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/add_event', methods=['POST'])
def add_event():
    try:
        # Retrieve event details from the request
        event_name = request.form['eventName']
        event_description = request.form['eventDescription']
        
        # Check if the post request has the file part
        if 'eventImage' not in request.files:
            return jsonify(message='No file part'), 400
        
        file = request.files['eventImage']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify(message='No selected file'), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Connect to the database
            conn = mysql.connector.connect(
                host="localhost",
                port="3306",
                user="root",
                password="",
                database="connectify"
            )
            cursor = conn.cursor()

            # Insert the event into the database
            query = "INSERT INTO events (name, description, image) VALUES (%s, %s, %s)"
            values = (event_name, event_description, filename)
            cursor.execute(query, values)
            conn.commit()

            # Close the database connection
            conn.close()

            return jsonify(message='Event added successfully'), 200
        else:
            return jsonify(message='Invalid file type'), 400
    except Exception as e:
        return jsonify(message=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True,port='8000')