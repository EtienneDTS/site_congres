from flask import Flask, render_template, redirect, url_for, request
import sqlite3
import os
from datetime import datetime
from flask import session
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

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
        params = (status, lastname, firstname, organism,
                  code, address, city, country, email, date)
        result = query_db(connexion, query, params)
        connexion.commit()
        connexion.close()
        return redirect(url_for("confirmation"))
    return render_template('inscription.html', status=status)


@app.route("/confirmation/<string:email>")
def confirmation(email):
    return render_template('confirmation.html', email=email)


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
        column = result[1]  # utilise pas car moche demander au prof
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


@app.route("/creation")
def creation():
    message = request.args.get("message")
    connexion = create_connexion()
    query = "select * from thematiques"
    result = query_db(connexion, query)
    themes = result[0]
    query = "select * from activites"
    result = query_db(connexion, query)
    activities = result[0]
    connexion.close()
    if message:
        return render_template("creation.html", themes=themes, activities=activities, message=message)
    return render_template("creation.html", themes=themes, activities=activities)


@app.route("/recapitulatif", methods=["POST"])
def recapitulatif():
    context = {}
    context["title"] = request.form.get("title")
    context["num"] = int(request.form.get("num"))
    context["url"] = request.form.get("url")
    context["start"] = request.form.get("start")
    context["end"] = request.form.get("end")
    start_date = datetime.strptime(context["start"], "%Y-%m-%d").date()
    end_date = datetime.strptime(context["end"], "%Y-%m-%d").date()
    context["themes"] = request.form.getlist("theme")
    context["activities"] = request.form.getlist("activity")
    today = datetime.now().date()

    if start_date > end_date:
        return redirect(url_for("creation", message="La date de début doit être inférieure à la date de fin"))
    if start_date < today:
        return redirect(url_for("creation", message="La date de début doit être supérieure à la date d'aujourd'hui"))

    connexion = create_connexion()

    query = """
    select c.codcongres 
    from congres c
    where c.titrecongres = ?
    and c.numeditioncongres = ?;
    """
    params = (context["title"], context["num"])
    result = query_db(connexion, query, params)
    if len(result[0]) > 0:
        return redirect(url_for("creation", message=f"Le congrès {context['title']} edition {context['num']} existe déjà"))

    query = """insert into congres (
        titrecongres,
        numeditioncongres,
        dtdebutcongres,
        dtfincongres,
        urlsitewebcongres
    ) values (?, ?, ?, ?, ?);
    """
    params = (context["title"], context["num"],
              context["start"], context["end"], context["url"])
    query_db(connexion, query, params)
    connexion.commit()
    query = """
    select c.codcongres 
    from congres c
    where c.titrecongres = ?
    and c.numeditioncongres = ?;
    """
    params = (context["title"], context["num"])
    result = query_db(connexion, query, params)
    codcongres = result[0][0][0]

    if len(context["activities"]) > 0:
        for code in context["activities"]:
            query = """
            insert into proposer (codeactivite, codcongres)
            values (?, ?)
            """
            params = (code, codcongres)
            query_db(connexion, query, params)

    if len(context["themes"]) > 0:
        for code in context["themes"]:
            query = """
            insert into traiter (codcongres, codethematique)
            values (?, ?)
            """
            params = (codcongres, code)
            query_db(connexion, query, params)
    connexion.commit()

    query = f"""
    select t.nomthematique 
    from thematiques t
    where t.codethematique in ({", ".join(context['themes'])});"""
    context["themes"] = query_db(connexion, query)[0]
    query = f"""
    select a.nomactivite
    from activites a
    where a.codeactivite in ({", ".join(context['activities'])});"""
    context["activities"] = query_db(connexion, query)[0]
    context["start"] = datetime.strptime(
        context["start"], "%Y-%m-%d").strftime("%d/%m/%Y")
    context["end"] = datetime.strptime(
        context["end"], "%Y-%m-%d").strftime("%d/%m/%Y")
    connexion.close()

    return render_template("recapitulatif.html", **context)


@app.route("/logout")
def logout():
    session.pop('participant', None)
    return redirect(url_for('menu'))


@app.route("/choisir/<int:num>", methods=["GET"])
def choisir(num):
    if not session.get("participant"):
        return redirect(url_for("enregistrer"))
    num = int(num)
    connexion = create_connexion()
    query = """
    select distinct t.codethematique, t.nomthematique
    from thematiques t, traiter tr, congres c
    where t.codethematique = tr.codethematique
    and c.codcongres = tr.codcongres
    and c.codcongres = ?
    """
    params = [num]
    themes = query_db(connexion, query, params)[0]
    query = """
    select distinct a.codeactivite, a.nomactivite
    from activites a, proposer p, congres c
    where a.codeactivite = p.codeactivite
    and c.codcongres = p.codcongres
    and c.codcongres = ?
    """
    params = [num]
    activities = query_db(connexion, query, params)[0]
    
    query = "select c.titrecongres, c.numeditioncongres, c.codcongres from congres c where c.codcongres = ?;"
    params = [num]
    congres = query_db(connexion, query, params)[0][0]
    connexion.close()
    return render_template("choisir.html", themes=themes, activities=activities, congres=congres)


@app.route("/enregistrer", methods=["GET", "POST"])
def enregistrer():
    connexion = create_connexion()
    query = "select * from congres;"
    result = query_db(connexion, query)
    congres = result[0]
    if request.method == "POST":
        email = request.form.get("email")
        codcongres = int(request.form.get("congres"))
        print(codcongres)
        query = "select * from participants where emailpart = ?;"
        params = [email]
        result = query_db(connexion, query, params)
        if len(result[0]) < 1:
            message = "Aucun participant ne correspond à l'adresse email"
            connexion.close()
            return render_template('enregistrer.html', congres=congres, message=message)
        query = "select nomstatut from statuts where codestatut = ?;"
        params = [result[0][0][1]]
        status = query_db(connexion, query, params)[0][0][0]
        session["participant"] = {}
        session["participant"]["codparticipant"] = result[0][0][0]
        session["participant"]["codestatut"] = status
        session["participant"]["nompart"] = result[0][0][2]
        session["participant"]["prenompart"] = result[0][0][3]
        session["participant"]["organismepart"] = result[0][0][4]
        session["participant"]["cppart"] = result[0][0][5]
        session["participant"]["adrpart"] = result[0][0][6]
        session["participant"]["villepart"] = result[0][0][7]
        session["participant"]["payspart"] = result[0][0][8]
        session["participant"]["emailpart"] = result[0][0][9]
        session["participant"]["dtinscription"] = result[0][0][10]
        connexion.close()
        return redirect(url_for("choisir", num=codcongres))

    return render_template('enregistrer.html', congres=congres)


if __name__ == "__main__":
    app.run(debug=True)
