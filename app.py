from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "cbtis-secret-key")
ADMIN_CREDENTIALS = {
    "admin": "admin123"
}

MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://rosaldoantoniocbtis_db_user:tCQ5641BploPNZLM@cbtis.nt3myx6.mongodb.net/escuela?retryWrites=true&w=majority&appName=CBTIS")
client = MongoClient(MONGO_URI)
db = client.get_default_database()

def to_str_id(doc):
    if not doc:
        return None
    doc['id'] = str(doc['_id'])
    return doc

def to_str_list(cursor):
    return [to_str_id(d) for d in cursor]

def calcular_promedios(alumno):
    """Calcula promedios de parciales, materias y semestres"""
    if 'semestres' not in alumno or not alumno['semestres']:
        return alumno
    
    for semestre in alumno['semestres']:
        total_materias = len(semestre['materias'])
        suma_calificaciones = 0
        materias_aprobadas = 0
        
        for materia in semestre['materias']:
            if 'parciales' in materia and materia['parciales']:
                materia['promedio_parciales'] = round(sum(materia['parciales']) / len(materia['parciales']), 2)
            
            if 'calificacion_final' in materia and materia['calificacion_final']:
                suma_calificaciones += materia['calificacion_final']
                if materia['estado'] == 'Aprobada':
                    materias_aprobadas += 1
        
        if total_materias > 0:
            semestre['promedio_semestre'] = round(suma_calificaciones / total_materias, 2)
            semestre['materias_aprobadas'] = materias_aprobadas
            semestre['materias_reprobadas'] = total_materias - materias_aprobadas
    
    promedios_semestres = [s['promedio_semestre'] for s in alumno['semestres'] if 'promedio_semestre' in s]
    if promedios_semestres:
        alumno['promedio_general'] = round(sum(promedios_semestres) / len(promedios_semestres), 2)
    
    return alumno

