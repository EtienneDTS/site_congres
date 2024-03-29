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
    print(result)
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


@app.route("/inscription-np", methods=["GET", "POST"])
def inscription_np():
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
        # permet de s'assurer que l'email n'est pas déja dans la db
        connexion = create_connexion()
        query = f"select * from participants where emailpart = ?;"
        params = [email]
        result = query_db(connexion, query, params)
        if len(result[0]) > 0:
            message = "Cet email existe déjà"
            return render_template('inscription.html', message=message, status=status)
        status = str(request.form.get("status"))
        # La date d'inscription n'est pas ajoutée automatiquement par la base de donnée si on ne l'ajoute nous même
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
            "{status}", "{lastname}", "{firstname}", "{organism}", "{code}", "{address}", "{city}", "{country}", "{email}", "{date}");"""
        query_db(connexion, query)
        connexion.commit()
        connexion.close()
        return redirect(url_for("confirmation", email=email))
    return render_template('inscription_np.html', status=status)


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
        connexion = create_connexion()
        query = f"select * from participants where emailpart = ?;"
        params = [email]
        result = query_db(connexion, query, params)
        # permet de s'assurer que l'email n'est pas déja dans la db
        if len(result[0]) > 0:
            message = "Cet email existe déjà"
            return render_template('inscription.html', message=message, status=status)
        status = str(request.form.get("status"))
        date = datetime.now().strftime("%Y-%m-%d")
        query = """insert into participants (
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
        query_db(connexion, query, params)
        connexion.commit()
        connexion.close()
        return redirect(url_for("confirmation", email=email))
    return render_template('inscription.html', status=status)


@app.route("/confirmation/<string:email>")
def confirmation(email):
    return render_template('confirmation.html', email=email)

# Fait sur la meme page car plus "user friendly" les consignes sont respectées


@app.route("/consultation", methods=['POST', 'GET'])
def consultation():
    connexion = create_connexion()
    if request.method == "POST":
        email = request.form.get('email')
        query = "select codparticipant from participants where emailpart = ?"
        params = [email]
        result = query_db(connexion, query, params)
        # s'assure que l'email existe dans la db dans le cas contraire renvoie un message d'erreur visible dans la page
        if len(result[0]) < 1:
            message = "Aucun participant de correspond à l'adresse email"
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
        connexion.close()
        # permet d'avoir une liste de congres et une sous liste de thématique liée à chaque congres
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
    # viens dans l'ordre après le récapitulatif
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
    context["price"] = request.form.getlist("price")
    start_date = datetime.strptime(context["start"], "%Y-%m-%d").date()
    end_date = datetime.strptime(context["end"], "%Y-%m-%d").date()
    context["themes"] = request.form.getlist("theme")
    context["activities"] = request.form.getlist("activity")
    today = datetime.now().date()
    # étapes de prévention des erreurs avant création qui affiche un message d'erreur sur la page création si nécessaire dans ce cas rien ne sera créé
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
    # création du congrès
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
    # récupération du code du congrès pour les étapes suivantes
    # peut être fait avec SELECT last_insert_rowid() mais cela est équivalent car il ne peut y avoir qu'un seul congrès avec le même titre et le même numéro d'édition comme cela est vérifié plus haut
    query = """
    select c.codcongres 
    from congres c
    where c.titrecongres = ?
    and c.numeditioncongres = ?;
    """
    params = (context["title"], context["num"])
    result = query_db(connexion, query, params)
    codcongres = result[0][0][0]
    # ajout des activités et des thématiques
    if len(context["activities"]) > 0:
        for code in context["activities"]:
            query = """
            insert into proposer (codeactivite, codcongres)
            values (?, ?);
            """
            params = (code, codcongres)
            query_db(connexion, query, params)

    if len(context["themes"]) > 0:
        for code in context["themes"]:
            query = """
            insert into traiter (codcongres, codethematique)
            values (?, ?);
            """
            params = (codcongres, code)
            query_db(connexion, query, params)

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
    codestatut = 1
    for price in context["price"]:
        query = "insert into tarifs (codestatut, codcongres, montanttarif) values (?, ?, ?);"
        params = (codestatut, codcongres, int(price))
        query_db(connexion, query, params)
        codestatut += 1
    connexion.commit()
    connexion.close()

    return render_template("recapitulatif.html", **context)


@app.route("/logout")
def logout():
    session.pop('participant', None)
    return redirect(url_for('menu'))

# Dans l'ordre viens après enregistrer qui est en dessous
@app.route("/choisir", methods=["GET"])
def choisir():
    if not session.get("participant"):
        return redirect(url_for("enregistrer"))
    num = session["selection"]["codcongres"]
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
    if "selection" in session:
        session.pop("selection")
    date = datetime.now().strftime("%Y-%m-%d")
    query = f"select * from congres where dtdebutcongres >= {date};"
    connexion = create_connexion()
    result = query_db(connexion, query)
    congres = result[0]
    if request.method == "POST":
        email = request.form.get("email")
        codcongres = int(request.form.get("congres"))
        query = "select * from participants where emailpart = ?;"
        params = [email]
        result = query_db(connexion, query, params)
        if len(result[0]) < 1:
            message = "Aucun participant ne correspond à l'adresse email"
            connexion.close()
            return render_template('enregistrer.html', congres=congres, message=message)
        session["selection"] = {"codcongres": codcongres}
        query = "select nomstatut from statuts where codestatut = ?;"
        params = [result[0][0][1]]
        status = query_db(connexion, query, params)[0][0][0]
        session["participant"] = {}
        session["participant"]["codparticipant"] = result[0][0][0]
        session["participant"]["statut"] = status
        session["participant"]["codestatut"] = result[0][0][1]
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
        return redirect(url_for("choisir"))

    return render_template('enregistrer.html', congres=congres)


@app.route('/montant', methods=["POST"])
def montant():
    # fonction qui prend en compte le tarifs congrès qui ont un prix qui varies selon le statut mais aussi du prix des activités
    all_price = []
    codestatut = session["participant"]["codestatut"]
    connexion = create_connexion()
    codcongres = session["selection"]["codcongres"]
    session["selection"]["activities"] = list(map(int,request.form.getlist("activity")))
    session["selection"]["themes"] = list(map(int,request.form.getlist("theme")))
    session.modified = True
    activities = session["selection"]["activities"]
    themes = session["selection"]["themes"]
    
    query = "select * from congres where codcongres = ?;"
    params = [codcongres]
    result = query_db(connexion, query, params)
    congres = result[0][0]

    if len(activities) > 0:
        activities = tuple(activities)
        if len(activities) == 1:
            activities = str(activities).replace(",", "")
        else:
            activities = str(activities)
        query = f"select * from activites where codeactivite in {activities};"
        result = query_db(connexion, query)
        activities = result[0]
    if len(themes) > 0:
        themes = tuple(themes)
        if len(themes) == 1:
            themes = str(themes).replace(",", "")
        else:
            themes = str(themes)
        query = f"select * from thematiques where codethematique in {themes};"
        result = query_db(connexion, query)
        themes = result[0]
    query = "select montanttarif from tarifs where codcongres = ? and codestatut = ?;"
    params = [codcongres, codestatut]
    result = query_db(connexion, query, params)
    price = result[0][0][0]
    all_price.append(int(price))
    for activity in activities:
        all_price.append(int(activity[2]))
    total = sum(all_price)
    connexion.close()
    return render_template('montant.html', congres=congres, activities=activities, themes=themes, total=total)


@app.route('/validation', methods=["POST"])
def validation():
    connexion = create_connexion()
    codcongres = session["selection"]["codcongres"]
    query = "insert into inscrire (codparticipant, codcongres) values (?, ?);"
    params = [session["participant"]["codparticipant"], codcongres]
    query_db(connexion, query, params)
    activities = session["selection"]["activities"]
    themes = session["selection"]["themes"]
    price = request.form.get("price")

    query = "select * from congres where codcongres = ?;"
    params = [codcongres]
    result = query_db(connexion, query, params)
    congres = result[0][0]

    if len(activities) > 0:
        for activity in activities:
            query = "insert into choix_activites (codeactivite, codparticipant, codcongres) values (?, ?, ?);"
            params = [activity, session["participant"]
                      ["codparticipant"], codcongres]
            query_db(connexion, query, params)
        activities = tuple(activities)
        if len(activities) == 1:
            activities = str(activities).replace(",", "")
        else:
            activities = str(activities)
        query = f"select * from activites where codeactivite in {activities};"
        result = query_db(connexion, query)
        activities = result[0]

    if len(themes) > 0:
        for theme in themes:
            query = "insert into choix_thematiques (codethematique, codparticipant, codcongres) values (?, ?, ?);"
            params = [theme, session["participant"]
                      ["codparticipant"], codcongres]
            query_db(connexion, query, params)
        themes = tuple(themes)
        if len(themes) == 1:
            themes = str(themes).replace(",", "")
        else:
            themes = str(themes)
        query = f"select * from thematiques where codethematique in {themes};"
        result = query_db(connexion, query)
        themes = result[0]
    connexion.commit()
    connexion.close()
    session.pop("selection")
    return render_template('validation.html', congres=congres, activities=activities, themes=themes, price=price)


if __name__ == "__main__":
    app.run(debug=True)
