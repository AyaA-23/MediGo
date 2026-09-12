#!/usr/bin/env python3
"""
Script de patch pour consultation_live.html
Remplace: SYMPTOMES/MALADIES hardcodés + referentiel.json + updateAISuggestions()
Par: Appels API MEDIGO IA hybride
"""
import re
import sys

FILE = '/app/templates/medecin/consultation_live.html'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

original = content

# ============================================================
# 1) Remplacer le tableau SYMPTOMES hardcodé par un tableau vide
# ============================================================
pattern_symptomes = re.compile(
    r"var SYMPTOMES = \[[\s\S]*?\];\s*\n\s*var MALADIES",
    re.DOTALL
)
content = pattern_symptomes.sub(
    "var SYMPTOMES = [];  // Chargé depuis API MEDIGO IA\n\nvar MALADIES",
    content
)

# ============================================================
# 2) Remplacer le tableau MALADIES hardcodé par un tableau vide
# ============================================================
pattern_maladies = re.compile(
    r"var MALADIES = \[[\s\S]*?\];\s*\n",
    re.DOTALL
)
content = pattern_maladies.sub(
    "var MALADIES = [];  // Chargé depuis API MEDIGO IA\nvar MALADIES_DATA = [];  // Données complètes (nom, catégorie, urgence)\n\n",
    content
)

# ============================================================
# 3) Remplacer le bloc fetch referentiel.json + updateAISuggestions
# ============================================================
OLD_REFERENTIEL_BLOCK = """// ===== AI RULE-BASED SUGGESTIONS =====
// ===== AI REFERENTIEL =====
var REFERENTIEL = null;
var COMBO_RULES = [];
var RED_FLAGS = [];

fetch('/static/data/referentiel.json')"""

NEW_AI_BLOCK = """// ===== AI MEDIGO IA — Chargement symptômes et maladies depuis API =====
var _iaDebounceTimer = null;
var _iaLoading = false;

function chargerSymptomesAPI() {
    fetch('/api/medigo/symptomes/', {headers: {'X-CSRFToken': csrfToken}})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            SYMPTOMES = [];
            if (data.categories) {
                Object.keys(data.categories).forEach(function(cat) {
                    data.categories[cat].forEach(function(s) {
                        if (!SYMPTOMES.includes(s)) SYMPTOMES.push(s);
                    });
                });
            }
            renderSymptomes(SYMPTOMES);
            console.log('MEDIGO IA: ' + SYMPTOMES.length + ' symptômes chargés');
        })
        .catch(function(e) { console.log('Fallback symptômes locaux:', e); });
}

function chargerMaladiesAPI() {
    fetch('/api/medigo/maladies/', {headers: {'X-CSRFToken': csrfToken}})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.maladies) {
                MALADIES_DATA = data.maladies;
                MALADIES = data.maladies.map(function(m) { return m.nom; });
                renderMaladies(MALADIES);
                console.log('MEDIGO IA: ' + MALADIES.length + ' maladies chargées');
            }
        })
        .catch(function(e) { console.log('Fallback maladies locaux:', e); });
}

// Charger au démarrage
chargerSymptomesAPI();
chargerMaladiesAPI();

// ===== AI SUGGESTIONS — Appel API hybride =====
fetch('/static/data/referentiel.json')"""

content = content.replace(OLD_REFERENTIEL_BLOCK, NEW_AI_BLOCK)

# ============================================================
# 4) Remplacer la fonction updateAISuggestions complète
# ============================================================
# Trouver et remplacer la fonction updateAISuggestions
old_update_start = "function updateAISuggestions() {"
old_update_end_marker = "container.innerHTML = html;\n}"

# Utiliser regex pour capturer toute la fonction
pattern_update = re.compile(
    r"function updateAISuggestions\(\) \{[\s\S]*?container\.innerHTML = html;\s*\}",
    re.DOTALL
)

