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
upload_folder = 'static2/uploads'

os.makedirs('db2', exist_ok=True)
os.makedirs(upload_folder, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def initiation_db():
    with get_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS users(
        id int primary_key autoincrement,
        username text unique not null,
        password text not null,
        sec_q text not null,
        sec_a text not null
    );
     """)
    db.execute("""
    CREATE TABLE IF NOT EXISTS posts(
        id int primary_key autoincrement,
        user_id int not null,
        besedilo text not null,
        picture text not null,
        likes int default 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)
    db.execute("""
    CREATE TABLE IF NOT EXISTS comments(
        id int primary_key autoincrement,
        post_id int not null,
        user_id int not null,
        comment text not null,
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
            db.execute("""INSERT INTO users (username, password, sec_q, sec_a) VALUES (?, ?, ?, ?)""",
                        (username, password, sec_q, sec_a))
            db.commit()
            session['user'] = username
            return redirect(url_for('index'))
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

    db = get_db()

    if request.method == 'POST' and 'besedilo' in request.form:
        if 'bededilo' in request.form:
            besedilo = request.form['besedilo']
            slika = request.files['slika']
            slika_url = None

            if slika and slika.filename != '':
                filename = secure_filename(slika.filename)
                slika.save(os.path.join(upload_folder, filename))
                slika_url = f'uploads/{filename}'
    
            db.execute("""INSERT INTO posts (user_id, besedilo, slika_url) VALUES (?, ?, ?)""",
                (session['app2_user_id'], besedilo, slika_url))
            db.commit()
            return redirect(url_for('social'))

        if 'vsebina_komentarja' in request.form:
            post_id = request.form['post_id']
            tekst = request.form['vsebina_komentarja']

            db.execute("""INSERT INTO comments (post_id, user_id, tekst) VALUES (?, ?, ?)""",
                        (post_id, session['app2_user_id'], tekst))
            db.commit()
            return redirect(url_for('social'))

    """pridobivanje objav"""

    post = db.execute("""select posts.id, posts.besedilo, posts.slika_url, posts.likes, users.username from posts
    join users on posts.user_id = users.id
    order by posts.id desc""").fetchall()

    """pridobivanje komentarjev"""
    komentarji = db.execute("""select komentarji.post_id, komentarji.tekst, users.username from komentarji
    join users on komentarji.user_id = users.id""").fetchall()

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

if __name__ == '__main__':
    app.run(port=5001, debug=True)