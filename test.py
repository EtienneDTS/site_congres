import os
import sqlite3

def create_connexion(route: str):
    if not os.path.exists(route):
        raise ValueError("Le chemin n'existe pas")
    try:
        connection = sqlite3.connect(route)
    except:
        raise ValueError("Echec de la connexion ")
    return connection

print(create_connexion("./db/bd_congres.db"))
