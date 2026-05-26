import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__,
            template_folder='templates2',
            static_folder='static2',
            static_url_path='/static2')

app.secret_key = 'coolman'
DATABASE = 'db2/database2.db'
UPLOAD_FOLDER = 'static2/uploads'

os.makedirs('db2', exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def initiation_db():
    with get_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            sec_q TEXT NOT NULL,
            sec_a TEXT NOT NULL
        );
        """)
        
        #objave
        db.execute("""
        CREATE TABLE IF NOT EXISTS posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            besedilo TEXT NOT NULL,
            picture TEXT,
            likes INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
        
        # komentari
        db.execute("""
        CREATE TABLE IF NOT EXISTS comments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
        db.commit()

initiation_db()

"""autentikacija in varnost"""

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        sec_q = request.form['sec_q']
        sec_a = request.form['sec_a'].lower().strip()

        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password, sec_q, sec_a) VALUES (?, ?, ?, ?)",
                        (username, password, sec_q, sec_a))
            db.commit()
            session['user'] = username
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists", 400

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['app2_user_id'] = user['id']
            session['app2_username'] = user['username']
            return redirect(url_for('social'))
        return "Invalid credentials", 400   
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def social():
    if 'app2_user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST' and 'besedilo' in request.form:
        besedilo = request.form['besedilo']
        file = request.files.get('slika')
        slika_url = ""

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            pot_do_datoteke = os.path.join(UPLOAD_FOLDER, filename)
            file.save(pot_do_datoteke)
            slika_url = pot_do_datoteke

        with get_db() as db:
            db.execute("""
                INSERT INTO posts (user_id, besedilo, picture) 
                VALUES (?, ?, ?)
            """, (session['app2_user_id'], besedilo, slika_url if slika_url else None))
            db.commit()
        return redirect(url_for('social'))

    if request.method == 'POST' and 'vsebina_komentarja' in request.form:
        post_id = request.form['post_id']
        tekst = request.form['vsebina_komentarja']

        with get_db() as db:
            db.execute("""INSERT INTO comments (post_id, user_id, tekst) VALUES (?, ?, ?)""",
                        (post_id, session['app2_user_id'], tekst))
            db.commit()
        return redirect(url_for('social'))

    """pridobivanje objav"""
    with get_db() as db:
        post = db.execute("""
            SELECT posts.id, posts.besedilo, posts.picture AS slika_url, posts.likes, users.username 
            FROM posts 
            JOIN users ON posts.user_id = users.id
            ORDER BY posts.id DESC
        """).fetchall()

        """pridobivanje komentarjev"""
        komentarji = db.execute("""
            SELECT comments.post_id, comments.comment AS tekst, users.username 
            FROM comments 
            JOIN users ON comments.user_id = users.id
        """).fetchall()

    return render_template('social.html', post=post, komentarji=komentarji)

"""asinhroni klic (AJAX) za like"""

@app.route('/like/<int:post_id>', methods=['POST'])
def like(post_id):
    if 'app2_user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    db.execute("""UPDATE posts SET likes = likes + 1 WHERE id = ?""", (post_id,))
    db.commit()
    
    new_likes = db.execute("""SELECT likes FROM posts WHERE id = ?""", (post_id,)).fetchone()['likes']
    return jsonify({'likes': new_likes})

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        sec_a = request.form['sec_a'].lower().strip() 
        new_password = generate_password_hash(request.form['new_password'])
        
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            
            if user and user['sec_a'] == sec_a:
                db.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
                db.commit()
                return redirect(url_for('login'))
            else:
                return "Napačno uporabniško ime ali odgovor na varnostno vprašanje!"
                
    return render_template('reset-password.html')
if __name__ == '__main__':

    app.run(port=5001, debug=True)