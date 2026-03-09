import requests
import sqlite3
import os
import pandas as pd
from datetime import datetime

# Variables d'actualisation de la base de données

n_lignes = 0 # à recalculer par la suite
lignes_req = 20

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../data/raw_data.db")

api_request_string = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records?where=date_heure%20%3C%3D%20now()&order_by=date_heure%20desc&limit={}&offset={}"
with sqlite3.connect(DB_PATH) as conn:
    curr = conn.cursor()

    # On commence par voir dans la base de données existante quelle est la derniere acutalisation effectuée
    res = curr.execute("SELECT date, heure FROM raw_data WHERE consommation IS NOT NULL ORDER BY date_heure DESC LIMIT 1;")
    date, heure = res.fetchone()
    recent = datetime.strptime(date + ' ' + heure, '%Y-%m-%d %H:%M')
    print(f"Heure actuelle {datetime.now()}")
    print(f"Heure la plus récente dans la DB : {datetime.strptime(date + ' ' + heure, '%Y-%m-%d %H:%M')}")

    # calcul du nombre d'heures a rattraper
    diff = datetime.now() - recent
    heures = int(diff.total_seconds()) // 3600
    n_lignes = ((heures + 1) * 4) # estimation généreuse pour éviter les lignes a consommation nulle

    print(f"différence entre les 2 timestamps : {diff}, nombre d'heures : {diff.total_seconds() // 3600}")

    if (heures == 0):
        print("Rien a importer, on a fini")
        curr.close()
        exit()

    # requetes API 
    returns = []
    for offset in range(0, n_lignes, lignes_req):
        r = requests.request("GET", api_request_string.format(lignes_req, offset)).json()
        returns.extend(r["results"])

    cols = list(pd.DataFrame(returns).columns)
    cols_str = ", ".join(cols)
    updates = " ".join([f"{c} = excluded.{c}," for c in cols])[:-1]
    placeholder = "("+ ("?, " * len(cols))[:-2] + ")"

    query = f"INSERT INTO raw_data({cols_str}) VALUES {placeholder} ON CONFLICT(date_heure) DO UPDATE SET {updates}"

    for record in returns:
        curr.execute(query, tuple(record.values()))

    curr.close()

