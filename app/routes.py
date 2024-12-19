import csv
import os
import requests
from flask import render_template, request, jsonify
from app import app
import subprocess
import time
import requests
from threading import Thread
from flask import Flask, render_template, request

# URL d'Elasticsearch
ELASTICSEARCH_URL = "http://localhost:9200"

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    message = None
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Créer le dossier de destination si nécessaire
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Définir le chemin complet où sauvegarder le fichier
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            
            # Sauvegarder le fichier
            file.save(file_path)
            
            # Exécuter Logstash sur le fichier téléchargé
            execute_logstash(file_path)
        # if file and allowed_file(file.filename):  # Ajoutez une validation du type de fichier
        #   file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        #   file.save(file_path)
        #   execute_logstash(file_path)
        # else:
        #     message = "Fichier invalide. Veuillez télécharger un fichier autorisé."

            message = f"Fichier {file.filename} téléchargé avec succès et Logstash exécuté !"
    
    return render_template('upload.html', message=message)


def execute_logstash(file_path):
    """
    Exécute Logstash sur le fichier téléchargé en utilisant la commande Logstash configurée
    """
    logstash_cmd = [
         "/usr/share/logstash/bin/logstash", "-f", "/home/vboxuser/etc/logstash/conf.d/inventaire.conf", 
        "--input-file", file_path  # Assurez-vous que Logstash accepte ce paramètre
    ]
    subprocess.Popen(logstash_cmd)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    visualizations = get_visualizations()
    return render_template('dashboard.html', visualizations=visualizations)


# Fonction pour obtenir les visualisations et leurs URLs
def get_visualizations():
    return [
        {"title": "produit", "url": "http://localhost:5601/goto/c3d1f320-ae39-11ef-98eb-21fea7a6d62c"},
        {"title": "Monthly Revenue", "url": "http://localhost:5601/goto/3e233420-ae3c-11ef-98eb-21fea7a6d62d"},
        {"title": "people", "url": "http://localhost:5601/goto/6a5f7b30-ae4a-11ef-ac1b-47ecae5d8ab1"}
    ]





# @app.route('/produits', methods=['GET'])
# def liste_produits():
#     """
#     Récupère tous les noms de produits stockés dans Elasticsearch et applique un filtrage si nécessaire.
#     """
#     filtre = request.args.get('filtre', '').lower()  # Récupérer le terme de filtrage

#     try:
#         # Récupère tous les produits indexés depuis Elasticsearch
#         response = requests.get(f"{ELASTICSEARCH_URL}/haider-2024.12.10.08.04.56/_search?size=1000")
#         produits = response.json().get('hits', {}).get('hits', [])

#         # Extraire les noms de produits
#         # noms_produits = [produit['_source']['Nom du produit'] for produit in produits]
#         noms_produits = [produit['_source'].get('Nom du produit', 'Nom inconnu') for produit in produits]


#         # Appliquer le filtrage si un terme est donné
#         if filtre:
#             produits_filtrés = [nom for nom in noms_produits if filtre in nom.lower()]
#         else:
#             produits_filtrés = noms_produits

#     except Exception as e:
#         produits_filtrés = {"error": f"Erreur lors de la récupération des produits : {e}"}

#     # Passer les produits filtrés au template
#     return render_template('liste_produits.html', noms_produits=produits_filtrés)

@app.route('/produits', methods=['GET'])
def liste_produits():
    """
    Récupère tous les noms de produits stockés dans Elasticsearch et affiche uniquement les chaînes de caractères.
    """
    try:
        # Récupérer tous les produits indexés depuis Elasticsearch
        response = requests.get(f"{ELASTICSEARCH_URL}/haider-2024.12.10.08.04.56/_search?size=1000")
        produits = response.json().get('hits', {}).get('hits', [])

        # Extraire les noms de produits et filtrer uniquement les chaînes de caractères contenant des lettres
        noms_produits = [
            produit['_source'].get('Nom du produit', 'Nom inconnu')
            for produit in produits
            if isinstance(produit['_source'].get('Nom du produit'), str) and any(char.isalpha() for char in produit['_source']['Nom du produit'])
        ]

        # Vérifier si un filtre est passé en paramètre GET
        filtre = request.args.get('filtre', '').lower()
        if filtre:
            produits_filtrés = [nom for nom in noms_produits if filtre in nom.lower()]
        else:
            produits_filtrés = noms_produits

    except Exception as e:
        produits_filtrés = {"error": f"Erreur lors de la récupération des produits : {e}"}

    # Passer les produits filtrés au template
    return render_template('liste_produits.html', noms_produits=produits_filtrés)

