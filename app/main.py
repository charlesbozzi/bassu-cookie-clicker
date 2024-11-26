# app/main.py
import os
import sys
import time
from flask import Flask, request, render_template, redirect, url_for, jsonify
import redis
import psycopg

app = Flask(__name__)

# Configuration Redis
redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = int(os.getenv('REDIS_PORT', 6379))
r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

# Configuration PostgreSQL
db_user = os.getenv('POSTGRES_USER', 'postgres')
db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
db_host = os.getenv('POSTGRES_HOST', 'db')
db_port = os.getenv('POSTGRES_PORT', 5432)
db_name = os.getenv('POSTGRES_DB', 'cookie_clicker')

connection = psycopg.connect("dbname="+db_name+" user="+db_user+" password="+db_password+" host="+db_host+" port="+str(db_port)+" connect_timeout=10")
cursor = connection.cursor()

# Création de la table dans PostgreSQL

sql_context ="""
CREATE TABLE IF NOT EXISTS clicks (
  id SERIAL PRIMARY KEY,
  username VARCHAR NOT NULL,
  clicks integer NOT NULL DEFAULT '0'
);
"""
cursor.execute(sql_context)
connection.commit()

# Index
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form["username"]
        return redirect(url_for("game", username=username))
    currentPlayers = r.keys('*')
    return render_template("index.html", currentplayers=currentPlayers)

# Jeu
@app.route("/game/<username>")
def game(username):
    clicksCount = load_clicks(username)
    return render_template("game.html", username=username, clickscount=clicksCount)

# "API" pour enregistrer un clic
@app.route("/click/<username>", methods=["POST"])
def click(username):
    clicksCount = load_clicks(username)
    r.incr(f"{username}")
    #bitbanging some json because i can
    return "{\"clicks\": "+str(clicksCount+1)+"}"

# Leaderboard
@app.route("/leaderboard")
def leaderboard():
    sql_context ="SELECT username, clicks FROM clicks ORDER BY clicks DESC LIMIT 5;"
    cursor.execute(sql_context)
    leaderboard = cursor.fetchall()
    return render_template("leaderboard.html", leaderboard=leaderboard)


# Enregistrer les clics dans Postgres
def save_clicks():
    """Sauvegarde les clics de Redis vers PostgreSQL."""
    for key in r.keys("*"):
        clicksCount = int(r.get(key))

        # Vérifier si l'utilisateur a déjà un enregistrement dans Postgre
        sql_context ="SELECT clicks FROM clicks WHERE username LIKE '"+key+"' LIMIT 1;"
        cursor.execute(sql_context) # key c'est username
        result = cursor.fetchone()

        if result:
            # Si le contenu de Redis est le même que celui de Postgres alors on supprime le joueur de redis car le score n'a pas été modifié depuis la derniere sauvegarde vers pg
            if (result[0] ==  r.get(key)): # si la valeur de Redis est la meme que Postgres
                print("Removing",key,"from Redis")
                r.delete(key)
            else: # sinon
                print("Updating",key,"into Postgres")
                sql_context ="UPDATE clicks SET clicks = "+str(clicksCount)+" WHERE username LIKE '"+key+"';"
                cursor.execute(sql_context) # key c'est username
        else:
            print("Pushing",key,"into Postgres")
            # Insertion d'un nouvel enregistrement pour cet utilisateur
            sql_context = "INSERT INTO clicks (username, clicks) VALUES ('"+key+"', "+str(clicksCount)+");"
            cursor.execute(sql_context) # key c'est username
    connection.commit()

def load_clicks(username):
    """Charge les clics depuis Postgres dans Redis si l'utilisateur n'est pas déjà dedans."""
    # Vérifier si l'utilisateur existe déjà dans Redis
    if not r.exists(f"{username}"):
        print("Loading",username,"from Postgres")
        # Si l'utilisateur n'est pas dans Redis, on charge ses clics depuis Postgres
        sql_context ="SELECT clicks FROM clicks WHERE username LIKE '"+username+"' LIMIT 1;"
        cursor.execute(sql_context)
        result = cursor.fetchone()
        # si on a bien un résultat c'est que l'utilisateur existe, sinon il faut le créer
        # cela est fait par la fonction save_click
        clicksCount = result[0] if result else 0
        # Charger le score dans Redis
        r.set(f"{username}", clicksCount)
    else:
        print("Loading",username,"from Redis")
        clicksCount = r.get(f"{username}")
    return int(clicksCount)

with app.app_context():
    def run_job():
        while True:
            print("Moving old Redis data to Postgres")
            save_clicks()
            time.sleep(5*60)
    from threading import Thread
    thread = Thread(target=run_job)
    thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
