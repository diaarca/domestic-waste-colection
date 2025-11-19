import json
import pandas as pd


def set_project_root():
    """
    Définit le répertoire courant comme étant le dossier 'DOMESTIC-WASTE-COLECTION'
    en remontant depuis le script courant (ou le cwd si __file__ n'existe pas).
    """
    import os
    from pathlib import Path

    PROJECT_ROOT_NAME = "domestic-waste-colection"
    # Point de départ : fichier courant si possible, sinon cwd (cas notebooks, etc.)
    if "__file__" in globals():
        current_path = Path(__file__).resolve()
    else:
        current_path = Path.cwd().resolve()

    # On parcourt le dossier courant et tous ses parents
    for folder in [current_path] + list(current_path.parents):
        if folder.name == PROJECT_ROOT_NAME:
            os.chdir(folder)
            print(f"Répertoire projet défini sur : {folder}")
            return folder

    # Si on n'a rien trouvé
    raise FileNotFoundError(
        f"Impossible de trouver le dossier projet '{PROJECT_ROOT_NAME}' "
        f"en remontant depuis {current_path}"
    )

def import_duration():
    # Chargement de la matrice de durée depuis un fichier JSON
    with open("Maps\offline map\data\durations.json", "r", encoding="utf-8") as f:
        duration_matrix = json.load(f)

    # Vérification rapide
    n = len(duration_matrix)
    for row in duration_matrix:
        if len(row) != n:
            raise ValueError("La matrice de distances n'est pas carrée.")

    return duration_matrix

def import_distance():
    # Chargement de la matrice de durée depuis un fichier JSON
    with open("Maps\offline map\data\durations.json", "r", encoding="utf-8") as f:
        distance_matrix = json.load(f)

    # Vérification rapide
    n = len(distance_matrix)
    for row in distance_matrix:
        if len(row) != n:
            raise ValueError("La matrice de distances n'est pas carrée.")

    return distance_matrix

def import_prediction():
    prediction_df = pd.read_csv("Data\Linear Prediction.csv", sep=";")
    prediction_df = prediction_df[["Identifier","Daily (Kg)", "Daily (L)"]]
    res = (prediction_df.groupby("Identifier")[["Daily (Kg)", "Daily (L)"]].agg("first"))  # ou .agg({"Daily (Kg)": "first", "Daily (L)": "first"})
    Daily_kg = list(res["Daily (Kg)"])
    Daily_L = list(res["Daily (L)"])
    return Daily_kg, Daily_L

class DataProblem :
    def __init__(self):
        self.duration_matrix = import_duration()
        self.distance_matrix = import_distance()
        self.daily_kg, self.daily_L = import_prediction()
        

if __name__ == "__main__" :
    # Appel au démarrage du programme
    PROJECT_ROOT = set_project_root()
    data = DataProblem()



