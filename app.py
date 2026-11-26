import sqlite3
import os
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter

from flask_wtf.csrf import CSRFProtect
from flask import Flask, request, render_template_string, redirect, make_response

app = Flask(__name__)
# Corrección CSRF: clave secreta y protección global con tokens
app.secret_key = os.environ.get('SECRET_KEY', 'clave-solo-para-desarrollo')
csrf = CSRFProtect(app)
metrics = PrometheusMetrics(app)
LOGIN_FALLIDOS = Counter("login_fallidos_total", "Intentos de login fallidos")

def db_query(query, params=()):
    """Función auxiliar para ejecutar queries (Vulnerable por diseño)"""
    conn = sqlite3.connect('vulnerable.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.commit()
    conn.close()
    return result

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        
        query = "SELECT * FROM usuarios WHERE username = ? AND password = ?"
        usuarios = db_query(query, (user, pw))
        
        if usuarios:
            usuario = usuarios[0]
            resp = make_response(redirect('/dashboard'))
            resp.set_cookie('user_session', usuario['username'], httponly=True, samesite='Lax')
            return resp
        LOGIN_FALLIDOS.inc()
        return "<h3>Acceso denegado</h3><a href='/login'>Volver</a>", 401

    return render_template_string('''
        <h2>Login del Sistema Académico</h2>
        <form method="post">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            Usuario: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Ingresar">
        </form>
    ''')

# --- DASHBOARD (Vulnerable a XSS y CSRF) ---
@app.route('/dashboard')
def dashboard():
    username = request.cookies.get('user_session')
    if not username:
        return redirect('/login')

    # Buscamos los datos del usuario logueado
    resultado = db_query("SELECT * FROM usuarios WHERE username = ?", (username,))
    if not resultado:
        return redirect('/login')
    datos = resultado[0]

    # Corrección XSS: plantilla con variables Jinja2 ({{ }}), que escapan el HTML automáticamente
    html = """
    <h1>Panel de {{ username }}</h1>
    <p><b>Rol:</b> {{ rol }}</p>
    <p><b>Biografía:</b> {{ bio }}</p>
    <hr>
    <h3>Actualizar Biografía (Objetivo CSRF)</h3>
    <form action="/update_bio" method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">    
        <input type="text" name="nueva_bio" placeholder="Escribe algo...">
        <input type="submit" value="Guardar Cambios">
    </form>
    <br><a href="/logout">Cerrar Sesión</a>
    """
    return render_template_string(
        html,
        username=datos['username'],
        rol=datos['rol'],
        bio=datos['bio']
    )

@app.route('/update_bio', methods=['POST'])
def update_bio():
    username = request.cookies.get('user_session')
    if username:
        nueva_bio = request.form.get('nueva_bio')
        # Vulnerable a CSRF: No hay token de validación
        db_query("UPDATE usuarios SET bio = ? WHERE username = ?", (nueva_bio, username))
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    resp = make_response(redirect('/login'))
    resp.set_cookie('user_session', '', expires=0)
    return resp

@app.route('/')
def home():
    return redirect('/login')

if __name__ == '__main__':
    # Ejecución en modo debug para fines académicos
    app.run(debug=True, port=5000)
