#!/usr/bin/env python3
"""
Patch FINAL — Toutes les modifications consultation_live.html
1. Symptômes/Maladies depuis API
2. Suggestions IA hybride
3. Fuzzy matching custom
4. UX: ordre onglets, popup pourquoi, 4 résultats, pas de scores techniques
5. Suppression détails symptômes inutiles
"""
import re

FILE = '/app/templates/medecin/consultation_live.html'
with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(FILE + '.bak2', 'w', encoding='utf-8') as f:
    f.write(content)

changes = 0

# ============================================================
# 1) SYMPTOMES array → vide (chargé depuis API)
# ============================================================
p = re.compile(r"var SYMPTOMES = \[[\s\S]*?\];\s*\n\s*var MALADIES", re.DOTALL)
if p.search(content):
    content = p.sub("var SYMPTOMES = [];\n\nvar MALADIES", content)
    changes += 1
    print("✅ 1. SYMPTOMES → chargé depuis API")

# ============================================================
# 2) MALADIES array → vide (chargé depuis API)
# ============================================================
p = re.compile(r"var MALADIES = \[[\s\S]*?\];\s*\n", re.DOTALL)
if p.search(content):
    content = p.sub("var MALADIES = [];\nvar MALADIES_DATA = [];\n\n", content)
    changes += 1
    print("✅ 2. MALADIES → chargé depuis API")

# ============================================================
# 3) Réordonner onglets: Patient → Mesures → Sympt → Maladies
# ============================================================
OLD_TABS = """<div class="sidebar-tabs">
            <div class="sidebar-tab active" onclick="showTab('patient')">
                <i class="fa-solid fa-user"></i><br>Patient
            </div>
            <div class="sidebar-tab" onclick="showTab('symptomes')">
                <i class="fa-solid fa-stethoscope"></i><br>Sympt.
            </div>
            <div class="sidebar-tab" onclick="showTab('maladies')">
                <i class="fa-solid fa-virus"></i><br>Maladies
            </div>
            <div class="sidebar-tab" onclick="showTab('mesures')">
                <i class="fa-solid fa-ruler"></i><br>Mesures
            </div>
        </div>"""

NEW_TABS = """<div class="sidebar-tabs">
            <div class="sidebar-tab active" onclick="showTab('patient')">
                <i class="fa-solid fa-user"></i><br>Patient
            </div>
            <div class="sidebar-tab" onclick="showTab('mesures')">
                <i class="fa-solid fa-ruler"></i><br>Mesures
            </div>
            <div class="sidebar-tab" onclick="showTab('symptomes')">
                <i class="fa-solid fa-stethoscope"></i><br>Sympt.
            </div>
            <div class="sidebar-tab" onclick="showTab('maladies')">
                <i class="fa-solid fa-virus"></i><br>Maladies
            </div>
        </div>"""

if OLD_TABS in content:
    content = content.replace(OLD_TABS, NEW_TABS)
    changes += 1
    print("✅ 3. Onglets réordonnés")

# ============================================================
# 4) Corriger showTab pour le nouvel ordre
# ============================================================
content = content.replace(
    "var tabs = ['patient','symptomes','maladies','mesures'];",
    "var tabs = ['patient','mesures','symptomes','maladies'];"
)
changes += 1
print("✅ 4. showTab corrigé")

# ============================================================
# 5) Agrandir liste symptômes + supprimer détails
# ============================================================
content = content.replace(
    'id="symptomes-list" style="max-height:180px;overflow-y:auto;"',
    'id="symptomes-list" style="max-height:360px;overflow-y:auto;"'
)
content = content.replace(
    '<div id="symptomes-details" style="margin-top:0.5rem;max-height:200px;overflow-y:auto;border-top:1px solid var(--border);padding-top:0.5rem;"></div>',
    ''
)
content = content.replace('renderSymptomesDetails();', '')
changes += 1
print("✅ 5. Liste symptômes agrandie + détails supprimés")

# ============================================================
# 6) Remplacer referentiel.json + updateAISuggestions
# ============================================================

# 6a. Ajouter le chargement API avant le fetch referentiel
API_LOADER = """// ===== MEDIGO IA — Chargement depuis API =====
var _iaDebounceTimer = null;
var _iaLoading = false;

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
        console.log('MEDIGO IA: ' + SYMPTOMES.length + ' symptômes');
    }).catch(function(e) { console.warn('Fallback symptômes:', e); });

fetch('/api/medigo/maladies/', {headers: {'X-CSRFToken': csrfToken}})
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.maladies) {
            MALADIES_DATA = data.maladies;
            MALADIES = data.maladies.map(function(m) { return m.nom; });
            renderMaladies(MALADIES);
            console.log('MEDIGO IA: ' + MALADIES.length + ' maladies');
        }
    }).catch(function(e) { console.warn('Fallback maladies:', e); });

"""

