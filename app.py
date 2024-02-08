from flask import Flask, render_template, redirect, url_for, request
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

db_path = "./db/bd_congres.db"


def create_connexion():

    if not os.path.exists(db_path):
        raise ValueError("Le chemin n'existe pas")
    try:
        connection = sqlite3.connect(db_path)
    except:
        raise ValueError("Echec de la connexion ")
    return connection


def query_db(connexion, query, params=None):
    cursor = connexion.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    result = cursor.fetchall()
    metadata = cursor.description
    return (result, metadata)


@app.route("/")
def menu():
    return render_template("menu.html")


@app.route("/congres")
def congres():
    connexion = create_connexion()
    query = "select * from congres;"
    result = query_db(connexion, query)
    data = result[0]
    metadata = result[1]
    column = [meta[0] for meta in metadata]
    connexion.close()
    return render_template("congres.html", data=data, column=column)


@app.route("/participants")
def participant():
    connexion = create_connexion()
    query = "select * from participants;"
    result = query_db(connexion, query)
    data = result[0]
    metadata = result[1]
    column = [meta[0] for meta in metadata]
    connexion.close()
    return render_template("participant.html", data=data, column=column)


@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    connexion = create_connexion()
    query = "select * from statuts"
    result = query_db(connexion, query)
    status = result[0]
    if request.method == "POST":
        code = request.form.get("cp", "--")
        lastname = request.form.get("lastname")
        firstname = request.form.get("firstname")
        organism = request.form.get("organism")
        address = request.form.get("address", "--")
        city = request.form.get("city")
        country = request.form.get("country")
        email = request.form.get("email")
        status = str(request.form.get("status"))
        connexion = create_connexion()
        query = f"select * from participants where emailpart = ?;"
        params = [email]
        result = query_db(connexion, query, params)
        if len(result[0]) > 0:
            message = "Cet email existe déjà"
            return render_template('inscription.html', message=message)
        date = datetime.now().strftime("%Y-%m-%d")
        query = f"""insert into participants (
            codestatut, 
            nompart, 
            prenompart,
            organismepart,
            cppart,
            adrpart,
            villepart,
            payspart,
            emailpart,
            dtinscription
            ) values (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        params = [status, lastname, firstname, organism, code, address, city, country, email, date]
        result = query_db(connexion, query, params)
        connexion.commit()
        connexion.close()
        return redirect(url_for("confirmation"))
    return render_template('inscription.html', status=status)


@app.route("/confirmation")
def confirmation():
    return render_template('confirmation.html')


@app.route("/consultation", methods=['POST', 'GET'])
def consultation():
    connexion = create_connexion()
    if request.method == "POST":
        email = request.form.get('email')
        query = "select codparticipant from participants where emailpart = ?"
        params = [email]
        result = query_db(connexion, query, params)
        if len(result[0]) < 1:
            message = "Aucun participant de correpond à l'adresse email"
            connexion.close()
            return render_template('consultation.html', message=message)
        codparticipant = result[0][0][0]
        query = """
        select c.codcongres, c.titrecongres, c.numeditioncongres, c.dtdebutcongres, c.dtfincongres, t.nomthematique
        from congres c, inscrire i, participants p, choix_thematiques ct, thematiques t
        where c.codcongres = i.codcongres
        and p.codparticipant = i.codparticipant
        and ct.codparticipant = p.codparticipant
        and ct.codethematique = t.codethematique
        and p.codparticipant = ?"""
        params = [str(codparticipant)]
        result = query_db(connexion, query, params)
        data = result[0]
        column = result[1] # utilise pas car moche demander au prof
        connexion.close()
        congres_list = []
        congres = [[]]
        
        for line in data:
            for word in line[:-1]:
                congres.append(word)
            if congres not in congres_list:
                congres_list.append(congres)
            congres = [[]]
            
        for line in data:
            for congres in congres_list:
                if line[0] == congres[1]:
                    congres[0].append(line[-1])
                
        return render_template('consultation.html', data=congres_list)

    return render_template('consultation.html')


if __name__ == "__main__":
    app.run(debug=True)
