from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pyodbc
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde .env
load_dotenv()

# Configuración de la conexión a la base de datos
server = os.getenv('DB_SERVER')
database = os.getenv('DB_DATABASE')
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' +
                      server + ';DATABASE=' + database + ';UID=' +
                      username + ';PWD=' + password)
cursor = conn.cursor()

# Configuración de Flask y Flask-Login
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Clase de usuario para Flask-Login
class User(UserMixin):
    def __init__(self, user_id, role):
        self.id = user_id
        self.role = role

# Cargar el usuario para la sesión
@login_manager.user_loader
def load_user(user_id):
    role = session.get('role', None)
    if role:
        return User(user_id, role)
    return None

# Ruta para el login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verificar en la tabla de docentes
        cursor.execute("SELECT * FROM Docentes WHERE Usuario = ? AND Contraseña = ?", (username, password))
        docente = cursor.fetchone()

        if docente:
            user = User(docente.DocenteID, "docente")
            login_user(user)
            session['role'] = 'docente'
            return redirect(url_for('index'))

        # Verificar en la tabla de alumnos
        cursor.execute("SELECT * FROM Alumnos WHERE Usuario = ? AND Contraseña = ?", (username, password))
        alumno = cursor.fetchone()

        if alumno:
            user = User(alumno.AlumnoID, "alumno")
            login_user(user)
            session['role'] = 'alumno'
            return redirect(url_for('index'))

        flash('Credenciales inválidas')

    return render_template('login.html')

# Ruta para cerrar sesión
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('role', None)  # Eliminar el rol de la sesión
    return redirect(url_for('login'))

# Ruta de inicio
@app.route('/')
@login_required
def index():
    user = load_user(current_user.get_id())
    if user and user.role == 'docente':
        return redirect(url_for('index_docente'))
    elif user and user.role == 'alumno':
        return redirect(url_for('index_alumno'))
    else:
        return 'Rol no definido'

# Ruta para el índice de docentes
@app.route('/index_docente')
@login_required
def index_docente():
    return render_template('index_docente.html')

# Ruta para el índice de alumnos
@app.route('/index_alumno')
@login_required
def index_alumno():
    return render_template('index_alumno.html')

@app.route('/add_note', methods=['GET', 'POST'])
@login_required
def add_note():
    # Verificacion de usuario
    user = load_user(current_user.get_id())
    if user.role != 'docente':
        flash('Acceso denegado: solo los docentes pueden agregar notas.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        # Formulario de notas

        return redirect(url_for('index'))  # Redirigir después de agregar la nota

    return render_template('add_note.html')

@app.route('/view_notes')
@login_required
def view_notes():
    # Verificar si el usuario actual es un alumno
    user = load_user(current_user.get_id())
    if user.role != 'alumno':
        flash('Acceso denegado: solo los alumnos pueden ver las notas.')
        return redirect(url_for('index'))

    cursor.execute("SELECT Nombre, Apellido FROM Alumnos WHERE AlumnoID = ?", (user.id,))
    alumno_info = cursor.fetchone()
    nombre_completo = f"{alumno_info.Nombre} {alumno_info.Apellido}" if alumno_info else "Nombre no encontrado"

    # Obtener las notas y nombres de las asignaturas del alumno
    cursor.execute("""
            SELECT n.AsignaturaID, n.Corte, n.Calificacion, a.Nombre
            FROM Notas n
            JOIN Asignaturas a ON n.AsignaturaID = a.AsignaturaID
            WHERE n.AlumnoID = ?
        """, (user.id,))
    notas = cursor.fetchall()

    return render_template('view_notes.html', nombre_completo=nombre_completo, notas=notas)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
