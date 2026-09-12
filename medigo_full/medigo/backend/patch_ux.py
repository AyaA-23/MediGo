#!/usr/bin/env python3
"""Patch 2 — Améliorations UX consultation_live.html"""
import sys

FILE = '/app/templates/medecin/consultation_live.html'
with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()
original = content
changes = 0

# 1. Augmenter hauteur liste symptômes
old = 'id="symptomes-list" style="max-height:180px;overflow-y:auto;"'
new = 'id="symptomes-list" style="max-height:360px;overflow-y:auto;"'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1. Liste symptômes agrandie (360px)")

# 2. Renommer "Diagnostics IA (hybride)" → "Suggestions IA"
old = '<i class="fa-solid fa-brain"></i> Diagnostics IA (hybride)'
new = '<i class="fa-solid fa-lightbulb"></i> Suggestions IA'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2. Renommé en 'Suggestions IA'")

# 3. Limiter à 4 résultats
old = 'data.diagnostics.slice(0, 8).forEach'
new = 'data.diagnostics.slice(0, 4).forEach'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 3. Limité à 4 suggestions")

# 4. Cacher les scores techniques RB/XGB — remplacer par catégorie seule
old_scores = """html += '<div style="display:flex;gap:0.5rem;font-size:0.68rem;color:var(--text-muted);">';
            html += '<span>RB: ' + Math.round(d.score_rule_based * 100) + '%</span>';
            html += '<span>XGB: ' + Math.round(d.score_xgboost * 100) + '%</span>';
            if (d.categorie) html += '<span style="color:#5c6bc0;">• ' + d.categorie + '</span>';
            html += '</div>';"""

new_scores = """if (d.categorie) {
                html += '<div style="font-size:0.7rem;color:#5c6bc0;font-weight:600;"><i class="fa-solid fa-tag" style="font-size:0.58rem;margin-right:0.2rem;"></i>' + d.categorie + '</div>';
            }"""

if old_scores in content:
    content = content.replace(old_scores, new_scores)
    changes += 1
    print("✅ 4. Scores techniques cachés, catégorie affichée")

# 5. Remplacer alert() par popup pour "Voir pourquoi"
old_fn = "function voirPourquoi(idx) {"
new_fn = """function voirPourquoi(idx) {
    if (!window._lastIAResults || !window._lastIAResults.diagnostics) return;
    var d = window._lastIAResults.diagnostics[idx];
    if (!d) return;
    var old = document.getElementById('ia-popup-pourquoi');
    if (old) old.remove();
    var exp = d.explication || {};
    var h = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem;"><div style="font-weight:700;font-size:0.9rem;color:var(--navy);">' + d.maladie + '</div><button onclick="this.closest(\\\'#ia-popup-pourquoi\\\').remove()" style="background:none;border:none;font-size:1.1rem;cursor:pointer;color:var(--text-muted);padding:0.2rem;">✕</button></div>';
    if (exp.symptomes_correspondants && exp.symptomes_correspondants.length > 0) {
        h += '<div style="font-size:0.72rem;font-weight:700;color:#43a047;margin-bottom:0.15rem;">✓ Symptômes qui correspondent</div>';
        exp.symptomes_correspondants.forEach(function(s) { h += '<div style="font-size:0.78rem;padding:0.1rem 0 0.1rem 0.6rem;color:var(--text);">• ' + s + '</div>'; });
    }
    if (exp.symptomes_importants_manquants && exp.symptomes_importants_manquants.length > 0) {
        h += '<div style="font-size:0.72rem;font-weight:700;color:#fb8c00;margin-top:0.4rem;margin-bottom:0.15rem;">? À rechercher</div>';
        exp.symptomes_importants_manquants.forEach(function(s) { h += '<div style="font-size:0.78rem;padding:0.1rem 0 0.1rem 0.6rem;color:var(--text);">• ' + s + '</div>'; });
    }
    if (exp.facteurs_patient && exp.facteurs_patient.length > 0) {
        h += '<div style="font-size:0.72rem;font-weight:700;color:#1976d2;margin-top:0.4rem;margin-bottom:0.15rem;">👤 Contexte patient</div>';
        exp.facteurs_patient.forEach(function(f) { h += '<div style="font-size:0.78rem;padding:0.1rem 0 0.1rem 0.6rem;color:var(--text);">• ' + f + '</div>'; });
    }
    if (exp.red_flags_associes && exp.red_flags_associes.length > 0) {
        h += '<div style="font-size:0.72rem;font-weight:700;color:#e53935;margin-top:0.4rem;margin-bottom:0.15rem;">⚠️ Signaux d\\'alerte</div>';
        exp.red_flags_associes.forEach(function(r) { h += '<div style="font-size:0.78rem;padding:0.1rem 0 0.1rem 0.6rem;color:#c62828;">• ' + r + '</div>'; });
    }
    var popup = document.createElement('div');
    popup.id = 'ia-popup-pourquoi';
    popup.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;border-radius:14px;padding:1.1rem;box-shadow:0 16px 56px rgba(0,0,0,0.22);border:1px solid var(--border);z-index:300;max-width:380px;width:92%;max-height:70vh;overflow-y:auto;animation:slideIn 0.25s ease;';
    popup.innerHTML = h;
    document.body.appendChild(popup);
    setTimeout(function() {
        document.addEventListener('click', function handler(e) {
            var p = document.getElementById('ia-popup-pourquoi');
            if (p && !p.contains(e.target)) { p.remove(); document.removeEventListener('click', handler); }
        });
    }, 150);
    return; // fin — ancien code mort ci-dessous
}
function _voirPourquoi_old(idx) {"""

if old_fn in content:
    # Trouver la fin de l'ancienne fonction voirPourquoi
    idx_start = content.index(old_fn)
    # Trouver "alert(msg);\n}" qui termine la fonction
    idx_alert = content.index("alert(msg);", idx_start)
    idx_end = content.index("}", idx_alert) + 1

    content = content[:idx_start] + new_fn + content[idx_end:]
    changes += 1
    print("✅ 5. Popup 'Voir pourquoi' (remplace alert)")

# Sauvegarder
if changes > 0:
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n🎉 {changes} améliorations appliquées !")
else:
    print("❌ Aucune modification trouvée")
