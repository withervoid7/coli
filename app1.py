from flask import Flask, redirect, render_template, request, session
import sqlite3
import markdown

app = Flask(
        __name__,
        template_folder="templates1",
        static_folder="static1"
        )


app.secret_key = "JoJolands is da best"


@app.route("/")
def index():
    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("db/database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Preverimo obstoj uporabnika
    user = cursor.execute("select * from users where username = ?", (session["username"],)).fetchone()
    if user is None:
        session.pop("username", None)
        conn.close()
        return redirect("/login")

    try:
        notes = cursor.execute("select * from notes where creator_username = ?", (session["username"],)).fetchall()
    except sqlite3.OperationalError as e:
        conn.close()
        return f"<h3>Napaka v bazi podatkov!</h3><p>SQLite pravi: <b>{e}</b></p><p>Preveri, če ima tabela 'notes' res stolpec 'creator_username'.</p>"

    notes_formated = []
    for note in reversed(notes):
        title = note["title"] if note["title"] is not None else "Brez naslova"
        content = markdown.markdown(str(note["content"])) if note["content"] is not None else ""
        
        notes_formated.append(
            {
                "id": note["id"],
                "title": title,
                "content": content
            })

    conn.close()
    return render_template("index.html", notes_list=notes_formated)

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        conn = sqlite3.connect("db/database.db")
        cursor = conn.cursor()
        db_pass = cursor.execute("SELECT password FROM users WHERE username = ? ;", (username,)).fetchone()
        conn.close()
        
        if db_pass and db_pass[0] == password:
            session["username"] = username
            return redirect("/")
        else:
            return render_template("login.html", error="Napačno uporabniško ime ali geslo!")

   
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/login")

    return render_template("login.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username=request.form["username"]
        password=request.form["password"]
        conn = sqlite3.connect("db/database.db")
        cursor = conn.cursor()
        resp = cursor.execute("SELECT username from users where username= ? ;", (username,)).fetchall();
        print(resp)
        if len(resp) > 0:
            conn.close()
            return redirect("/login")
        cursor.execute("INSERT INTO users (username, password) values (?, ?)", (username, password))
        conn.commit()
        conn.close()
        session["username"] = username
        return redirect("/")

    return render_template("register.html")

@app.route("/create-note")
def create_note():
    conn = sqlite3.connect("db/database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (creator_username) values (?)", (session["username"],))
    id=cursor.lastrowid
    conn.commit()
    conn.close()
    return render_template("editor.html", note={"id":id,"content":"", "title": "note"});


@app.route("/edit-note", methods=["POST"])
def edit_note():
    id = request.form["id"]
    conn = sqlite3.connect("db/database.db")
    cursor = conn.cursor()
    title, content = cursor.execute("select title, content from notes where creator_username = ? and id = ?", (session["username"],id)).fetchone()
    conn.close()
    return render_template("editor.html", note={"id":id,"content":content, "title": title});

@app.route("/delete-note", methods=["POST"])
def delete_note():
    id = request.form["id"]
    conn = sqlite3.connect("db/database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes where id=? and creator_username=?", (id, session["username"]))
    conn.commit()
    conn.close()
    
    return redirect("/")

@app.route("/update", methods=["POST"])
def update_note():
    print()
    print()
    print()
    print(request.form)
    id = request.form["id"]
    content = request.form["content"]
    title = request.form["title"]

    conn = sqlite3.connect("db/database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE notes set content=?, title=? where id=? and creator_username=?", (content, title, id, session["username"]))

    conn.commit()
    conn.close()
    return "Success"

def init_db():
    conn = sqlite3.connect("db/database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT DEFAULT 'note',
        content TEXT DEFAULT '',
        creator_username TEXT,
        FOREIGN KEY(creator_username) REFERENCES users(username)
    );
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)