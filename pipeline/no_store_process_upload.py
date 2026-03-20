import os
import pandas as pd
import numpy as np # nécessaire pour le tolist final
from datetime import datetime
from requests import request
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
max_date = max([str(t) for t in time_col[1:]])  # on skip le header

print(f"date max dans la feuille : {max_date}")

# 3 (alternatif) : Récuération des données API plus récentes que la date la plus récente du sheets

offset = 0
chunk_size = 20

api_request_string = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records?where=date_heure%20%3E%20\"{}\"%20AND%20consommation%20is%20not%20null&limit={}&offset={}&order_by=date_heure%20ASC"
r = request("GET", api_request_string.format(max_date, chunk_size, offset)).json()

print(api_request_string.format(max_date, chunk_size, offset))

new_lines = []

while "results" in r and len(r["results"]) != 0:
    new_lines.extend(r["results"])
    offset += chunk_size
    r = request("GET", api_request_string.format(max_date, chunk_size, offset)).json()

if len(new_lines) == 0:
    print("erreur lors de la lecture des données depuis l'API")
    exit()

print(len(new_lines))


df = pd.DataFrame(new_lines,index=None)
useful_cols = [c for c in df.columns if c not in ["prevision_j1", "prevision_j"]]

useful_data = df[df["date_heure"] > max_date][useful_cols]

print(useful_cols)
print(min(useful_data["date_heure"]) > max_date)

print(new_lines[0])

sheet.append_rows(useful_data.to_numpy().tolist())