OLD_REF_START = "// ===== AI RULE-BASED SUGGESTIONS =====\n// ===== AI REFERENTIEL ====="
if OLD_REF_START in content:
    content = content.replace(OLD_REF_START, API_LOADER + "// ===== ANCIEN REFERENTIEL (désactivé) =====")
    changes += 1
    print("✅ 6a. Chargement API ajouté")

# 6b. Supprimer le fetch referentiel.json
p = re.compile(
    r"fetch\('/static/data/referentiel\.json'\)[\s\S]*?\.catch\(function\(e\) \{ console\.log\('Erreur chargement référentiel:', e\); \}\);",
    re.DOTALL
)
if p.search(content):
    content = p.sub("// referentiel.json désactivé — remplacé par API MEDIGO IA", content)
    changes += 1
    print("✅ 6b. referentiel.json désactivé")

# 6c. Remplacer updateAISuggestions
p_update = re.compile(
    r"function updateAISuggestions\(\) \{[\s\S]*?container\.innerHTML = html;\s*\}",
    re.DOTALL
)

NEW_AI = r"""function updateAISuggestions() {
    var container = document.getElementById('ai-suggestions');
    if (selectedSymptomes.size === 0) {
        container.innerHTML = '<div class="ai-empty"><i class="fa-solid fa-robot"></i>Sélectionnez des symptômes pour voir les suggestions IA</div>';
        return;
    }
    if (_iaDebounceTimer) clearTimeout(_iaDebounceTimer);
    _iaDebounceTimer = setTimeout(function() { _callIALive(); }, 600);
}

function _callIALive() {
    var container = document.getElementById('ai-suggestions');
    if (_iaLoading) return;
    _iaLoading = true;
    container.innerHTML = '<div class="ai-empty"><div class="spinner" style="margin:0 auto;border-color:rgba(92,107,192,0.2);border-top-color:#5c6bc0;width:24px;height:24px;"></div><div style="margin-top:0.5rem;">Analyse en cours...</div></div>';
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
        return fetch('/api/consultation/' + consultationId + '/ia-live/', {headers: {'X-CSRFToken': csrfToken}});
    })
    .then(function(r) { return r.json(); })
    .then(function(data) { _iaLoading = false; _renderIAResults(data); })
    .catch(function(e) {
        _iaLoading = false;
        container.innerHTML = '<div class="ai-empty"><i class="fa-solid fa-exclamation-triangle" style="color:var(--orange);"></i><div style="margin-top:0.3rem;">Erreur — réessayez</div></div>';
    });
}

function _renderIAResults(data) {
    var container = document.getElementById('ai-suggestions');
    var html = '';
    if (data.red_flags && data.red_flags.length > 0) {
        html += '<div style="background:#ffebee;border:1.5px solid #e53935;border-radius:8px;padding:0.65rem;margin-bottom:0.5rem;">';
        html += '<div style="font-size:0.72rem;font-weight:800;color:#c62828;text-transform:uppercase;margin-bottom:0.3rem;"><i class="fa-solid fa-triangle-exclamation"></i> Signaux d\'alerte</div>';
        data.red_flags.forEach(function(rf) { html += '<div style="font-size:0.78rem;color:#c62828;padding:0.15rem 0;">' + rf.alerte + '</div>'; });
        html += '</div>';
    }
    if (data.orientation && data.orientation.niveau !== 'orientation_standard') {
        var tc = data.orientation.niveau === 'urgence_immediate' ? '#c62828' : '#e65100';
        var tb = data.orientation.niveau === 'urgence_immediate' ? '#ffebee' : '#fff3e0';
        html += '<div style="background:' + tb + ';border:1px solid ' + tc + ';border-radius:8px;padding:0.5rem;margin-bottom:0.5rem;font-size:0.78rem;color:' + tc + ';font-weight:600;"><i class="fa-solid fa-hospital"></i> ' + data.orientation.message + '</div>';
    }
    if (data.diagnostics && data.diagnostics.length > 0) {
        html += '<div class="ai-box"><div class="ai-box-title"><i class="fa-solid fa-lightbulb"></i> Suggestions IA</div>';
        data.diagnostics.slice(0, 4).forEach(function(d, idx) {
            var pct = Math.round(d.score_final * 100);
            var cls = pct >= 40 ? 'high' : pct >= 20 ? 'medium' : 'low';
            var urg = d.urgence ? ' <span style="background:#c62828;color:white;font-size:0.6rem;padding:0.1rem 0.35rem;border-radius:10px;font-weight:800;">URGENT</span>' : '';
            html += '<div class="ai-disease" style="flex-direction:column;align-items:stretch;padding:0.4rem 0;gap:0.2rem;">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;"><span class="ai-disease-name">' + d.maladie + urg + '</span><span class="ai-confidence ' + cls + '">' + pct + '%</span></div>';
            if (d.categorie) html += '<div style="font-size:0.7rem;color:#5c6bc0;font-weight:600;"><i class="fa-solid fa-tag" style="font-size:0.58rem;margin-right:0.2rem;"></i>' + d.categorie + '</div>';
            if (d.explication && d.explication.raison_courte) html += '<div style="font-size:0.72rem;color:var(--text-muted);font-style:italic;">' + d.explication.raison_courte + '</div>';
            html += '<div style="display:flex;gap:0.3rem;margin-top:0.15rem;">';
            html += '<button onclick="selectionnerDiagnostic(\'' + d.maladie.replace(/'/g, "\\'") + '\')" style="font-size:0.68rem;padding:0.2rem 0.5rem;background:var(--green);color:white;border:none;border-radius:4px;cursor:pointer;font-family:inherit;font-weight:600;"><i class="fa-solid fa-check"></i> Sélectionner</button>';
            html += '<button onclick="voirPourquoi(' + idx + ')" style="font-size:0.68rem;padding:0.2rem 0.5rem;background:var(--bg);color:var(--blue);border:1px solid var(--border);border-radius:4px;cursor:pointer;font-family:inherit;font-weight:600;"><i class="fa-solid fa-circle-info"></i> Voir pourquoi</button>';
            html += '</div></div>';
        });
        html += '</div>';
    }
    if (data.questions_suivantes && data.questions_suivantes.length > 0) {
        html += '<div class="ai-box"><div class="ai-box-title"><i class="fa-solid fa-circle-question"></i> Questions à poser</div>';
        data.questions_suivantes.slice(0, 6).forEach(function(q) { html += '<div class="ai-question"><i class="fa-solid fa-chevron-right"></i><span>' + q + '</span></div>'; });
        html += '</div>';
    }
    if (data.symptomes_inconnus && data.symptomes_inconnus.length > 0) {
        html += '<div style="background:#fff3e0;border:1px solid #ffb74d;border-radius:8px;padding:0.5rem;margin-bottom:0.5rem;"><div style="font-size:0.68rem;font-weight:700;color:#e65100;margin-bottom:0.2rem;"><i class="fa-solid fa-question-circle"></i> Non reconnus</div>';
        data.symptomes_inconnus.forEach(function(s) { html += '<div style="font-size:0.75rem;color:#e65100;">• ' + s + '</div>'; });
        html += '</div>';
    }
    html += '<div class="ai-disclaimer"><i class="fa-solid fa-triangle-exclamation"></i> Aide au diagnostic — ne remplace pas le jugement clinique</div>';
    container.innerHTML = html;
    window._lastIAResults = data;
}

function selectionnerDiagnostic(nom) {
    if (!MALADIES.includes(nom)) MALADIES.push(nom);
    selectedMaladies.add(nom);
    document.getElementById('maladies-count').textContent = selectedMaladies.size + ' maladie(s)';
    renderMaladies(MALADIES);
    var container = document.getElementById('ai-suggestions');
    var msg = document.createElement('div');
    msg.style.cssText = 'background:#e8f5e9;color:#2e7d32;padding:0.4rem;border-radius:6px;font-size:0.78rem;font-weight:600;text-align:center;margin-bottom:0.5rem;';
    msg.innerHTML = '<i class="fa-solid fa-check-circle"></i> ' + nom + ' ajoutée';
    container.insertBefore(msg, container.firstChild);
    setTimeout(function() { if (msg.parentNode) msg.remove(); }, 2500);
}

function voirPourquoi(idx) {
    if (!window._lastIAResults || !window._lastIAResults.diagnostics) return;
    var d = window._lastIAResults.diagnostics[idx];
    if (!d) return;
    var old = document.getElementById('ia-popup-pourquoi');
    if (old) old.remove();
    var exp = d.explication || {};
    var h = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;"><div style="font-weight:700;font-size:0.9rem;color:var(--navy);">' + d.maladie + '</div><button onclick="document.getElementById(\'ia-popup-pourquoi\').remove()" style="background:none;border:none;font-size:1.1rem;cursor:pointer;color:var(--text-muted);padding:0.2rem;">✕</button></div>';
    if (exp.symptomes_correspondants && exp.symptomes_correspondants.length > 0) {
        h += '<div style="font-size:0.72rem;font-weight:700;color:#43a047;margin-bottom:0.15rem;">✓ Symptômes qui correspondent</div>';
        exp.symptomes_correspondants.forEach(function(s) { h += '<div style="font-size:0.78rem;padding:0.1rem 0 0.1rem 0.6rem;">• ' + s + '</div>'; });
    }
    if (exp.symptomes_importants_manquants && exp.symptomes_importants_manquants.length > 0) {
        h += '<div style="font-size:0.72rem;font-weight:700;color:#fb8c00;margin-top:0.35rem;margin-bottom:0.15rem;">? À rechercher</div>';
        exp.symptomes_importants_manquants.forEach(function(s) { h += '<div style="font-size:0.78rem;padding:0.1rem 0 0.1rem 0.6rem;">• ' + s + '</div>'; });
    }
    if (exp.facteurs_patient && exp.facteurs_patient.length > 0) {
        h += '<div style="font-size:0.72rem;font-weight:700;color:#1976d2;margin-top:0.35rem;margin-bottom:0.15rem;">Contexte patient</div>';
        exp.facteurs_patient.forEach(function(f) { h += '<div style="font-size:0.78rem;padding:0.1rem 0 0.1rem 0.6rem;">• ' + f + '</div>'; });
    }
    if (exp.red_flags_associes && exp.red_flags_associes.length > 0) {
        h += '<div style="font-size:0.72rem;font-weight:700;color:#e53935;margin-top:0.35rem;margin-bottom:0.15rem;">Signaux d\'alerte</div>';
        exp.red_flags_associes.forEach(function(r) { h += '<div style="font-size:0.78rem;padding:0.1rem 0 0.1rem 0.6rem;color:#c62828;">• ' + r + '</div>'; });
    }
    var popup = document.createElement('div');
    popup.id = 'ia-popup-pourquoi';
    popup.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;border-radius:14px;padding:1.1rem;box-shadow:0 16px 56px rgba(0,0,0,0.22);border:1px solid #e2e8f0;z-index:300;max-width:380px;width:92%;max-height:70vh;overflow-y:auto;';
    popup.innerHTML = h;
    document.body.appendChild(popup);
    setTimeout(function() {
        document.addEventListener('click', function handler(e) {
            var p = document.getElementById('ia-popup-pourquoi');
            if (p && !p.contains(e.target)) { p.remove(); document.removeEventListener('click', handler); }
        });
    }, 150);
}"""

