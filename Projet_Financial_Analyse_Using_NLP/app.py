from flask import Flask, request, jsonify, render_template
from model_bert_fine_tuned import predict, NumpyEncoder
import traceback
import logging
import os
import sys
import json
from check_models import check_huggingface_models, create_model_placeholder

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')

# Configurer Flask pour utiliser notre encodeur JSON personnalisé
app.json_encoder = NumpyEncoder

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.json
    text = data.get('text', '')
    model_type = data.get('model_type', 'sentiment')
    instruction = data.get('instruction', None)
    analyze_instruction = data.get('analyze_instruction', False)
    
    if not text:
        return jsonify({'error': 'Texte manquant'}), 400
    
    try:
        app.logger.info(f"Analyse demandée: model_type={model_type}, texte={text[:50]}...")
        
        # Extraction de relation avec analyse optionnelle de l'instruction
        if model_type == 'relation' and analyze_instruction and instruction:
            from model_bert_fine_tuned import predict_ner, predict_relation
            
            # Obtenir le résultat principal de l'extraction de relation
            result = predict_relation(text, instruction)
            
            # Analyser l'instruction avec NER pour extraire les entités
            try:
                app.logger.info(f"Analyse NER de l'instruction: {instruction[:50]}...")
                instruction_ner_result = predict_ner(instruction)
                if instruction_ner_result and 'entities' in instruction_ner_result:
                    # Ajouter les entités de l'instruction au résultat
                    result['instruction_entities'] = instruction_ner_result['entities']
                    app.logger.info(f"Entités extraites de l'instruction: {len(instruction_ner_result['entities'])}")
            except Exception as e:
                app.logger.error(f"Erreur lors de l'analyse NER de l'instruction: {str(e)}")
                # Ne pas interrompre le flux principal si l'analyse NER échoue
        else:
            # Cas standard pour les autres types de modèles
            from model_bert_fine_tuned import predict
            result = predict(text, instruction, model_type)
        
        # Vérifier la sérialisabilité
        try:
            # Essayer de sérialiser le résultat avant de le renvoyer
            json.dumps(result)
        except TypeError as e:
            app.logger.error(f"Erreur de sérialisation JSON: {str(e)}")
            # Si une erreur se produit, essayer de nettoyer le résultat
            import numpy as np
            
            def clean_for_json(obj):
                if isinstance(obj, (np.integer, np.floating)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, list):
                    return [clean_for_json(item) for item in obj]
                elif isinstance(obj, dict):
                    return {key: clean_for_json(value) for key, value in obj.items()}
                return obj
            
            result = clean_for_json(result)
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Erreur pendant la prédiction: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'details': traceback.format_exc()}), 500

def startup_check():
    """Vérifie que tout est correctement configuré au démarrage"""
    logger.info("Vérification de la configuration au démarrage...")
    
    # Vérifier les modèles Hugging Face
    try:
        logger.info("Vérification des modèles Hugging Face...")
        check_huggingface_models()
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des modèles Hugging Face: {str(e)}")
    
    # Créer des placeholders pour les modèles locaux si nécessaire
    try:
        create_model_placeholder()
    except Exception as e:
        logger.error(f"Erreur lors de la création des placeholders de modèles: {str(e)}")
    
    logger.info("Vérification terminée.")

if __name__ == '__main__':
    # Effectuer les vérifications au démarrage
    startup_check()
    
    # Démarrer l'application
    app.run(debug=True)