import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import numpy as np
import logging
import os
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemins des modèles
model_analysis_sentiment_path = './Fine-tuned-model_Bert-base-uncased-110M-sentiment_analysis'
model_relation_extraction_path = './Fine-tuned-Bert-base-uncased-lora-financial-Relation-Extraction-cls'

# Cache pour les modèles et pipelines
model_cache = {}

# Classe pour rendre les objets NumPy sérialisables en JSON
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def convert_to_serializable(obj):
    """Convertit les types NumPy en types Python standards pour la sérialisation JSON"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return [convert_to_serializable(x) for x in obj]
    elif isinstance(obj, list):
        return [convert_to_serializable(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif hasattr(obj, 'item') and callable(getattr(obj, 'item')):
        # Pour les types torch qui ont une méthode item()
        return obj.item()
    else:
        return obj

def get_sentiment_pipeline():
    """Obtient ou crée un pipeline de sentiment avec mise en cache"""
    if 'sentiment_pipeline' not in model_cache:
        try:
            logger.info("Initialisation du pipeline d'analyse de sentiment")
            sentiment_pipeline = pipeline(
                "text-classification",
                model="Wilbiz/financial-sentiment",
                tokenizer="Wilbiz/financial-sentiment",
                return_all_scores=True
            )
            model_cache['sentiment_pipeline'] = sentiment_pipeline
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du pipeline de sentiment: {str(e)}")
            raise
    return model_cache['sentiment_pipeline']

def get_ner_pipeline():
    """Obtient ou crée un pipeline NER avec mise en cache"""
    if 'ner_pipeline' not in model_cache:
        try:
            logger.info("Initialisation du pipeline NER")
            ner_pipeline = pipeline(
                "ner",
                model="Wilbiz/financial-ner",
                tokenizer="Wilbiz/financial-ner",
                aggregation_strategy="simple",
                ignore_labels=["O"]
            )
            model_cache['ner_pipeline'] = ner_pipeline
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du pipeline NER: {str(e)}")
            raise
    return model_cache['ner_pipeline']

def load_model_bert_base_uncased(model_path: str, num_labels: int):
    """Charge un modèle BERT et son tokenizer avec mise en cache"""
    cache_key = f"model_{model_path}"
    if cache_key not in model_cache:
        try:
            logger.info(f"Chargement du modèle depuis {model_path}")
            
            # Vérifier si le chemin existe
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Le chemin du modèle n'existe pas: {model_path}")
                
            model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=num_labels)
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model_cache[cache_key] = (model, tokenizer)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle {model_path}: {str(e)}")
            raise
    return model_cache[cache_key]

def predict_sentiment(text):
    logger.info("Analyse de sentiment demandée")
    try:
        # Utiliser le pipeline Hugging Face avec le modèle financier spécifié
        sentiment_pipeline = get_sentiment_pipeline()
        
        # Faire la prédiction
        predictions = sentiment_pipeline(text)
        
        # Créer un mapping des labels
        label_mapping = {
            "Negative": "Négatif",
            "Positive": "Positif",
            "Neutral": "Neutre"
        }
        
        # Extraire les scores et les labels
        scores_with_labels = predictions[0]
        
        # S'assurer que les scores sont des floats standards, pas des float32
        for item in scores_with_labels:
            item["score"] = float(item["score"])
        
        # Trier par score pour trouver le label avec le score le plus élevé
        scores_with_labels.sort(key=lambda x: x["score"], reverse=True)
        top_prediction = scores_with_labels[0]
        
        # Extraire les probabilités dans le même ordre
        probabilities = [float(item["score"]) for item in scores_with_labels]  # Conversion en float standard
        
        # Traduire le label prédit
        predicted_label = top_prediction["label"]
        translated_label = label_mapping.get(predicted_label, predicted_label)
        
        # Retourner au format attendu par le frontend
        result = {
            "class": scores_with_labels.index(top_prediction),
            "label": translated_label,
            "probabilities": probabilities,
            "predictions": scores_with_labels  # Inclure les prédictions complètes pour référence
        }
        
        logger.info(f"Analyse de sentiment terminée: {translated_label}")
        return result
    except Exception as e:
        logger.error(f"Erreur pendant l'analyse de sentiment: {str(e)}")
        raise

def predict_ner(text):
    logger.info("Reconnaissance d'entités demandée")
    try:
        # Obtenir le pipeline NER
        ner_pipeline = get_ner_pipeline()
        
        # Mapping en français pour les types d'entités
        entity_type_mapping = {
            "CORP": "Entreprise",
            "CW": "Crypto-monnaie",
            "DATE": "Date",
            "MONEY": "Montant",
            "PERCENT": "Pourcentage",
            "PERSON": "Personne",
            "PRODUCT": "Produit"
        }
        
        # Faire la prédiction
        entities = ner_pipeline(text)
        
        # Conversion des valeurs numpy en types Python standards
        for entity in entities:
            entity["score"] = float(entity["score"])
            entity["start"] = int(entity["start"])
            entity["end"] = int(entity["end"])
        
        # Traduire les types d'entités
        for entity in entities:
            entity_type = entity["entity_group"]
            entity["entity_group_fr"] = entity_type_mapping.get(entity_type, entity_type)
        
        # Créer des statistiques sur les entités trouvées
        entity_stats = {}
        for entity in entities:
            entity_type = entity["entity_group"]
            if entity_type not in entity_stats:
                entity_stats[entity_type] = 0
            entity_stats[entity_type] += 1
        
        # Retourner les résultats
        result = {
            "entities": entities,
            "entity_stats": entity_stats,
            "text": text
        }
        
        logger.info(f"Reconnaissance d'entités terminée: {len(entities)} entités trouvées")
        return result
    except Exception as e:
        logger.error(f"Erreur pendant la reconnaissance d'entités: {str(e)}")
        raise

def predict_relation(text, instruction=None):
    logger.info("Extraction de relation demandée")
    try:
        relation_map = {
            0: 'owner of', 1: 'product/material produced', 2: 'headquarters location', 
            3: 'location of formation', 4: 'industry', 5: 'stock exchange', 6: 'manufacturer',
            7: 'chairperson', 8: 'owned by', 9: 'brand', 10: 'employer', 
            11: 'developer', 12: 'subsidiary', 13: 'parent organization',
            14: 'position held', 15: 'founded by', 16: 'original broadcaster', 17: 'legal form', 
            18: 'currency', 19: 'operator', 20: 'platform', 21: 'distribution format', 22: 'business division',
            23: 'chief executive officer', 24: 'creator', 25: 'distributed by', 26: 'director/manager',
            27: 'member of', 28: 'publisher'
        }
        
        # Vérifier si le modèle existe
        if not os.path.exists(model_relation_extraction_path):
            raise FileNotFoundError(f"Le modèle d'extraction de relation n'existe pas: {model_relation_extraction_path}")
        
        model, tokenizer = load_model_bert_base_uncased(model_relation_extraction_path, num_labels=29)
        
        # Utiliser l'instruction fournie par l'utilisateur ou une instruction par défaut
        if instruction is None or instruction.strip() == "":
            instruction = "Utilize the input text as a context reference, choose the right relationship between"
        
        prompt = f"""
                    {instruction}

                    [{text}]

                """.strip()
        
        inputs = tokenizer(prompt, return_tensors="pt", max_length=512,
                        padding=True, truncation=True)
        
        # Vérifier si le modèle a un attribut 'device'
        if hasattr(model, 'device'):
            inputs = inputs.to(model.device)
        
        predictions = model(**inputs)

        predicted_class = predictions.logits.argmax().item()
        
        # S'assurer que la classe prédite est dans le mappage
        if predicted_class not in relation_map:
            logger.warning(f"Classe prédite {predicted_class} non trouvée dans relation_map")
            relation_label = f"Relation inconnue ({predicted_class})"
        else:
            relation_label = relation_map[predicted_class]
        
        # Récupérer les logits et les convertir en probabilités avec la fonction softmax
        logits = predictions.logits
        probabilities = torch.nn.functional.softmax(logits, dim=-1)
        
        # Convertir les probabilités en liste Python standard (pas numpy)
        probabilities_list = [float(p) for p in probabilities[0].tolist()]
        
        # Extraire les entités potentielles pour la visualisation
        entities = []
        try:
            # Essayer d'utiliser le modèle NER pour identifier les entités potentielles
            ner_pipeline = get_ner_pipeline()
            ner_results = ner_pipeline(text)
            
            # Convertir les résultats en format standard
            for entity in ner_results:
                entity_type = entity["entity_group"]
                entity_text = entity["word"]
                entities.append({
                    "type": entity_type,
                    "text": entity_text,
                    "start": int(entity["start"]),
                    "end": int(entity["end"]),
                    "score": float(entity["score"])
                })
            
            logger.info(f"Extraction d'entités pour la relation: {len(entities)} entités trouvées")
        except Exception as e:
            logger.warning(f"Impossible d'extraire les entités pour la relation: {str(e)}")
        
        # Retourner au format attendu par le frontend
        result = {
            "class": int(predicted_class),  # Convertir en int Python standard
            "label": relation_label,
            "probabilities": probabilities_list,
            "entities": entities,
            "text": text,
            # instruction_entities sera ajouté par app.py si analyze_instruction est vrai
        }
        
        logger.info(f"Extraction de relation terminée: {relation_label}")
        return result
    except Exception as e:
        logger.error(f"Erreur pendant l'extraction de relation: {str(e)}")
        raise

def predict(text: str, instruction: str = None, model_type: str = "sentiment"):
    logger.info(f"Prédiction demandée: type={model_type}, texte={text[:50]}...")
    
    try:
        if model_type == "sentiment":
            result = predict_sentiment(text)
        elif model_type == "relation":
            result = predict_relation(text, instruction)
        elif model_type == "ner":
            result = predict_ner(text)
        else:
            raise ValueError(f"Type de modèle non valide: {model_type}. Choisissez 'sentiment', 'relation' ou 'ner'")
        
        # S'assurer que tous les résultats sont sérialisables en JSON
        result = convert_to_serializable(result)
        return result
    except Exception as e:
        logger.error(f"Erreur pendant la prédiction: {str(e)}")
        # Relancer l'exception pour la gestion d'erreur de niveau supérieur
        raise






