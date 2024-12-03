import os
import requests
from flask import render_template, request, jsonify
from app import app
import subprocess

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
            
            message = f"Fichier {file.filename} téléchargé avec succès et Logstash exécuté !"
    
    return render_template('upload.html', message=message)


def execute_logstash(file_path):
    """
    Exécute Logstash sur le fichier téléchargé en utilisant la commande Logstash configurée
    """
    logstash_cmd = [
        "/usr/share/logstash/bin/logstash", "-f", "/home/vboxuser/etc/logstash/conf.d/partiecsv.conf", 
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

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')  # Récupère la requête de recherche
    response = requests.get(f"{ELASTICSEARCH_URL}/dataset_index/_search?q={query}")
    return response.json()