@app.route('/produit/<nom>', methods=['GET'])
def details_produit(nom):
    """
    Affiche les détails d’un produit spécifique.
    """
    try:
        # Requête pour chercher le produit par son nom
        response = requests.get(f"{ELASTICSEARCH_URL}/haider-2024.12.10.08.04.56/_search?q=Nom du produit:{nom}")
        produits = response.json().get('hits', {}).get('hits', [])
        
        # Récupère les détails du produit
        # details = [produit['_source'] for produit in produits]
        details = [produit['_source'] for produit in produits if '_source' in produit and produit['_source'].get('Nom du produit') == nom]


    except Exception as e:
        details = {"error": f"Erreur lors de la récupération des détails : {e}"}
    
    return render_template('details_produit.html', nom=nom, details=details)

def create_credit_csv(file_path):
    """
    Extrait uniquement les noms des produits du fichier téléchargé et les sauvegarde dans credit.csv.
    """
    try:
        # Définir le chemin de sortie pour credit.csv
        credit_csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'credit.csv')

        with open(file_path, 'r') as input_file, open(credit_csv_path, 'w', newline='') as output_file:
            reader = csv.reader(input_file)
            writer = csv.writer(output_file)
            
            # Filtrer et écrire uniquement les noms des produits
            for row in reader:
                # Boucler sur chaque colonne et vérifier si elle contient du texte
                for cell in row:
                    # Ajouter la ligne uniquement si elle contient des lettres (un nom de produit)
                    if any(char.isalpha() for char in cell):  # Vérifie s'il y a une lettre
                        writer.writerow([cell])
        
        return credit_csv_path
    except Exception as e:
        print(f"Erreur lors de la création de credit.csv : {e}")
        return None


@app.route('/liste_produits', methods=['GET'])
def liste_produits_filtered():
    """
    Récupère tous les noms de produits stockés dans Elasticsearch et applique un filtrage si nécessaire.
    """
    filtre = request.args.get('filtre', '').lower()  # Récupérer le terme de filtrage

    try:
        # Récupère tous les produits indexés depuis Elasticsearch
        response = requests.get(f"{ELASTICSEARCH_URL}/haider-2024.12.10.08.04.56/_search?size=1000")
        produits = response.json().get('hits', {}).get('hits', [])

        # Extraire les noms de produits
        noms_produits = {produit['_source']['Nom du produit'] for produit in produits}

        # Appliquer le filtrage si un terme est donné
        if filtre:
            produits_filtrés = [nom for nom in noms_produits if filtre in nom.lower()]
        else:
            produits_filtrés = noms_produits

    except Exception as e:
        produits_filtrés = {"error": f"Erreur lors de la récupération des produits : {e}"}

    # Passer les produits filtrés au template
    return render_template('liste_produits.html', noms_produits=produits_filtrés)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')  # Récupère la requête de recherche
    response = requests.get(f"{ELASTICSEARCH_URL}/dataset_index/_search?q={query}")
    return response.json()


def monitor_elasticsearch():
    """
    Surveille Elasticsearch pour détecter de nouveaux indices
    """
    global existing_indices
    while True:
        try:
            # Récupère la liste des indices actuels
            response = requests.get(f"{ELASTICSEARCH_URL}/_cat/indices?format=json")
            indices = {index['index'] for index in response.json()}
            
            # Vérifie si de nouveaux indices ont été ajoutés
            new_indices = indices - existing_indices
            if new_indices:
                print(f"Nouveaux indices détectés : {new_indices}")
                existing_indices = indices
                
                # Redémarrer Logstash
                restart_logstash()
            
        except Exception as e:
            print(f"Erreur lors de la surveillance d'Elasticsearch : {e}")
        
        # Attendre quelques minutes avant de revérifier
        time.sleep(300)  # 5 minutes

def restart_logstash():
    """
    Redémarre Logstash via systemctl
    """
    try:
        subprocess.run(["sudo", "systemctl", "restart", "logstash"], check=True)
        print("Logstash redémarré avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du redémarrage de Logstash : {e}")