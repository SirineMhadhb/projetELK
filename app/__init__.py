from flask import Flask

# Configuration du chemin d'upload
UPLOAD_FOLDER = "/home/vboxuser/Desktop/projet ELK/data"

# Initialisation de l'application Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Import des routes
from app import routes
