document.addEventListener('DOMContentLoaded', () => {
    // Éléments DOM
    const themeToggle = document.getElementById('theme-toggle');
    const modelButtons = document.querySelectorAll('.model-btn');
    const analyzeBtn = document.getElementById('analyze-btn');
    const textInput = document.getElementById('text-input');
    const instructionContainer = document.getElementById('instruction-container');
    const instructionInput = document.getElementById('instruction-input');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultsContainer = document.getElementById('results-container');
    const resultModel = document.getElementById('result-model');
    const resultLabel = document.getElementById('result-label');
    const resultDetails = document.getElementById('result-details');

    // État de l'application
    let currentModel = 'sentiment';
    
    // Basculer entre mode clair et sombre
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        document.body.classList.toggle('light-mode');
        
        // Stocker la préférence de thème
        const isDarkMode = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isDarkMode);
    });
    
    // Charger la préférence de thème
    const loadThemePreference = () => {
        const isDarkMode = localStorage.getItem('darkMode') === 'true';
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
            document.body.classList.remove('light-mode');
        } else {
            document.body.classList.add('light-mode');
            document.body.classList.remove('dark-mode');
        }
    };
    loadThemePreference();
    
    // Fonction pour gérer l'affichage du champ d'instruction
    const toggleInstructionField = () => {
        if (currentModel === 'relation') {
            instructionContainer.classList.remove('hidden');
        } else {
            instructionContainer.classList.add('hidden');
        }
    };
    
    // Initialisation de l'affichage du champ d'instruction
    toggleInstructionField();
    
    // Changer de modèle
    modelButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Mettre à jour la classe active
            modelButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Mettre à jour le modèle actuel
            currentModel = button.dataset.model;
            
            // Mettre à jour l'étiquette du modèle dans les résultats
            if (currentModel === 'sentiment') {
                resultModel.textContent = 'Analyse de sentiment';
            } else if (currentModel === 'relation') {
                resultModel.textContent = 'Extraction de relation';
            } else if (currentModel === 'ner') {
                resultModel.textContent = 'Reconnaissance d\'entités';
            }
            
            // Gérer l'affichage du champ d'instruction
            toggleInstructionField();
            
            // Réinitialiser les résultats
            resultsContainer.classList.add('hidden');
        });
    });
    
    // Fonction d'analyse du texte
    analyzeBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        
        if (!text) {
            alert('Veuillez entrer un texte à analyser.');
            return;
        }
        
        // Afficher l'indicateur de chargement
        loadingIndicator.classList.remove('hidden');
        resultsContainer.classList.add('hidden');
        
        try {
            // Préparer les données à envoyer
            const requestData = {
                text: text,
                model_type: currentModel
            };
            
            // Ajouter l'instruction si c'est une extraction de relation (même si vide)
            if (currentModel === 'relation') {
                requestData.instruction = instructionInput.value.trim();
                
                // Si l'instruction est fournie, également demander l'analyse NER de l'instruction
                if (requestData.instruction) {
                    requestData.analyze_instruction = true;
                }
            }
            
            console.log('Envoi de requête:', requestData);
            
            // Appeler l'API
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Erreur inconnue' }));
                console.error('Erreur API:', response.status, errorData);
                throw new Error(`Erreur du serveur: ${errorData.error || response.statusText}`);
            }
            
            const result = await response.json();
            console.log('Résultat reçu:', result);
            
            // Masquer l'indicateur de chargement
            loadingIndicator.classList.add('hidden');
            
            // Afficher les résultats
            displayResults(result);
            
        } catch (error) {
            console.error('Erreur détaillée:', error);
            loadingIndicator.classList.add('hidden');
            alert('Une erreur est survenue lors de l\'analyse: ' + error.message);
        }
    });
    
    // Fonction pour interpréter une relation
    function interpretRelation(relation, entities, instruction, instructionEntities) {
        // Formater le nom de la relation pour une meilleure lisibilité
        const formattedRelation = relation
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
            
        // Tableau pour stocker les entités à utiliser et leur source
        let usedEntities = [];
        let sourceText = "";
        
        // Si nous avons des entités extraites de l'instruction, les utiliser en priorité
        if (instruction && instructionEntities && instructionEntities.length > 0) {
            sourceText = "instruction";
            usedEntities = instructionEntities;
            console.log("Utilisation des entités de l'instruction (NER):", usedEntities);
        }
        // Sinon, utiliser les entités du texte principal
        else if (entities && entities.length > 0) {
            sourceText = "texte principal";
            usedEntities = entities;
            console.log("Utilisation des entités du texte principal (NER):", usedEntities);
        }
        
        // Créer un tableau d'entités par type, en évitant les doublons
        const entitiesByType = {};
        
        usedEntities.forEach(entity => {
            const type = entity.entity_group || entity.type;
            const text = entity.word || entity.text;
            
            if (!entitiesByType[type]) {
                entitiesByType[type] = new Set();
            }
            entitiesByType[type].add(text);
        });
        
        // Convertir les Sets en Arrays pour faciliter l'utilisation
        Object.keys(entitiesByType).forEach(type => {
            entitiesByType[type] = Array.from(entitiesByType[type]);
        });
        
        // Si nous avons des entités, générer une interprétation
        if (Object.keys(entitiesByType).length > 0) {
            // Adapter l'interprétation selon le type de relation
            if (relation.includes('owner') || relation.includes('owned')) {
                const orgs = entitiesByType['ORG'] || [];
                const persons = entitiesByType['PER'] || [];
                
                if (orgs.length > 0 && persons.length > 0) {
                    return `La relation <strong>${formattedRelation}</strong> indique que <strong>${persons[0]}</strong> est propriétaire de <strong>${orgs[0]}</strong>. <em>(Source: ${sourceText})</em>`;
                }
                else if (orgs.length > 1) {
                    return `La relation <strong>${formattedRelation}</strong> indique que <strong>${orgs[0]}</strong> est propriétaire de <strong>${orgs[1]}</strong>. <em>(Source: ${sourceText})</em>`;
                }
            }
            else if (relation.includes('employe') || relation.includes('employer')) {
                const orgs = entitiesByType['ORG'] || [];
                const persons = entitiesByType['PER'] || [];
                
                if (orgs.length > 0 && persons.length > 0) {
                    return `La relation <strong>${formattedRelation}</strong> indique que <strong>${persons[0]}</strong> est employé(e) par <strong>${orgs[0]}</strong>. <em>(Source: ${sourceText})</em>`;
                }
            }
            else if (relation.includes('headquarter') || relation.includes('location')) {
                const orgs = entitiesByType['ORG'] || [];
                const locs = entitiesByType['LOC'] || [];
                
                if (orgs.length > 0 && locs.length > 0) {
                    return `La relation <strong>${formattedRelation}</strong> indique que <strong>${orgs[0]}</strong> a son siège à <strong>${locs[0]}</strong>. <em>(Source: ${sourceText})</em>`;
                }
            }
            else if (relation.includes('product') || relation.includes('produced')) {
                const orgs = entitiesByType['ORG'] || [];
                const products = entitiesByType['PRODUCT'] || [];
                
                if (orgs.length > 0 && products.length > 0) {
                    return `La relation <strong>${formattedRelation}</strong> indique que <strong>${orgs[0]}</strong> produit <strong>${products[0]}</strong>. <em>(Source: ${sourceText})</em>`;
                }
            }
            
            // Interprétation générique basée sur les types d'entités trouvés
            const entityParts = [];
            Object.entries(entitiesByType).forEach(([type, values]) => {
                if (values.length > 0) {
                    const entityNames = values.slice(0, 2).join(', ');
                    const suffix = values.length > 2 ? '...' : '';
                    entityParts.push(`<strong>${type}</strong>: ${entityNames}${suffix}`);
                }
            });
            
            return `La relation <strong>${formattedRelation}</strong> a été détectée entre les entités:<br>${entityParts.join('<br>')}<br><em>(Source: ${sourceText})</em>`;
        }
        
        // Si aucune entité n'est trouvée
        return `La relation <strong>${formattedRelation}</strong> a été détectée dans ce texte, mais aucune entité spécifique n'a pu être identifiée.`;
    }
    
    // Afficher les résultats
    function displayResults(result) {
        // Afficher le conteneur de résultats
        resultsContainer.classList.remove('hidden');
        
        // Préparer le contenu en fonction du modèle
        if (currentModel === 'sentiment') {
            // Afficher l'étiquette du résultat
            resultLabel.textContent = result.label;
            resultLabel.className = 'result-label';
            
            if (result.label === 'Positif') {
                resultLabel.classList.add('positive');
            } else if (result.label === 'Négatif') {
                resultLabel.classList.add('negative');
            } else {
                resultLabel.classList.add('neutral');
            }
            
            // Afficher les détails de probabilité
            let detailsHTML = '<h3>Détails des probabilités</h3>';
            
            // Pour le modèle de sentiment financier
            const labels = {
                'Negative': 'Négatif', 
                'Positive': 'Positif', 
                'Neutral': 'Neutre'
            };
            
            if (result.predictions) {
                // Utiliser les prédictions avec les labels directement
                detailsHTML += createProbabilityBarsFromPredictions(result.predictions, labels);
            } else {
                // Utiliser uniquement les probabilités
                const defaultLabels = ['Négatif', 'Positif', 'Neutre'];
                detailsHTML += createProbabilityBars(result.probabilities, defaultLabels);
            }
            
            // Ajouter le texte coloré selon le sentiment
            detailsHTML += '<h3>Texte analysé</h3>';
            
            // Déterminer la classe CSS pour le sentiment
            let sentimentClass = '';
            if (result.label === 'Positif') {
                sentimentClass = 'positive-text';
            } else if (result.label === 'Négatif') {
                sentimentClass = 'negative-text';
            } else {
                sentimentClass = 'neutral-text';
            }
            
            // Afficher le texte coloré
            detailsHTML += `<div class="analyzed-text ${sentimentClass}">${textInput.value}</div>`;
            
            resultDetails.innerHTML = detailsHTML;
        } 
        else if (currentModel === 'relation') {
            // Afficher l'étiquette du résultat pour la relation
            resultLabel.textContent = result.label;
            resultLabel.className = 'result-label neutral';
            
            // Afficher les détails de la relation
            let detailsHTML = '<h3>Détails de la relation</h3>';
            
            // Formater le nom de la relation pour une meilleure lisibilité
            const formattedRelation = result.label
                .split('_')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
            
            detailsHTML += `<p>Relation détectée : <strong class="relation-name">${formattedRelation}</strong> (${result.class})</p>`;
            detailsHTML += `<p>Confiance : <strong>${(result.probabilities[result.class] * 100).toFixed(2)}%</strong></p>`;
            
            // Légende des couleurs d'entités
            const entityMappings = {
                'CORP': 'Entreprise',
                'CW': 'Crypto-monnaie',
                'DATE': 'Date',
                'MONEY': 'Montant',
                'PERCENT': 'Pourcentage',
                'PERSON': 'Personne',
                'PER': 'Personne',
                'PRODUCT': 'Produit',
                'LOC': 'Lieu',
                'GPE': 'Entité géopolitique',
                'ORG': 'Organisation',
                'TIME': 'Heure/Temps',
                'MISC': 'Divers'
            };
            
            // Ajouter le texte avec la relation mise en évidence
            detailsHTML += '<h3>Texte analysé</h3>';
            
            // Si des entités ont été identifiées, les mettre en évidence
            if (result.entities && result.entities.length > 0) {
                detailsHTML += '<div class="entity-text">';
                
                // Créer une version du texte avec les spans d'entités
                const text = result.text;
                let lastEnd = 0;
                let markedText = '';
                
                // Trier les entités par position de début
                const sortedEntities = [...result.entities].sort((a, b) => a.start - b.start);
                
                for (const entity of sortedEntities) {
                    // Ajouter le texte entre la dernière entité et celle-ci
                    markedText += text.substring(lastEnd, entity.start);
                    
                    // Ajouter l'entité avec le span
                    const entityText = text.substring(entity.start, entity.end);
                    const entityType = entity.type || entity.entity_group;
                    const entityTypeFr = entityMappings[entityType] || entityType;
                    
                    markedText += `<span class="entity entity-${entityType}" title="${entityTypeFr}">
                                ${entityText}
                                <span class="entity-tooltip">
                                    ${entityTypeFr} (${(entity.score * 100).toFixed(1)}%)
                                </span>
                            </span>`;
                    
                    lastEnd = entity.end;
                }
                
                // Ajouter le reste du texte
                markedText += text.substring(lastEnd);
                
                detailsHTML += markedText;
                detailsHTML += '</div>';
                
                // Ajouter une légende pour les entités
                if (sortedEntities.length > 0) {
                    detailsHTML += '<div class="entity-legend">';
                    detailsHTML += '<h4>Entités identifiées</h4>';
                    detailsHTML += '<div class="entity-stats">';
                    
                    // Créer un tableau pour compter les types d'entités
                    const entityTypes = {};
                    for (const entity of result.entities) {
                        const type = entity.type || entity.entity_group;
                        if (!entityTypes[type]) {
                            entityTypes[type] = 0;
                        }
                        entityTypes[type]++;
                    }
                    
                    // Afficher les types d'entités
                    for (const [type, count] of Object.entries(entityTypes)) {
                        const typeFr = entityMappings[type] || type;
                        detailsHTML += `
                            <div class="entity-stat-item">
                                <span class="entity-color-sample entity-${type}"></span>
                                ${typeFr}
                                <span class="entity-stat-count">${count}</span>
                            </div>
                        `;
                    }
                    
                    detailsHTML += '</div></div>';
                    
                    // Ajouter l'interprétation de la relation
                    detailsHTML += `<div class="relation-interpretation">
                        <h4>Interprétation</h4>
                        <p>${interpretRelation(result.label, result.entities, instructionInput.value, result.instruction_entities)}</p>
                    </div>`;
                }
            } else {
                // Sinon, afficher simplement le texte avec un style relation
                detailsHTML += `<div class="analyzed-text relation-text">${result.text}</div>`;
                
                // Ajouter l'interprétation de la relation en utilisant les entités de l'instruction s'il y en a
                detailsHTML += `<div class="relation-interpretation">
                    <h4>Interprétation</h4>
                    <p>${interpretRelation(result.label, null, instructionInput.value, result.instruction_entities)}</p>
                </div>`;
            }
            
            resultDetails.innerHTML = detailsHTML;
        }
        else if (currentModel === 'ner') {
            // Pour le modèle NER, afficher un résumé et masquer l'étiquette
            resultLabel.textContent = "";
            resultLabel.className = 'hidden';
            
            // Afficher les entités trouvées
            let detailsHTML = '<h3>Entités détectées</h3>';
            
            // Légende des couleurs d'entités
            const entityMappings = {
                'CORP': 'Entreprise',
                'CW': 'Crypto-monnaie',
                'DATE': 'Date',
                'MONEY': 'Montant',
                'PERCENT': 'Pourcentage',
                'PERSON': 'Personne',
                'PER': 'Personne',
                'PRODUCT': 'Produit',
                'LOC': 'Lieu',
                'GPE': 'Entité géopolitique',
                'ORG': 'Organisation',
                'TIME': 'Heure/Temps',
                'MISC': 'Divers'
            };
            
            // Afficher les statistiques d'entités
            if (Object.keys(result.entity_stats).length > 0) {
                detailsHTML += '<div class="entity-legend">';
                detailsHTML += '<h4>Types d\'entités reconnus</h4>';
                detailsHTML += '<div class="entity-stats">';
                
                for (const [entityType, count] of Object.entries(result.entity_stats)) {
                    const entityTypeFr = result.entities.find(e => e.entity_group === entityType)?.entity_group_fr || 
                                        entityMappings[entityType] || entityType;
                    detailsHTML += `
                        <div class="entity-stat-item">
                            <span class="entity-color-sample entity-${entityType}"></span>
                            ${entityTypeFr}
                            <span class="entity-stat-count">${count}</span>
                        </div>
                    `;
                }
                
                detailsHTML += '</div></div>';
            } else {
                detailsHTML += '<p>Aucune entité n\'a été détectée dans ce texte.</p>';
            }
            
            // Afficher le texte avec les entités surlignées
            if (result.entities.length > 0) {
                detailsHTML += '<h3>Texte analysé</h3>';
                detailsHTML += '<div class="entity-text">';
                
                // Créer une version du texte avec les spans d'entités
                const text = result.text;
                let lastEnd = 0;
                let markedText = '';
                
                // Trier les entités par position de début
                const sortedEntities = [...result.entities].sort((a, b) => a.start - b.start);
                
                for (const entity of sortedEntities) {
                    // Ajouter le texte entre la dernière entité et celle-ci
                    markedText += text.substring(lastEnd, entity.start);
                    
                    // Ajouter l'entité avec le span
                    const entityText = text.substring(entity.start, entity.end);
                    const entityTypeFr = entity.entity_group_fr || entityMappings[entity.entity_group] || entity.entity_group;
                    
                    markedText += `<span class="entity entity-${entity.entity_group}" title="${entityTypeFr}">
                                    ${entityText}
                                    <span class="entity-tooltip">${entityTypeFr} (${(entity.score * 100).toFixed(1)}%)</span>
                                </span>`;
                    
                    lastEnd = entity.end;
                }
                
                // Ajouter le reste du texte
                markedText += text.substring(lastEnd);
                
                detailsHTML += markedText;
                detailsHTML += '</div>';
            }
            
            resultDetails.innerHTML = detailsHTML;
        }
    }
    
    // Créer les barres de probabilité à partir des prédictions
    function createProbabilityBarsFromPredictions(predictions, labelMapping) {
        let html = '<div class="probability-bars">';
        
        predictions.forEach(pred => {
            const percentage = (pred.score * 100).toFixed(2);
            const label = labelMapping[pred.label] || pred.label;
            
            html += `
                <div class="probability-item">
                    <div class="probability-info">
                        <span>${label}</span>
                        <span>${percentage}%</span>
                    </div>
                    <div class="probability-bar">
                        <div class="probability-fill" style="width: ${percentage}%"></div>
                        <div class="probability-label">${percentage}%</div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    // Créer les barres de probabilité
    function createProbabilityBars(probabilities, labels) {
        let html = '<div class="probability-bars">';
        
        probabilities.forEach((prob, index) => {
            const percentage = (prob * 100).toFixed(2);
            html += `
                <div class="probability-item">
                    <div class="probability-info">
                        <span>${labels[index]}</span>
                        <span>${percentage}%</span>
                    </div>
                    <div class="probability-bar">
                        <div class="probability-fill" style="width: ${percentage}%"></div>
                        <div class="probability-label">${percentage}%</div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
}); 