@app.route("/")
def index():
    if 'alumno_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        numero_control = request.form.get("numero_control", "").strip()
        contrasena = request.form.get("contrasena", "").strip()
        
        if numero_control in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[numero_control] == contrasena:
            session['alumno_id'] = 'admin'
            session['numero_control'] = 'admin'
            session['nombre'] = 'Administrador'
            session['es_admin'] = True
            flash("Bienvenido Administrador", "success")
            return redirect(url_for('admin_dashboard'))
        
        alumno = db.alumnos.find_one({"numero_control": numero_control})
        
        if alumno and alumno.get('contrasena') == contrasena:
            session['alumno_id'] = str(alumno['_id'])
            session['numero_control'] = alumno['numero_control']
            session['nombre'] = alumno['nombre']
            session['es_admin'] = False
            flash(f"Bienvenido/a {alumno['nombre']}", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Usuario o contraseña incorrectos", "danger")
    
    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", "info")
    return redirect(url_for('login'))

@app.route("/dashboard")
def dashboard():
    if session.get('es_admin'):
        return redirect(url_for('admin_dashboard'))
    
    if 'alumno_id' not in session:
        return redirect(url_for('login'))
    
    alumno = db.alumnos.find_one({"_id": ObjectId(session['alumno_id'])})
    if not alumno:
        flash("Alumno no encontrado", "danger")
        return redirect(url_for('login'))
    
    alumno = to_str_id(alumno)
    alumno = calcular_promedios(alumno)
    
    return render_template("dashboard.html", alumno=alumno)
    
@app.route("/historial")
def historial():
    if 'alumno_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('es_admin'):
        return redirect(url_for('admin_dashboard'))
    
    alumno = db.alumnos.find_one({"_id": ObjectId(session['alumno_id'])})
    if not alumno:
        flash("Alumno no encontrado", "danger")
        return redirect(url_for('login'))
    
    alumno = to_str_id(alumno)
    alumno = calcular_promedios(alumno)
    
    total_materias = 0
    materias_aprobadas = 0
    total_creditos = 0
    
    if 'semestres' in alumno:
        for semestre in alumno['semestres']:
            total_materias += len(semestre['materias'])
            for materia in semestre['materias']:
                if materia['estado'] == 'Aprobada':
                    materias_aprobadas += 1
                total_creditos += materia.get('creditos', 0)
    
    materias_reprobadas = total_materias - materias_aprobadas
    
    return render_template("historial.html", 
                         alumno=alumno,
                         total_materias=total_materias,
                         materias_aprobadas=materias_aprobadas,
                         materias_reprobadas=materias_reprobadas,
                         total_creditos=total_creditos)

@app.route("/boletas")
def boletas():
    if 'alumno_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('es_admin'):
        return redirect(url_for('admin_dashboard'))
    
    alumno = db.alumnos.find_one({"_id": ObjectId(session['alumno_id'])})
    if not alumno:
        flash("Alumno no encontrado", "danger")
        return redirect(url_for('login'))
    
    alumno = to_str_id(alumno)
    alumno = calcular_promedios(alumno)
    
    return render_template("boletas.html", alumno=alumno)

@app.route("/admin/alumnos")
def admin_alumnos():
    """Lista de alumnos para administrar"""
    alumnos = to_str_list(db.alumnos.find().sort("nombre", 1))
    for alumno in alumnos:
        alumno = calcular_promedios(alumno)
    return render_template("admin_alumnos.html", alumnos=alumnos)

@app.route("/admin/alumnos/new", methods=["GET", "POST"])
def create_alumno():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        edad = request.form.get("edad", "").strip()
        grupo = request.form.get("grupo", "").strip()
        promedio = request.form.get("promedio", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo = request.form.get("correo", "").strip()
        contrasena = request.form.get("contrasena", "").strip()
        numero_control = request.form.get("numero_control", "").strip()
        grado = request.form.get("grado", "").strip()
        especialidad = request.form.get("especialidad", "").strip()
        turno = request.form.get("turno", "").strip()
        
        try:
            promedio = float(promedio) if promedio else None
            if promedio is not None and (promedio < 0 or promedio > 10):
                flash('Error: El promedio debe estar entre 0 y 10', 'danger')
                return redirect(url_for('create_alumno'))
        except:
            promedio = None

        alumno = {
            "nombre": nombre,
            "edad": int(edad) if edad.isdigit() else None,
            "grupo": grupo,
            "promedio": promedio,
            "telefono": telefono,
            "correo": correo,
            "contrasena": contrasena,
            "numero_control": numero_control,
            "grado": grado,
            "especialidad": especialidad,
            "turno": turno,
            "semestres": []  
        }
        db.alumnos.insert_one(alumno)
        flash("Alumno creado correctamente.", "success")
        return redirect(url_for('admin_alumnos'))
    return render_template("create.html")

@app.route("/admin/alumnos/<id>")
def view_alumno(id):
    try:
        alumno = db.alumnos.find_one({"_id": ObjectId(id)})
    except:
        alumno = None
    if not alumno:
        flash("Alumno no encontrado.", "danger")
        return redirect(url_for('admin_alumnos'))
    alumno = to_str_id(alumno)
    alumno = calcular_promedios(alumno)
    return render_template("view.html", alumno=alumno)

@app.route("/admin/alumnos/edit/<id>", methods=["GET", "POST"])
def edit_alumno(id):
    try:
        alumno = db.alumnos.find_one({"_id": ObjectId(id)})
    except:
        alumno = None
    if not alumno:
        flash("Alumno no encontrado.", "danger")
        return redirect(url_for('admin_alumnos'))
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        edad = request.form.get("edad", "").strip()
        grupo = request.form.get("grupo", "").strip()
        promedio = request.form.get("promedio", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo = request.form.get("correo", "").strip()
        contrasena = request.form.get("contrasena", "").strip()
        numero_control = request.form.get("numero_control", "").strip()
        grado = request.form.get("grado", "").strip()
        especialidad = request.form.get("especialidad", "").strip()
        turno = request.form.get("turno", "").strip()
        
        try:
            promedio = float(promedio) if promedio else None
            if promedio is not None and (promedio < 0 or promedio > 10):
                flash('Error: El promedio debe estar entre 0 y 10', 'danger')
                return redirect(url_for('edit_alumno', id=id))
        except:
            promedio = None
            
        update = {
            "nombre": nombre,
            "edad": int(edad) if edad.isdigit() else None,
            "grupo": grupo,
            "promedio": promedio,
            "telefono": telefono,
            "correo": correo,
            "contrasena": contrasena,
            "numero_control": numero_control,
            "grado": grado,
            "especialidad": especialidad,
            "turno": turno
        }
        db.alumnos.update_one({"_id": ObjectId(id)}, {"$set": update})
        flash("Alumno actualizado.", "success")
        return redirect(url_for('admin_alumnos'))
    alumno = to_str_id(alumno)
    return render_template("edit.html", alumno=alumno)

@app.route("/admin/alumnos/delete/<id>", methods=["POST"])
def delete_alumno(id):
    try:
        db.alumnos.delete_one({"_id": ObjectId(id)})
        flash("Alumno eliminado.", "info")
    except Exception as e:
        flash("Error al eliminar: " + str(e), "danger")
    return redirect(url_for('admin_alumnos'))

@app.route("/admin/semestres/<id_alumno>")
def gestion_semestres(id_alumno):
    """Gestión de semestres del alumno"""
    if 'alumno_id' not in session:
        return redirect(url_for('login'))
    
    try:
        alumno = db.alumnos.find_one({"_id": ObjectId(id_alumno)})
        if not alumno:
            flash("Alumno no encontrado", "danger")
            return redirect(url_for('admin_alumnos'))
        
        alumno = to_str_id(alumno)
        alumno = calcular_promedios(alumno)
        
        return render_template("gestion_semestres.html", alumno=alumno)
        
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('admin_alumnos'))

@app.route("/admin/agregar_semestre/<id_alumno>", methods=["GET", "POST"])
def agregar_semestre(id_alumno):
    """Agregar nuevo semestre al alumno"""
    if 'alumno_id' not in session:
        return redirect(url_for('login'))
    
    try:
        alumno = db.alumnos.find_one({"_id": ObjectId(id_alumno)})
        if not alumno:
            flash("Alumno no encontrado", "danger")
            return redirect(url_for('admin_alumnos'))
        
        if request.method == "POST":
            semestre_numero = int(request.form.get("semestre_numero"))
            periodo = request.form.get("periodo")
            
            nuevo_semestre = {
                "semestre_numero": semestre_numero,
                "periodo": periodo,
                "materias": [],
                "promedio_semestre": 0.0
            }
            
            db.alumnos.update_one(
                {"_id": ObjectId(id_alumno)},
                {"$push": {"semestres": nuevo_semestre}}
            )
            
            flash("Semestre agregado correctamente", "success")
            return redirect(url_for('gestion_semestres', id_alumno=id_alumno))
        
        alumno = to_str_id(alumno)
        return render_template("agregar_semestre.html", alumno=alumno)
        
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('admin_alumnos'))
@app.route("/admin/agregar_materia/<id_alumno>/<int:semestre_index>", methods=["GET", "POST"])
def agregar_materia(id_alumno, semestre_index):
    """Agregar materia a un semestre"""
    if 'alumno_id' not in session:
        return redirect(url_for('login'))
    
    try:
        alumno = db.alumnos.find_one({"_id": ObjectId(id_alumno)})
        if not alumno:
            flash("Alumno no encontrado", "danger")
            return redirect(url_for('admin_alumnos'))
        
        if request.method == "POST":
            nombre = request.form.get("nombre")
            profesor = request.form.get("profesor")
            creditos = int(request.form.get("creditos"))
            
            parcial1 = float(request.form.get("parcial1", 0))
            parcial2 = float(request.form.get("parcial2", 0))
            parcial3 = float(request.form.get("parcial3", 0))
            
            parciales = [parcial1, parcial2, parcial3]
            
            calificaciones_validas = [p for p in parciales if p > 0]
            if calificaciones_validas:
                calificacion_final = sum(calificaciones_validas) / len(calificaciones_validas)
                estado = "Aprobada" if calificacion_final >= 6 else "Reprobada"
            else:
                calificacion_final = 0
                estado = "Cursando"
            
            nueva_materia = {
                "nombre": nombre,
                "profesor": profesor,
                "creditos": creditos,
                "parciales": parciales,
                "calificacion_final": round(calificacion_final, 2),
                "estado": estado
            }
            
            db.alumnos.update_one(
                {"_id": ObjectId(id_alumno)},
                {"$push": {f"semestres.{semestre_index}.materias": nueva_materia}}
            )
            
            flash("Materia agregada correctamente", "success")
            return redirect(url_for('gestion_semestres', id_alumno=id_alumno))
        
        alumno = to_str_id(alumno)
        return render_template("agregar_materia.html", 
                             alumno=alumno, 
                             semestre_index=semestre_index,
                             semestre=alumno['semestres'][semestre_index])
        
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('admin_alumnos'))

