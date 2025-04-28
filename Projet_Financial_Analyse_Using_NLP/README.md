# Application d'Analyse NLP Financière

Cette application web permet d'analyser des textes financiers en utilisant des techniques avancées de traitement du langage naturel (NLP). Elle intègre deux modèles BERT fine-tunés spécialisés dans l'analyse financière :
- Analyse de sentiment (3 classes : Positif, Neutre, Négatif)
- Extraction de relation (29 classes de relations financières)
- Reconnaissance des entités nommées (4 classes : PER, ORG, LOC, MISC)

## Fonctionnalités Principales

- **Interface Utilisateur Intuitive**
  - Design responsive et moderne
  - Mode clair/sombre pour un confort visuel optimal
  - Navigation simple et intuitive

- **Analyse de Texte Avancée**
  - Analyse de sentiment avec probabilités détaillées
  - Extraction de relations financières complexes
  - Visualisation des résultats avec graphiques interactifs

- **Architecture Moderne**
  - Backend Flask robuste
  - Modèles BERT fine-tunés pour des résultats précis
  - API RESTful pour une intégration facile

## Prérequis

- Python 3.11 ou supérieur
- PyTorch 1.7+
- Transformers (Hugging Face) 4.0+
- Flask 2.0+
- Autres dépendances listées dans `requirements.txt`

## Installation

1. Clonez ce dépôt :
```bash
git clone <URL-du-dépôt>
cd <nom-du-dossier>
```

2. Créez un environnement virtuel (recommandé) :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Assurez-vous d'avoir les modèles fine-tunés dans les dossiers suivants :
   - `./Fine-tuned-Bert-base-uncased-lora-financial-Relation-Extraction-cls`
4. Les autres modèles sont sur HuggingFace
- `Wilbiz/financial-ner`
- `Wilbiz/financial-sentiment`
## Utilisation

1. Lancez l'application :
```bash
python app.py
```

2. Accédez à l'interface web :
   - Ouvrez votre navigateur à l'adresse : `http://127.0.0.1:5000`

3. Utilisation de l'application :
   - Sélectionnez le modèle souhaité dans la barre latérale
   - Entrez votre texte financier dans la zone de texte
   - Cliquez sur "Analyser" pour obtenir les résultats
   - Visualisez les probabilités et les relations extraites

## Exemple d'Utilisation

```python
# Exemple de texte financier
texte = "Apple Inc. announced record quarterly revenue of $123.9 billion, up 11% year over year. The company's CEO, Tim Cook, highlighted strong performance across all product categories."

# Résultats attendus :
# - Analyse de sentiment : Positif (0.85)
# - Relations extraites :
#   - Apple Inc. -> CEO -> Tim Cook
#   - Apple Inc. -> revenue -> $123.9 billion
```

## Classes de Relation

L'extraction de relation peut détecter les 29 types suivants :
- 0: 'headquarters location'
- 1: 'owned by'
- 2: 'parent organization'
- 3: 'position held'
- 4: 'product/material produced'
- 5: 'founded by'
- 6: 'manufacturer'
- 7: 'chairperson'
- 8: 'currency'
- 9: 'subsidiary'
- 10: 'industry'
- 11: 'operator'
- 12: 'location of formation'
- 13: 'legal form'
- 14: 'owner of'
- 15: 'chief executive officer'
- 16: 'stock exchange'
- 17: 'employer'
- 18: 'developer'
- 19: 'creator'
- 20: 'brand'
- 21: 'business division'
- 22: 'original broadcaster'
- 23: 'member of'
- 24: 'publisher'
- 25: 'distributed by'
- 26: 'director/manager'
- 27: 'distribution format'
- 28: 'platform'

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Contact

Pour toute question ou suggestion, n'hésitez pas à ouvrir une issue sur GitHub.
