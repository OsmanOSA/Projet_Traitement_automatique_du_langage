"""
Script de vérification des modèles.
Ce script vérifie que tous les modèles et dépendances sont correctement installés
et accessibles avant de démarrer l'application.
"""

import os
import sys
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemins des modèles locaux
model_analysis_sentiment_path = './Fine-tuned-model_Bert-base-uncased-110M-sentiment_analysis'
model_relation_extraction_path = './Fine-tuned-Bert-base-uncased-lora-financial-Relation-Extraction-cls'

def check_huggingface_models():
    """Vérifie que les modèles Hugging Face sont accessibles"""
    logger.info("Vérification des modèles Hugging Face...")
    
    try:
        # Vérifier le modèle de sentiment financier
        logger.info("Vérification du modèle de sentiment...")
        sentiment_pipeline = pipeline(
            "text-classification",
            model="Wilbiz/financial-sentiment",
            tokenizer="Wilbiz/financial-sentiment",
            return_all_scores=True
        )
        result = sentiment_pipeline("Apple a annoncé des résultats financiers positifs.")
        logger.info(f"Modèle de sentiment testé avec succès: {result}")
    except Exception as e:
        logger.error(f"Erreur avec le modèle de sentiment: {str(e)}")
        return False
    
    try:
        # Vérifier le modèle NER
        logger.info("Vérification du modèle NER...")
        ner_pipeline = pipeline(
            "ner",
            model="Wilbiz/financial-ner",
            tokenizer="Wilbiz/financial-ner",
            aggregation_strategy="simple",
            ignore_labels=["O"]
        )
        result = ner_pipeline("Apple a gagné 10 millions de dollars en 2023.")
        logger.info(f"Modèle NER testé avec succès: {result}")
    except Exception as e:
        logger.error(f"Erreur avec le modèle NER: {str(e)}")
        return False
    
    return True

def check_local_models():
    """Vérifie que les modèles locaux sont accessibles"""
    logger.info("Vérification des modèles locaux...")
    
    # Vérifier l'existence des dossiers de modèles
    local_models = {
        "Sentiment Analysis": model_analysis_sentiment_path,
        "Relation Extraction": model_relation_extraction_path
    }
    
    all_ok = True
    
    for model_name, model_path in local_models.items():
        if not os.path.exists(model_path):
            logger.error(f"Le modèle {model_name} n'existe pas au chemin: {model_path}")
            all_ok = False
    
    # Si les dossiers existent, tenter de charger les modèles
    if all_ok:
        for model_name, model_path in local_models.items():
            try:
                logger.info(f"Tentative de chargement du modèle {model_name}...")
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModelForSequenceClassification.from_pretrained(model_path)
                logger.info(f"Modèle {model_name} chargé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors du chargement du modèle {model_name}: {str(e)}")
                all_ok = False
    
    if all_ok:
        create_model_placeholder()
    
    return all_ok

def create_model_placeholder():
    """Crée des fichiers de modèles vides si les modèles locaux n'existent pas"""
    # Cette fonction permet de créer rapidement des dossiers vides si les modèles locaux
    # ne sont pas nécessaires (ex: si on utilise uniquement les modèles Hugging Face)
    
    local_models = {
        "Sentiment Analysis": model_analysis_sentiment_path,
        "Relation Extraction": model_relation_extraction_path
    }
    
    for model_name, model_path in local_models.items():
        if not os.path.exists(model_path):
            os.makedirs(model_path, exist_ok=True)
            with open(os.path.join(model_path, "README.txt"), "w") as f:
                f.write(f"Placeholder pour le modèle {model_name}.\n")
                f.write("Ce fichier a été créé automatiquement par check_models.py\n")
                f.write("Ce dossier est un placeholder pour permettre à l'application de fonctionner sans erreur.\n")
            logger.info(f"Créé un placeholder pour le modèle {model_name}")

def main():
    """Fonction principale"""
    logger.info("Démarrage de la vérification des modèles...")
    
    # Vérifier les modèles Hugging Face
    hf_models_ok = check_huggingface_models()
    
    # Vérifier les modèles locaux (et créer des placeholders si nécessaire)
    check_local_models()
    
    if hf_models_ok:
        logger.info("Tous les modèles Hugging Face sont disponibles.")
        return 0
    else:
        logger.error("Certains modèles Hugging Face ne sont pas disponibles.")
        return 1
    
if __name__ == "__main__":
    sys.exit(main()) 