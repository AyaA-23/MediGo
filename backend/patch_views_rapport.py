#!/usr/bin/env python3
"""
Patch — Ajouter le rapport auto au debriefing et voir_consultation
"""

FILE = '/app/apps/consultations/views.py'
with open(FILE, 'r') as f:
    content = f.read()

# 1. Ajouter l'import du service rapport
if 'rapport_service' not in content:
    content = content.replace(
        'from apps.ordonnances.models import Ordonnance',
        'from apps.ordonnances.models import Ordonnance\nfrom apps.consultations.services.rapport_service import generer_rapport_consultation, generer_resume_patient',
        1
    )
    print("✅ Import rapport_service ajouté")

# 2. Ajouter rapport + resume au contexte debriefing
OLD_DEBRIEF = """    return render(request, 'medecin/debriefing.html', {
        'consultation': consultation,
        'patient': patient,
        'historique': historique,
        'maladies': maladies,
        'ordonnances': ordonnances,
        'derniers_signes': derniers_signes,
    })"""

NEW_DEBRIEF = """    # Générer le rapport de consultation et résumé patient (100% local)
    rapport = generer_rapport_consultation(consultation)
    resume = generer_resume_patient(patient)

    return render(request, 'medecin/debriefing.html', {
        'consultation': consultation,
        'patient': patient,
        'historique': historique,
        'maladies': maladies,
        'ordonnances': ordonnances,
        'derniers_signes': derniers_signes,
        'rapport': rapport,
        'resume': resume,
    })"""

if OLD_DEBRIEF in content:
    content = content.replace(OLD_DEBRIEF, NEW_DEBRIEF)
    print("✅ Debriefing: rapport + résumé ajoutés au contexte")

with open(FILE, 'w') as f:
    f.write(content)
print("🎉 views.py patchée")