NEW_UPDATE_FUNCTION = """function updateAISuggestions() {
    var container = document.getElementById('ai-suggestions');
    if (selectedSymptomes.size === 0) {
        container.innerHTML = '<div class="ai-empty"><i class="fa-solid fa-robot"></i>Sélectionnez des symptômes pour voir les suggestions IA</div>';
        return;
    }

    // Debounce : attendre 600ms après la dernière sélection
    if (_iaDebounceTimer) clearTimeout(_iaDebounceTimer);
    _iaDebounceTimer = setTimeout(function() { _callIALive(); }, 600);
}

function _callIALive() {
    var container = document.getElementById('ai-suggestions');
    if (_iaLoading) return;
    _iaLoading = true;

    container.innerHTML = '<div class="ai-empty"><div class="spinner" style="margin:0 auto;border-color:rgba(92,107,192,0.2);border-top-color:#5c6bc0;width:24px;height:24px;"></div><div style="margin-top:0.5rem;">Analyse IA en cours...</div></div>';

    // 1) Sauvegarder les symptômes actuels d'abord
    var symptList = [];
    selectedSymptomes.forEach(function(data, nom) {
        symptList.push({nom: nom, intensite: data.intensite, evolution: data.evolution});
    });

    fetch('/api/consultation/symptomes/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
        body: JSON.stringify({consultation_id: consultationId, symptomes: symptList})
    })
    .then(function() {
        // 2) Appeler l'endpoint IA hybride
        return fetch('/api/consultation/' + consultationId + '/ia-live/', {
            headers: {'X-CSRFToken': csrfToken}
        });
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        _iaLoading = false;
        _renderIAResults(data);
    })
    .catch(function(e) {
        _iaLoading = false;
        console.error('Erreur IA:', e);
        container.innerHTML = '<div class="ai-empty"><i class="fa-solid fa-exclamation-triangle" style="color:var(--orange);"></i><div style="margin-top:0.3rem;">Erreur IA — réessayez</div></div>';
    });
}

function _renderIAResults(data) {
    var container = document.getElementById('ai-suggestions');
    var html = '';

    // Red flags en premier
    if (data.red_flags && data.red_flags.length > 0) {
        html += '<div style="background:#ffebee;border:1.5px solid #e53935;border-radius:8px;padding:0.65rem;margin-bottom:0.5rem;animation:slideIn 0.3s ease;">';
        html += '<div style="font-size:0.72rem;font-weight:800;color:#c62828;text-transform:uppercase;margin-bottom:0.3rem;"><i class="fa-solid fa-triangle-exclamation"></i> Signaux d\\'alerte</div>';
        data.red_flags.forEach(function(rf) {
            html += '<div style="font-size:0.78rem;color:#c62828;padding:0.2rem 0;">' + rf.alerte + '</div>';
        });
        html += '</div>';
    }

    // Orientation triage
    if (data.orientation && data.orientation.niveau !== 'orientation_standard') {
        var triColor = data.orientation.niveau === 'urgence_immediate' ? '#c62828' : '#e65100';
        var triBg = data.orientation.niveau === 'urgence_immediate' ? '#ffebee' : '#fff3e0';
        html += '<div style="background:' + triBg + ';border:1px solid ' + triColor + ';border-radius:8px;padding:0.5rem;margin-bottom:0.5rem;font-size:0.78rem;color:' + triColor + ';font-weight:600;">';
        html += '<i class="fa-solid fa-hospital"></i> ' + data.orientation.message + '</div>';
    }

    // Diagnostics hybrides
    if (data.diagnostics && data.diagnostics.length > 0) {
        html += '<div class="ai-box" style="animation:slideIn 0.3s ease;">';
        html += '<div class="ai-box-title"><i class="fa-solid fa-brain"></i> Diagnostics IA (hybride)</div>';
        data.diagnostics.slice(0, 8).forEach(function(d, idx) {
            var pct = Math.round(d.score_final * 100);
            var cls = pct >= 40 ? 'high' : pct >= 20 ? 'medium' : 'low';
            var urgBadge = d.urgence ? ' <span style="background:#c62828;color:white;font-size:0.6rem;padding:0.1rem 0.35rem;border-radius:10px;font-weight:800;">URGENT</span>' : '';

            html += '<div class="ai-disease" style="flex-direction:column;align-items:stretch;padding:0.4rem 0;gap:0.25rem;">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
            html += '<span class="ai-disease-name">' + d.maladie + urgBadge + '</span>';
            html += '<span class="ai-confidence ' + cls + '">' + pct + '%</span>';
            html += '</div>';

            // Scores détaillés
            html += '<div style="display:flex;gap:0.5rem;font-size:0.68rem;color:var(--text-muted);">';
            html += '<span>RB: ' + Math.round(d.score_rule_based * 100) + '%</span>';
            html += '<span>XGB: ' + Math.round(d.score_xgboost * 100) + '%</span>';
            if (d.categorie) html += '<span style="color:#5c6bc0;">• ' + d.categorie + '</span>';
            html += '</div>';

            // Explication courte
            if (d.explication && d.explication.raison_courte) {
                html += '<div style="font-size:0.72rem;color:var(--text-muted);font-style:italic;">' + d.explication.raison_courte + '</div>';
            }

            // Boutons action
            html += '<div style="display:flex;gap:0.3rem;margin-top:0.2rem;">';
            html += '<button onclick="selectionnerDiagnostic(\\'' + d.maladie.replace(/'/g, "\\\\'") + '\\')" style="font-size:0.68rem;padding:0.2rem 0.5rem;background:var(--green);color:white;border:none;border-radius:4px;cursor:pointer;font-family:inherit;font-weight:600;"><i class="fa-solid fa-check"></i> Sélectionner</button>';
            html += '<button onclick="voirPourquoi(' + idx + ')" style="font-size:0.68rem;padding:0.2rem 0.5rem;background:var(--bg);color:var(--blue);border:1px solid var(--border);border-radius:4px;cursor:pointer;font-family:inherit;font-weight:600;"><i class="fa-solid fa-circle-info"></i> Voir pourquoi</button>';
            html += '</div>';

            html += '</div>';
        });
        html += '</div>';
    }

    // Questions à poser
    if (data.questions_suivantes && data.questions_suivantes.length > 0) {
        html += '<div class="ai-box">';
        html += '<div class="ai-box-title"><i class="fa-solid fa-circle-question"></i> Questions à poser</div>';
        data.questions_suivantes.slice(0, 8).forEach(function(q) {
            html += '<div class="ai-question"><i class="fa-solid fa-chevron-right"></i><span>' + q + '</span></div>';
        });
        html += '</div>';
    }

    // Symptômes non reconnus
    if (data.symptomes_inconnus && data.symptomes_inconnus.length > 0) {
        html += '<div style="background:#fff3e0;border:1px solid #ffb74d;border-radius:8px;padding:0.5rem;margin-bottom:0.5rem;">';
        html += '<div style="font-size:0.68rem;font-weight:700;color:#e65100;margin-bottom:0.2rem;"><i class="fa-solid fa-question-circle"></i> Symptômes non reconnus</div>';
        data.symptomes_inconnus.forEach(function(s) {
            html += '<div style="font-size:0.75rem;color:#e65100;">• ' + s + '</div>';
        });
        html += '</div>';
    }

    html += '<div class="ai-disclaimer"><i class="fa-solid fa-triangle-exclamation"></i> Aide au diagnostic — ne remplace pas le jugement clinique</div>';

    container.innerHTML = html;

    // Stocker les résultats pour "Voir pourquoi"
    window._lastIAResults = data;
}

function selectionnerDiagnostic(nom) {
    // Ajouter la maladie aux maladies sélectionnées
    if (!MALADIES.includes(nom)) MALADIES.push(nom);
    selectedMaladies.add(nom);
    document.getElementById('maladies-count').textContent = selectedMaladies.size + ' maladie(s)';
    renderMaladies(MALADIES);

    // Feedback visuel
    var container = document.getElementById('ai-suggestions');
    var msg = document.createElement('div');
    msg.style.cssText = 'background:#e8f5e9;color:#2e7d32;padding:0.4rem;border-radius:6px;font-size:0.78rem;font-weight:600;text-align:center;margin-bottom:0.5rem;animation:slideIn 0.3s ease;';
    msg.innerHTML = '<i class="fa-solid fa-check-circle"></i> ' + nom + ' ajoutée';
    container.insertBefore(msg, container.firstChild);
    setTimeout(function() { if (msg.parentNode) msg.remove(); }, 2500);
}

function voirPourquoi(idx) {
    if (!window._lastIAResults || !window._lastIAResults.diagnostics) return;
    var d = window._lastIAResults.diagnostics[idx];
    if (!d) return;

    var exp = d.explication || {};
    var msg = d.maladie + '\\n\\n';
    msg += 'Score final: ' + Math.round(d.score_final * 100) + '% (RB: ' + Math.round(d.score_rule_based * 100) + '% + XGB: ' + Math.round(d.score_xgboost * 100) + '%)\\n\\n';

    if (exp.symptomes_correspondants && exp.symptomes_correspondants.length > 0) {
        msg += 'Symptômes correspondants:\\n• ' + exp.symptomes_correspondants.join('\\n• ') + '\\n\\n';
    }
    if (exp.symptomes_importants_manquants && exp.symptomes_importants_manquants.length > 0) {
        msg += 'Symptômes importants manquants:\\n• ' + exp.symptomes_importants_manquants.join('\\n• ') + '\\n\\n';
    }
    if (exp.facteurs_patient && exp.facteurs_patient.length > 0) {
        msg += 'Facteurs patient:\\n• ' + exp.facteurs_patient.join('\\n• ') + '\\n\\n';
    }
    if (exp.red_flags_associes && exp.red_flags_associes.length > 0) {
        msg += 'Red flags associés:\\n⚠️ ' + exp.red_flags_associes.join('\\n⚠️ ');
    }

    alert(msg);
}"""

