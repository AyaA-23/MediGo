#!/usr/bin/env python3
"""Patch — Ajouter rapport + résumé patient au template debriefing.html"""

FILE = '/app/templates/medecin/debriefing.html'
with open(FILE, 'r') as f:
    content = f.read()

# Ajouter les sections Rapport + Résumé AVANT le bloc historique
RAPPORT_HTML = """
<!-- RAPPORT DE CONSULTATION (auto-généré, 100% local) -->
{% if rapport %}
<div class="card" style="margin-bottom:1.5rem;border-left:4px solid var(--blue);">
    <div class="section-title">
        <i class="fa-solid fa-file-medical" style="color:var(--blue);"></i>
        Rapport de consultation
    </div>
    <div style="font-size:0.88rem;line-height:1.65;color:var(--text);padding:0.5rem 0;">
        {{ rapport.paragraphe }}
    </div>
    {% if rapport.medicaments %}
    <div style="margin-top:0.5rem;">
        {% for med in rapport.medicaments %}
        <div style="display:flex;align-items:center;gap:0.5rem;padding:0.35rem 0.75rem;background:var(--bg);border-radius:8px;margin-bottom:0.3rem;font-size:0.84rem;">
            <i class="fa-solid fa-pills" style="color:var(--green);font-size:0.75rem;"></i>
            <span style="font-weight:600;color:var(--navy);">{{ med }}</span>
        </div>
        {% endfor %}
    </div>
    {% endif %}
</div>
{% endif %}

<!-- RÉSUMÉ PATIENT (combinaison de toutes les consultations) -->
{% if resume %}
<div class="card" style="margin-bottom:1.5rem;border-left:4px solid var(--teal);background:linear-gradient(135deg,#f0fdfa,#f8fffe);">
    <div class="section-title">
        <i class="fa-solid fa-clipboard-list" style="color:var(--teal);"></i>
        Résumé patient
        <span style="font-size:0.7rem;font-weight:500;color:var(--text-muted);margin-left:0.5rem;">{{ resume.nb_consultations }} consultation{{ resume.nb_consultations|pluralize }}</span>
    </div>
    <div style="font-size:0.88rem;line-height:1.65;color:var(--text);padding:0.5rem 0;">
        {{ resume.resume }}
    </div>
    {% if resume.chroniques %}
    <div style="display:flex;flex-wrap:wrap;gap:0.3rem;margin-top:0.5rem;">
        {% for c in resume.chroniques %}
        <span style="background:#f3e5f5;color:#7b1fa2;padding:0.2rem 0.6rem;border-radius:12px;font-size:0.75rem;font-weight:600;">{{ c }}</span>
        {% endfor %}
    </div>
    {% endif %}
    {% if resume.allergies %}
    <div style="display:flex;flex-wrap:wrap;gap:0.3rem;margin-top:0.4rem;">
        {% for a in resume.allergies %}
        <span style="background:#fff3e0;color:#e65100;padding:0.2rem 0.6rem;border-radius:12px;font-size:0.75rem;font-weight:600;">⚠ {{ a }}</span>
        {% endfor %}
    </div>
    {% endif %}
</div>
{% endif %}

"""

# Insérer avant le bloc historique
TARGET = """<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.25rem;margin-bottom:1.5rem;">
    <div class="card">
        <div class="section-title">
            <i class="fa-solid fa-clock-rotate-left" style="color:var(--teal);"></i>
            Historique consultations
        </div>"""

if TARGET in content:
    content = content.replace(TARGET, RAPPORT_HTML + TARGET)
    print("✅ Rapport + Résumé ajoutés au debriefing")
else:
    print("⚠️ Bloc historique non trouvé")

with open(FILE, 'w') as f:
    f.write(content)
print("🎉 debriefing.html patchée")
