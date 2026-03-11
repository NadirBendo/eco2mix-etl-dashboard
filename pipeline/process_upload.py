import sqlite3
import os
import pandas as pd
from datetime import datetime
import dotenv
from google.oauth2.service_account import Credentials
import gspread

# 1 : setup les variables qu'on utilisera pour sqlite et la connexion à la google sheet

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if not dotenv.load_dotenv(os.path.join(BASE_DIR,".env")):
    print("Fichier .env (credentials et ID google sheet) manquant, arret")
    exit()

CRED_PATH = os.path.join(BASE_DIR, os.environ["GCP_TOKEN"])
DB_PATH = os.path.join(BASE_DIR, "../data/raw_data.db")

scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# 2: Connexion au google sheet et récupération du dernier timestamp stocké

creds = Credentials.from_service_account_file(CRED_PATH, scopes=scopes)
client = gspread.authorize(creds)

sheet = client.open_by_key(os.environ["SHEET_ID"]).sheet1

time_col = sheet.col_values(5)  # liste de valeurs
max_date = max(time_col[1:])  # on skip le header

print(f"date max dans la feuille : {max_date}")


# 3: Récupération du dernier timestamp clean dans la base sqlite3

with sqlite3.connect(DB_PATH) as conn:
    curr = conn.cursor()
    curr.execute("PRAGMA table_info(raw_data);")

    cols = [r[1] for r in curr.fetchall()]
    useful_cols = [c for c in cols if c not in ["prevision_j1", "prevision_j"]]

    db_query = f"SELECT {','.join(useful_cols)} FROM raw_data WHERE consommation IS NOT NULL AND datetime(\"{max_date}\") <= date_heure;"
    curr.execute(db_query)
    rows = curr.fetchall()
    
    if len(rows) > 0:
        sheet.append_rows(rows)

    curr.close()
