# eCO2mix - ETL Dashboard Production Électrique Nationale

> Pipeline de données temps réel depuis l'API RTE eCO2mix, avec stockage local SQLite, upload incrémental vers Google Sheets et visualisation via Power BI.

---

## Présentation

Ce projet a pour objectif de collecter, stocker et valoriser les données de production électrique nationale françaises issues de l'API publique [eCO2mix (RTE)](https://odre.opendatasoft.com/explore/dataset/eco2mix-national-tr/).

Le pipeline s'alimente en continu (prévu pour tourner sur Raspberry Pi) et alimente un dashboard Power BI de 4 pages couvrant la consommation, le mix de production, les énergies renouvelables et les échanges transfrontaliers.

---

## Architecture

```
API RTE eCO2mix
      │
      ▼
bootstrap.py ──────────────────────────────────────────────────┐
(extraction initiale, N lignes)                                │
      │                                                        │
      ▼                                                        │
SQLite (raw_data.db)                                           │
[index unique sur date_heure → déduplication garantie]         │
      │                                                        │
      |◄── extract.py                                          │
      │    (màj incrémentale, calcul automatique du delta)     │
      │                                                        │
      ▼                                                        │
process_upload.py ◄────────────────────────────────────────────┘
(upload incrémental Google Sheets, vérification du dernier timestamp)
      │
      ▼
Google Sheets
      │
      ▼
Power BI Dashboard
```

---

## Stack technique

| Composant | Technologie |
|---|---|
| Extraction | Python, `requests` |
| Stockage local | SQLite3 |
| Upload cloud | Google Sheets API (`gspread`) |
| Authentification GCP | Service Account (`google.oauth2`) |
| Visualisation | Power BI Desktop |
| Requêtes analytiques | DAX |
| Transformation données | Power Query (M) |

---

## Description des scripts

### `bootstrap.py`
Extraction initiale des données depuis l'API eCO2mix. Récupère N lignes (paramétrable), les stocke dans SQLite avec un index unique sur `date_heure` pour garantir l'absence de doublons. Ne gère pas l'upload Google Sheets - délégué à `process_upload.py`.

### `extract.py`
Mise à jour incrémentale de la base SQLite. Calcule automatiquement le delta entre le dernier timestamp en base et l'heure actuelle, puis récupère uniquement les lignes manquantes via l'API. Utilise un `INSERT OR REPLACE` avec gestion des conflits sur `date_heure`.

### `process_upload.py`
Upload incrémental vers Google Sheets. Récupère le timestamp maximum déjà présent dans la feuille, interroge SQLite pour les lignes plus récentes, et les appende. Évite tout doublon côté Google Sheets.

---

## Choix techniques notables

**Modèle de données plat (flat model)**
Source unique et homogène : pas de justification à normaliser. Un modèle plat avec une table de dates dédiée est suffisant et plus performant pour ce cas d'usage.

**Déduplication via index unique SQLite**
La clé d'unicité sur `date_heure` garantit l'idempotence des insertions sans logique applicative complexe.

**Dépivotage Power Query pour les échanges**
Les colonnes d'échanges par pays (une colonne par pays dans la source) sont dépivotées en Power Query pour produire une table `pays / valeur` exploitable en dataviz.

---

## Dashboard Power BI - Aperçu

### Page 1 - Vue d'ensemble
KPIs globaux (part nucléaire, consommation moyenne, tonnes CO₂ produites), évolution de la consommation vs production nucléaire, mix de production en donut, échanges aux frontières, profil de consommation journalier moyen.

### Page 2 - Production Électrique
Évolution du mix de production à 100% dans le temps, décomposition journalière moyenne par filière, variation du stock hydraulique STEP.

### Page 3 - Énergies Renouvelables
Répartition Renouvelable / Nucléaire / Fossile, décomposition hydraulique et bioénergies, part éolien terrestre vs offshore, corrélation part renouvelable / intensité carbone (gCO₂/kWh).

### Page 4 - Échanges Transfrontaliers
Top partenaires (import/export/volume), part des échanges dans la consommation nationale, évolution du volume d'échanges, profil journalier par pays, répartition du volume par pays.

---

## Insights principaux

- **Production de nucléaire comparable à 81%** de la consommation nationale 
- **~69% de nucléaire** dans le mix de production sur la période janvier–mars 2026.
- **France exportatrice** : échanges avec les pays voisins à hauteur de ~19% de sa consommation, exportatrice nette vers l'Italie et l'Allemagne/Belgique.
- **Corrélation nette** entre part d'énergies renouvelables et baisse de l'intensité carbone (gCO₂/kWh).
- **Remontée du solaire** visible dès mars 2026 avec l'allongement des journées.
- **Baisse progressive de la consommation** de janvier à mars, cohérente avec la fin de la saison de chauffage.
- **Production de CO2 en baisse** de janvier à mars, cohérente avec l'augmentation de production d'énergie solaire.

---

## Évolutions prévues

- [ ] Automatisation du pipeline sur Raspberry Pi (exécution planifiée via cron)
- [ ] Accumulation des données sur 12 mois pour analyses saisonnières
- [ ] Comparaisons inter-annuelles

---

## Données

Source : [API eCO2mix nationale temps réel](https://odre.opendatasoft.com/explore/dataset/eco2mix-national-tr/)  
Périmètre : France entière  
Granularité : 15 min (consommation) / 30 min (production, échanges)  
Période couverte : janvier 2026 → en cours