match = pattern_update.search(content)
if match:
    content = content[:match.start()] + NEW_UPDATE_FUNCTION + content[match.end():]
    print("✅ updateAISuggestions() remplacée par version IA hybride")
else:
    print("⚠️ Impossible de trouver updateAISuggestions() — ajout en fin de script")
    content = content.replace("// ===== INIT =====", NEW_UPDATE_FUNCTION + "\n\n// ===== INIT =====")

# ============================================================
# 5) Remplacer ajouterSymptomeCustom pour ajouter fuzzy matching
# ============================================================
OLD_CUSTOM = """function ajouterSymptomeCustom() {
    var val = document.getElementById('custom-symptome-input').value.trim();
    if (!val) return;
    if (!SYMPTOMES.includes(val)) SYMPTOMES.push(val);
    selectedSymptomes.set(val, {intensite: 0, evolution: 'stable'});
    document.getElementById('symptome-search').value = '';
    document.getElementById('add-symptome-box').style.display = 'none';
    renderSymptomes(SYMPTOMES);
    document.getElementById('symptomes-count').textContent = selectedSymptomes.size + ' symptôme(s)';
    renderSymptomesDetails();
    updateAISuggestions();
}"""

NEW_CUSTOM = """function ajouterSymptomeCustom() {
    var val = document.getElementById('custom-symptome-input').value.trim();
    if (!val) return;

    // Appeler l'API de fuzzy matching
    fetch('/api/consultation/normalize-symptome/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
        body: JSON.stringify({texte: val})
    })
    .then(function(r) { return r.json(); })
    .then(function(result) {
        var nomFinal = val;

        if (result.statut_mapping === 'canonique' || result.statut_mapping === 'confirme_auto') {
            // Match fiable : utiliser le symptôme canonique
            nomFinal = result.symptome_canonique;
        } else if (result.statut_mapping === 'a_confirmer' && result.suggestions && result.suggestions.length > 0) {
            // Match moyen : proposer des suggestions
            var sugList = result.suggestions.map(function(s) { return s.nom + ' (' + Math.round(s.score * 100) + '%)'; }).join('\\n');
            var choix = prompt('Symptôme ambigu. Vouliez-vous dire :\\n\\n' + sugList + '\\n\\nTapez le numéro (1-' + result.suggestions.length + ') ou Entrée pour garder "' + val + '"');
            if (choix && !isNaN(choix) && choix >= 1 && choix <= result.suggestions.length) {
                nomFinal = result.suggestions[parseInt(choix) - 1].nom;
            }
        }
        // sinon : non_reconnu, on garde le texte original

        if (!SYMPTOMES.includes(nomFinal)) SYMPTOMES.push(nomFinal);
        selectedSymptomes.set(nomFinal, {intensite: 0, evolution: 'stable'});
        document.getElementById('symptome-search').value = '';
        document.getElementById('add-symptome-box').style.display = 'none';
        renderSymptomes(SYMPTOMES);
        document.getElementById('symptomes-count').textContent = selectedSymptomes.size + ' symptôme(s)';
        renderSymptomesDetails();
        updateAISuggestions();
    })
    .catch(function(e) {
        // Fallback sans fuzzy
        console.warn('Fuzzy matching failed:', e);
        if (!SYMPTOMES.includes(val)) SYMPTOMES.push(val);
        selectedSymptomes.set(val, {intensite: 0, evolution: 'stable'});
        document.getElementById('symptome-search').value = '';
        document.getElementById('add-symptome-box').style.display = 'none';
        renderSymptomes(SYMPTOMES);
        document.getElementById('symptomes-count').textContent = selectedSymptomes.size + ' symptôme(s)';
        renderSymptomesDetails();
        updateAISuggestions();
    });
}"""

