from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "vulnkey"
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/profile')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                     (username, email, password))
        conn.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", 
                            (username, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            return redirect('/profile')
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('profile.html', username=session['username'], email=session['email'])

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        new_password = request.form['new_password']
        conn = get_db()
        conn.execute("UPDATE users SET password=? WHERE id=?", (new_password, session['user_id']))
        conn.commit()
        return redirect('/profile')
    return render_template('change_password.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        file = request.files['image']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        conn = get_db()
        conn.execute("INSERT INTO uploads (user_id, filename) VALUES (?, ?)", 
                     (session['user_id'], filename))
        conn.commit()
        return redirect('/gallery')
    return render_template('upload.html')

@app.route('/gallery')
def gallery():
    if 'user_id' not in session:
        return redirect('/login')
    conn = get_db()
    images = conn.execute("SELECT * FROM uploads WHERE user_id=?", 
                          (session['user_id'],)).fetchall()
    return render_template('gallery.html', images=images)

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        content = request.form['content']
        conn = get_db()
        conn.execute("INSERT INTO posts (user_id, content) VALUES (?, ?)", 
                     (session['user_id'], content))
        conn.commit()
        return redirect('/profile')
    return render_template('create_post.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    with get_db() as db:
        db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, password TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS uploads (id INTEGER PRIMARY KEY, user_id INTEGER, filename TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT)')
    app.run(debug=True)
