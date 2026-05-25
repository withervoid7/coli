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
    print(session)
    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("db1/database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    user = cursor.execute("select * from users where username = ?", (session["username"],)).fetchone()
    notes = cursor.execute("select * from notes where creator_username = ?", (user["username"],)).fetchall()
    notes_formated = []
    for note in reversed(notes):
        notes_formated.append(
                {
                    "id": note["id"],
                    "title": note["title"],
                    "content": markdown.markdown(str(note["content"]))
                })
    print(notes)
    print(notes_formated)

    conn.close()
    return render_template("index.html", notes_list=notes_formated)

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username=request.form["username"]
        password=request.form["password"]
        conn = sqlite3.connect("db1/database.db")
        cursor = conn.cursor()
        db_pass = cursor.execute("SELECT password FROM users WHERE username= ? ;", (username,)).fetchone()
        conn.close()
        if db_pass and db_pass[0] == password:
            session["username"] = username
            return redirect("/")

    return render_template("login.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username=request.form["username"]
        password=request.form["password"]
        conn = sqlite3.connect("db1/database.db")
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
    conn = sqlite3.connect("db1/database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (creator_username) values (?)", (session["username"],))
    id=cursor.lastrowid
    conn.commit()
    conn.close()
    return render_template("editor.html", note={"id":id,"content":"", "title": "note"});


@app.route("/edit-note", methods=["POST"])
def edit_note():
    id = request.form["id"]
    conn = sqlite3.connect("db1/database.db")
    cursor = conn.cursor()
    title, content = cursor.execute("select title, content from notes where creator_username = ? and id = ?", (session["username"],id)).fetchone()
    conn.close()
    return render_template("editor.html", note={"id":id,"content":content, "title": title});

@app.route("/delete-note", methods=["POST"])
def delete_note():
    id = request.form["id"]
    conn = sqlite3.connect("db1/database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes where id=? and creator_username=?", (id, session["username"]))
    conn.commit()
    conn.close()
    return "Deleted"

@app.route("/update", methods=["POST"])
def update_note():
    print()
    print()
    print()
    print(request.form)
    id = request.form["id"]
    content = request.form["content"]
    title = request.form["title"]

    conn = sqlite3.connect("db1/database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE notes set content=?, title=? where id=? and creator_username=?", (content, title, id, session["username"]))

    conn.commit()
    conn.close()
    return "Success"

if __name__ == "__main__":
    app.run(debug=True, port=5000)