if p_update.search(content):
    content = p_update.sub(NEW_AI, content)
    changes += 1
    print("✅ 6c. updateAISuggestions remplacé par version IA")

# ============================================================
# 7) Remplacer ajouterSymptomeCustom avec fuzzy
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
    fetch('/api/consultation/normalize-symptome/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
        body: JSON.stringify({texte: val})
    })
    .then(function(r) { return r.json(); })
    .then(function(result) {
        var nomFinal = val;
        if (result.statut_mapping === 'canonique' || result.statut_mapping === 'confirme_auto') {
            nomFinal = result.symptome_canonique;
        } else if (result.statut_mapping === 'a_confirmer' && result.suggestions && result.suggestions.length > 0) {
            var sugList = result.suggestions.map(function(s,i) { return (i+1) + '. ' + s.nom; }).join('\\n');
            var choix = prompt('Vouliez-vous dire :\\n\\n' + sugList + '\\n\\nTapez le numéro ou Entrée pour garder "' + val + '"');
            if (choix && !isNaN(choix) && choix >= 1 && choix <= result.suggestions.length) {
                nomFinal = result.suggestions[parseInt(choix) - 1].nom;
            }
        }
        if (!SYMPTOMES.includes(nomFinal)) SYMPTOMES.push(nomFinal);
        selectedSymptomes.set(nomFinal, {intensite: 0, evolution: 'stable'});
        document.getElementById('symptome-search').value = '';
        document.getElementById('add-symptome-box').style.display = 'none';
        renderSymptomes(SYMPTOMES);
        document.getElementById('symptomes-count').textContent = selectedSymptomes.size + ' symptôme(s)';
        updateAISuggestions();
    })
    .catch(function() {
        if (!SYMPTOMES.includes(val)) SYMPTOMES.push(val);
        selectedSymptomes.set(val, {intensite: 0, evolution: 'stable'});
        document.getElementById('symptome-search').value = '';
        document.getElementById('add-symptome-box').style.display = 'none';
        renderSymptomes(SYMPTOMES);
        document.getElementById('symptomes-count').textContent = selectedSymptomes.size + ' symptôme(s)';
        updateAISuggestions();
    });
}"""

if OLD_CUSTOM in content:
    content = content.replace(OLD_CUSTOM, NEW_CUSTOM)
    changes += 1
    print("✅ 7. Fuzzy matching pour symptômes custom")

# Sauvegarder
with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎉 {changes} modifications appliquées avec succès !")
