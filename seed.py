from pymongo import MongoClient
import os
from datetime import datetime

MONGO_URI = "mongodb+srv://rosaldoantoniocbtis_db_user:tCQ5641BploPNZLM@cbtis.nt3myx6.mongodb.net/escuela?retryWrites=true&w=majority&appName=CBTIS"
client = MongoClient(MONGO_URI)
db = client.get_default_database()

db.alumnos.delete_many({})

alumnos = [
    {
        "nombre": "Ana López García",
        "edad": 17,
        "grupo": "6AVP",
        "numero_control": "2024123456",
        "contrasena": "123456",
        "correo": "2024123456@cbtis272.edu.mx",
        "telefono": "555-123-4567",
        "grado": "6to",
        "especialidad": "Programación",
        "turno": "Matutino",
        "fecha_inscripcion": datetime(2022, 8, 15),
        "semestres": [
            {
                "semestre_numero": 1,
                "periodo": "AGO 2022 - ENE 2023",
                "materias": [
                    {
                        "nombre": "Matemáticas I",
                        "profesor": "Dr. Carlos Rodríguez",
                        "creditos": 5,
                        "parciales": [8, 7, 9, 8],
                        "calificacion_final": 8,
                        "estado": "Aprobada"
                    },
                    {
                        "nombre": "Química I",
                        "profesor": "Dra. María González",
                        "creditos": 4,
                        "parciales": [7, 6, 8, 7],
                        "calificacion_final": 7,
                        "estado": "Aprobada"
                    },
                    {
                        "nombre": "Inglés I",
                        "profesor": "Mtro. Roberto Silva",
                        "creditos": 3,
                        "parciales": [5, 6, 5, 4],
                        "calificacion_final": 5,
                        "estado": "Reprobada"
                    }
                ],
                "promedio_semestre": 6.7
            },
            {
                "semestre_numero": 2,
                "periodo": "FEB 2023 - JUL 2023",
                "materias": [
                    {
                        "nombre": "Matemáticas II",
                        "profesor": "Dr. Carlos Rodríguez",
                        "creditos": 5,
                        "parciales": [9, 8, 9, 10],
                        "calificacion_final": 9,
                        "estado": "Aprobada"
                    },
                    {
                        "nombre": "Programación I",
                        "profesor": "Ing. Laura Martínez",
                        "creditos": 5,
                        "parciales": [10, 9, 10, 10],
                        "calificacion_final": 10,
                        "estado": "Aprobada"
                    },
                    {
                        "nombre": "Física I",
                        "profesor": "Dra. Patricia López",
                        "creditos": 4,
                        "parciales": [7, 8, 7, 8],
                        "calificacion_final": 7,
                        "estado": "Aprobada"
                    }
                ],
                "promedio_semestre": 8.7
            }
        ]
    }
]

db.alumnos.insert_many(alumnos)
print("✅ Seed completado con nueva estructura de calificaciones!")
