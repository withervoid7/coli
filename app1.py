from flask import Flask, redirect, render_template, request, session
import sqlite3

app = Flask(
    __name__,
    template_folder="templates1",
    static_folder="static1"
)

app.secret_key="Maticko"

@app.route("/")
def index():
    print(session)
    if "user" not in session:  
        return redirect("/login")
    
    con= sqlite3.connect("db/database.db")
    con.row_factory = sqlite3.row
    cursor= con.cursor()
    user = cursor.execute("select * from users where username = ?",(session["user"],)).fetchone ()


    con.close()
    return render_template("index.html", user=user)

@app.route("/login", methods = ["POST","GET"])   
def login():
    if request.method == "POST":
        username=request.form["username"]
        password=request.form["password"]
        con = sqlite3.connect("db/database.db")
        cursor = con.cursor()
        db_pass = cursor.execute("SELECT password from Users Where username = ?", (username,)).fetchone()
        con.close()
        if db_pass and db_pass[0]== password:
            session["user"]=username
            return redirect("/")
            
    return render_template("login.html")

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST":
        username=request.form["username"]
        password=request.form["password"]
        con= sqlite3.connect("db/database.db")
        cursor = con.cursor()
        resp = cursor.execute("select username from users where username = ?",(username,)).fetchall();
        if len(resp) > 0:
            con.close()
            return redirect("/login")
        cursor.execute("INSERT into users (username, password) values (?,?)",(username,password))
        con.commit()
        con.close()
        session["user"]=username
        return redirect("/")
    
    return render_template("register.html")
        


if __name__ == "__main__":
    app.run(debug=True, port=5000)