def crear_datos_prueba():
    """Ruta de emergencia para crear datos de prueba"""
    try:
        alumno_prueba = {
            "nombre": "María García López",
            "edad": 16,
            "grupo": "4AVP", 
            "promedio": 9.2,
            "numero_control": "2024111111",
            "contrasena": "123456",
            "correo": "2024111111@cbtis272.edu.mx",
            "telefono": "555-111-1111",
            "grado": "4to",
            "especialidad": "Programación",
            "turno": "Matutino",
            "semestres": []
        }
        
        existe = db.alumnos.find_one({"numero_control": "2024111111"})
        if not existe:
            db.alumnos.insert_one(alumno_prueba)
            return '''
            <h1>✅ Usuario de prueba creado</h1>
            <p><strong>Número de Control:</strong> 2024111111</p>
            <p><strong>Contraseña:</strong> 123456</p>
            <p><a href="/login">Ir al Login</a></p>
            '''
        else:
            return '''
            <h1>⚠️ Usuario ya existe</h1>
            <p>Usa estas credenciales:</p>
            <p><strong>Número de Control:</strong> 2024111111</p>
            <p><strong>Contraseña:</strong> 123456</p>
            <p><a href="/login">Ir al Login</a></p>
            '''
            
    except Exception as e:
        return f"<h1>❌ Error: {str(e)}</h1>"

