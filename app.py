from flask import Flask, request, render_template, redirect, session, jsonify
import sqlite3
from datetime import datetime, timedelta
import pytz
from werkzeug.security import check_password_hash
import requests
from user_agents import parse
# Flask app for user login with security features
app = Flask(__name__)
app.secret_key = 'supersecretkey'

MAX_ATTEMPTS = 3
LOCK_TIME_MINUTES = 5
ALLOWED_START_HOUR = 9
ALLOWED_END_HOUR = 17

# ---------- DATABASE UTILS ----------

def get_user(username):
    con = sqlite3.connect('users.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    con.close()
    return user

def reset_login_attempts(username):
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    cur.execute("UPDATE users SET failed_attempts = 0, is_locked = 0 WHERE username = ?", (username,))
    con.commit()
    con.close()

def increment_login_attempts(username):
    user = get_user(username)
    attempts = user['failed_attempts'] + 1
    is_locked = 1 if attempts >= MAX_ATTEMPTS else 0

    con = sqlite3.connect('users.db')
    cur = con.cursor()
    cur.execute("""
        UPDATE users SET failed_attempts = ?, last_failed_login = ?, is_locked = ?
        WHERE username = ?
    """, (attempts, datetime.now().isoformat(), is_locked, username))
    con.commit()
    con.close()

# ---------- SECURITY CHECKS ----------

def is_within_login_time():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    return ALLOWED_START_HOUR <= now.hour < ALLOWED_END_HOUR

def log_login_attempt(username, ip, status, user_agent):
    timestamp = datetime.now().isoformat()
    browser = user_agent.browser.family or "Unknown"
    platform = user_agent.os.family or "Unknown"
    device = user_agent.device.family or "Unknown"

    con = sqlite3.connect("users.db")
    cur = con.cursor()
    cur.execute("""
        INSERT INTO login_logs (username, ip_address, timestamp, browser, device, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, ip, timestamp, browser, device, status))
    con.commit()
    con.close()



def is_login_from_india(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        return data.get("countryCode") == "IN"
    except:
        return False

# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template('register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if get_user(username):
            return "Username already exists. Try a different one.", 409

        password_hash = generate_password_hash(password)
        con = sqlite3.connect('users.db')
        cur = con.cursor()
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash))
        con.commit()
        con.close()
        return render_template('register.html', message="Registration successful. You can now login."),redirect('/login')


    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua_string = request.headers.get('User-Agent')
    user_agent = parse(ua_string)

    if not is_login_from_india(ip):
        log_login_attempt(username, ip, 'Denied - Not from India', user_agent)
        return "Login allowed only from India.", 403

    if not is_within_login_time():
        log_login_attempt(username, ip, 'Denied - Outside Time Window', user_agent)
        return "Login allowed only between 9:00 AM and 5:00 PM IST.", 403

    user = get_user(username)
    if user:
        if user['is_locked']:
            last_attempt = datetime.fromisoformat(user['last_failed_login'])
            if datetime.now() - last_attempt < timedelta(minutes=LOCK_TIME_MINUTES):
                log_login_attempt(username, ip, 'Locked Out', user_agent)
                return "Account is locked. Try again later.", 403
            else:
                reset_login_attempts(username)

        if check_password_hash(user['password_hash'], password):
            reset_login_attempts(username)
            log_login_attempt(username, ip, 'Success', user_agent)
            session['user'] = username
            return "Login successful!"
        else:
            increment_login_attempts(username)
            log_login_attempt(username, ip, 'Failed - Wrong Password', user_agent)
            return "Invalid credentials.", 401

    log_login_attempt(username, ip, 'Failed - User Not Found', user_agent)
    return "User not found.", 404


if __name__ == '__main__':
    app.run(debug=True)



# This code is a Flask application that implements a secure user login system with features like:
# - User registration
# - Password hashing
# - Login attempt tracking
# - Account lockout after multiple failed attempts
# - Time-based login restrictions
# Note: This code assumes you have a SQLite database named 'users.db' with a table 'users' that has the following columns: