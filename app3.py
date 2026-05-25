import os
import sqlite3
import requests
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import time


app = Flask(__name__, template_folder='templates3')
app.secret_key = "dež"

DB_PATH = 'db3/database3.db'
os.makedirs('db3', exist_ok=True)

session_api = requests.Session()
session_api.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})
def get_db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_baza():
    conn = get_db()
    cursor = conn.cursor()
    # Tabela za uporabnike
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    """)
    # Tabela za destinacije
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS destinations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mesto TEXT NOT NULL,
        drzava TEXT NOT NULL,
        opomba TEXT,
        vreme TEXT
    );
    """)
    
    # --- DODAJ TA DEL SPODAJ (Varnostni popravek) ---
    try:
        cursor.execute("ALTER TABLE destinations ADD COLUMN vreme TEXT;")
        conn.commit()
    except sqlite3.OperationalError:
        # Če stolpec že obstaja, bo javilo napako, ki jo preprosto ignoriramo
        pass
    # -------------------------------------------------
    
    conn.close()

init_baza()

#klic api

def dobi_vreme(mesto):
    # Bumped to 2.5 seconds to give the API breathing room over a standard connection
    UDAREC_TIMEOUT = 2.5
    
    g_url = f"https://geocoding-api.open-meteo.com/v1/search?name={mesto}&count=1"
    try:
        # Give the API a brief 100ms break before knocking on the door again
        time.sleep(0.1)
        
        # 1. Get Coordinates
        r_resp = session_api.get(g_url, timeout=UDAREC_TIMEOUT)
        r_resp.raise_for_status()
        r = r_resp.json()
        
        if "results" in r and len(r["results"]) > 0:
            lat = r["results"][0]["latitude"]
            lon = r["results"][0]["longitude"]
            
            # 2. Get Weather
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            w_resp = session_api.get(w_url, timeout=UDAREC_TIMEOUT)
            w_resp.raise_for_status()
            w_res = w_resp.json()
            
            if "current_weather" in w_res:
                return f"{w_res['current_weather']['temperature']} °C"
        else:
            print(f"-> Mesto '{mesto}' ni bilo najdeno na API-ju.")
            return "Neznano mesto"
            
    except requests.exceptions.Timeout:
        print(f"!!! API se je vlekel preveč počasi za {mesto}, aktiviran timeout !!!")
        return "API Timeout"
    except requests.exceptions.HTTPError as http_err:
        # If they are rate-limiting you, it will catch here (e.g., HTTP 429 Too Many Requests)
        print(f"HTTP Error (Verjetno API blokada/limit): {http_err}")
        return "API Limit"
    except Exception as e:
        print(f"Druga napaka pri vremenu za {mesto}: {e}")
        return "N/A"
        
    return "N/A"

@app.route('/')
def domov():
    if 'user' in session:
        return redirect('/dashboard')  
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def registracija():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pass = generate_password_hash(password)
        
        db = get_db()
        try:
            # S tem ukazom prisilimo bazo, da nujno naredi tabelo, če je slučajno ni!
            db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            """)
            
            # Zdaj pa vnos
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pass))
            db.commit()
            db.close()
            return redirect('/login')
        except Exception as e:
            db.close()
            print("!!! TOLE JE PRAVA NAPAKA V TERMINALU !!! :", e)
            return f"Napaka v bazi: {e}"  # <--- To ti bo zdaj izpisalo TOČNO napako direktno na ekran v brskalniku!
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user_row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        db.close()

        if not user_row:
            return redirect('/user-not-found')

        if user_row and check_password_hash(user_row['password'], password):
            session['user'] = user_row['username']
            session['user_id'] = user_row['id']
            return redirect('/dashboard')
        else:
            return "Napacno geslo ali uporabnisko ime!"

    return render_template('login.html')

@app.route('/user-not-found')
def uporabnik_ne_obstaja():
    return render_template('user_not_found.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/login')
        
    u_id = session['user_id']
    
    # procesiranje forme za nov kraj
    if request.method == 'POST':
        mesto = request.form['mesto']
        drzava = request.form['drzava']
        opomba = request.form['opomba']
        
        trenutno_vreme = dobi_vreme(mesto) 
        
        db = get_db()
        db.execute(
            "INSERT INTO destinations (user_id, mesto, drzava, opomba, vreme) VALUES (?, ?, ?, ?, ?)", 
            (u_id, mesto, drzava, opomba, trenutno_vreme)
        )
        db.commit()
        db.close()
        return redirect('/dashboard')

    db = get_db()
    vse_vrstice = db.execute("SELECT * FROM destinations WHERE user_id = ?", (u_id,)).fetchall()
    db.close()
    
    # Ustvarimo prazen seznam, da ga peš napolnimo
    končni_seznam = []
    for lokacija in vse_vrstice:
        temp_podatki = {}
        temp_podatki['id'] = lokacija['id']
        temp_podatki['mesto'] = lokacija['mesto']
        temp_podatki['drzava'] = lokacija['drzava']
        temp_podatki['opomba'] = lokacija['opomba']
        temp_podatki['vreme'] = dobi_vreme(lokacija['mesto']) 
        
        končni_seznam.append(temp_podatki)
        
    return render_template('dashboard.html', podatki=končni_seznam)


@app.route('/brisi/<int:id>', methods=['POST'])
def brisi_kraj(id):
    if 'user' not in session:
        return redirect('/login')
    
    db = get_db()
    db.execute("DELETE FROM destinations WHERE id = ? AND user_id = ?", (id, session['user_id']))
    db.commit()
    db.close()
    return redirect('/dashboard')

@app.route('/logout')
def odjava():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(port=5002, debug=True)
