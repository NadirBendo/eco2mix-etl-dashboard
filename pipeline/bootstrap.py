import requests
import sqlite3
import os
import pandas as pd
import numpy as np
import dotenv
from google.oauth2.service_account import Credentials
import gspread

# Variables initiales

n_lignes = 8000 # 1 jour ~ 100 lignes
lignes_req = 80


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../data/raw_data.db")
local_dump = True

dotenv.load_dotenv(os.path.join(BASE_DIR, "../pipeline/.env"))

api_request_string = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records?where=date_heure%20%3C%3D%20now(days%3D-1)&order_by=date_heure%20DESC&limit={}&offset={}"

# requete API 

returns = []
for offset in range(0, n_lignes, lignes_req):
    r = requests.request("GET", api_request_string.format(lignes_req, offset)).json()
    if ("results" not in r) or len(r["results"]) == 0:
        print(f"Limite atteinte (réponse API ou résultat nul)")
        break

    returns.extend(r["results"])


df = pd.DataFrame(returns)

# stockage dans la base de données sqlite3

with sqlite3.connect(DB_PATH) as conn:
    df.to_sql(name="raw_data",con=conn, if_exists="replace", index=False)

    curr = conn.cursor()
    curr.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_date_heure ON raw_data(date_heure);")


    # Stockage des données propres dans le google sheet
    useful_cols = [c for c in df.columns if c not in ["prevision_j1", "prevision_j"]]

    db_query = f"SELECT {','.join(useful_cols)} FROM raw_data WHERE consommation IS NOT NULL;"

    curr.execute(db_query)

    useful_data = curr.fetchall()

    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    creds = Credentials.from_service_account_file(os.path.join(BASE_DIR, os.environ["GCP_TOKEN"]), scopes = scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(os.environ["SHEET_ID"]).sheet1

    sheet.append_row(useful_cols)
    sheet.append_rows(useful_data)

    curr.close()

if local_dump:
    df.to_csv(os.path.join(BASE_DIR, "../data/dump.csv"), index=False)
