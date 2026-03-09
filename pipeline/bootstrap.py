import requests
import sqlite3
import os
import pandas as pd

# Variables initiales

n_lignes = 1500 # 1 jour ~ 100 lignes
lignes_req = 20

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../data/raw_data.db")
local_dump = True

api_request_string = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records?where=date_heure%20%3C%3D%20now(days%3D-1)&order_by=date_heure%20DESC&limit={}&offset={}"

# requete API 

returns = []
for offset in range(0, n_lignes, lignes_req):
    r = requests.request("GET", api_request_string.format(lignes_req, offset)).json()
    returns.extend(r["results"])


df = pd.DataFrame(returns)

# stockage dans la base de données sqlite3

with sqlite3.connect(DB_PATH) as conn:
    df.to_sql(name="raw_data",con=conn, if_exists="replace", index=False)

    curr = conn.cursor()
    curr.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_date_heure ON raw_data(date_heure);")
    curr.close()


if local_dump:
    df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/dump.csv"))