@app.route("/ver-usuarios")
def ver_usuarios():
    """Ruta temporal para ver usuarios en la base de datos"""
    usuarios = list(db.alumnos.find({}, {"numero_control": 1, "contrasena": 1, "nombre": 1}))
    resultado = "<h1>Usuarios en la base de datos:</h1><ul>"
    for usuario in usuarios:
        resultado += f"<li>Control: {usuario.get('numero_control', 'N/A')} - Contraseña: {usuario.get('contrasena', 'N/A')} - Nombre: {usuario.get('nombre', 'N/A')}</li>"
    resultado += "</ul>"
    return resultado

@app.route("/ver-templates")
def ver_templates():
    import os
    try:
        templates = os.listdir('templates')
        html = "<h1>📁 Templates en la carpeta:</h1><ul>"
        for template in sorted(templates):
            html += f"<li>{template}</li>"
        html += "</ul>"
        return html
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get('es_admin'):
        flash("Acceso denegado", "danger")
        return redirect(url_for('login'))
    
    total_alumnos = db.alumnos.count_documents({})
    total_semestres = 0
    total_materias = 0
    
    alumnos = db.alumnos.find({})
    for alumno in alumnos:
        if 'semestres' in alumno:
            total_semestres += len(alumno['semestres'])
            for semestre in alumno['semestres']:
                total_materias += len(semestre['materias'])
    
    return render_template("admin_dashboard.html",
                         total_alumnos=total_alumnos,
                         total_semestres=total_semestres,
                         total_materias=total_materias)



if __name__ == "__main__":
    app.run(debug=True)