content = content.replace(OLD_CUSTOM, NEW_CUSTOM)

# ============================================================
# 6) Supprimer le bloc referentiel.json fetch qui reste
# ============================================================
# Le fetch('/static/data/referentiel.json') reste après notre insertion
# On doit le remplacer par un commentaire
pattern_fetch_ref = re.compile(
    r"fetch\('/static/data/referentiel\.json'\)[\s\S]*?\.catch\(function\(e\) \{ console\.log\('Erreur chargement référentiel:', e\); \}\);",
    re.DOTALL
)
content = pattern_fetch_ref.sub(
    "// Référentiel.json remplacé par API MEDIGO IA (chargé ci-dessus)",
    content
)

# ============================================================
# Vérification et sauvegarde
# ============================================================
if content == original:
    print("❌ ERREUR: Aucune modification appliquée !")
    sys.exit(1)

# Backup
with open(FILE + '.bak', 'w', encoding='utf-8') as f:
    f.write(original)
print("📦 Backup sauvegardé: " + FILE + '.bak')

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ consultation_live.html patchée avec succès !")
print("   - SYMPTOMES: chargé depuis /api/medigo/symptomes/")
print("   - MALADIES: chargé depuis /api/medigo/maladies/")
print("   - AI Suggestions: appel hybride /api/consultation/<id>/ia-live/")
print("   - Custom symptôme: fuzzy matching via API")
print("   - Boutons 'Sélectionner' et 'Voir pourquoi' ajoutés")
