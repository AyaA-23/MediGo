#!/usr/bin/env python3
"""
Ajoute la pondération par prévalence Maroc au scoring hybride.
Basé sur les données IHME GBD, Ministère de la Santé Maroc, et OMS:
- Diabète: 10.7% adultes | HTA: 19.5% adultes
- Infections respiratoires: 1er motif de consultation
- Maladies diarrhéiques: 2ème cause infectieuse
- NCDs: majorité des décès (cardiovasculaire, diabète)
"""

FILE = '/app/apps/consultations/services/medigo_ai_service.py'
with open(FILE, 'r') as f:
    content = f.read()

# Vérifier si déjà appliqué
if 'PREVALENCE_MAROC' in content:
    print("⚠️ Prévalence déjà présente — mise à jour...")
    # Supprimer l'ancien bloc
    import re
    content = re.sub(
        r'# -{10,}\n# Prévalence Maroc[\s\S]*?PREVALENCE_MAROC = \{[\s\S]*?\}\s*\n',
        '',
        content
    )

PREVALENCE_BLOCK = '''# ---------------------------------------------------------------------------
# Prévalence Maroc — Source: IHME GBD, OMS, Min. Santé Maroc
# Maladies courantes boostées, rares pénalisées
# ---------------------------------------------------------------------------
PREVALENCE_MAROC = {
    # ══════════════════════════════════════════════════════════════
    # TRÈS COURANTES — 1ers motifs de consultation au Maroc (×1.5)
    # ══════════════════════════════════════════════════════════════
    'Grippe / Syndrome grippal': 1.6,
    'COVID-19': 1.5,
    'Rhinopharyngite': 1.6,
    'Angine': 1.5,
    'Pharyngite': 1.5,
    'Rhume': 1.6,

    # Respiratoire courant
    'Bronchite aiguë': 1.45,
    'Sinusite': 1.4,
    'Otite moyenne aiguë': 1.4,
    'Laryngite': 1.35,

    # Digestif courant
    'Gastro-entérite aiguë': 1.5,
    'Toxi-infection alimentaire collective': 1.4,
    'Gastrite': 1.35,
    'Reflux gastro-œsophagien': 1.3,
    'Syndrome du côlon irritable': 1.25,
    'Ulcère gastrique': 1.2,

    # Douleur / MSK courant
    'Lombalgie commune': 1.4,
    'Arthrose': 1.35,
    'Cervicalgie': 1.3,
    'Sciatique': 1.25,
    'Tendinite': 1.3,

    # Dermatologie courante
    'Eczéma de contact': 1.35,
    'Dermatite atopique': 1.3,
    'Gale': 1.35,
    'Mycose cutanée / Dermatophytose': 1.35,
    'Acné': 1.3,
    'Urticaire': 1.25,
    'Impétigo': 1.2,

    # Urinaire courant
    'Infection urinaire basse / Cystite': 1.4,
    'Pyélonéphrite': 1.15,

    # Pédiatrie / infectieux courant Maroc
    'Bronchiolite': 1.3,
    'Conjonctivite': 1.35,
    'Varicelle': 1.2,
    'Rougeole': 1.15,
    'Scarlatine': 1.1,

    # Neurologie courante
    'Migraine': 1.4,
    'Céphalée de tension': 1.4,
    'Névralgie cervico-brachiale': 1.2,

    # ORL courant
    'Rhinite allergique': 1.35,

    # Gynéco courant
    'Vaginite / Vaginose': 1.3,
    'Infection génitale basse': 1.25,
    'Dysménorrhée primaire': 1.25,

    # ══════════════════════════════════════════════════════════════
    # MALADIES CHRONIQUES FRÉQUENTES au Maroc (×1.2-1.3)
    # HTA: 19.5% | Diabète: 10.7% de la population adulte
    # ══════════════════════════════════════════════════════════════
    'Hypertension artérielle': 1.3,
    'Diabète type 2': 1.3,
    'Diabète type 1': 1.1,
    'Asthme (crise)': 1.25,
    'BPCO (exacerbation)': 1.15,
    'Anémie ferriprive': 1.3,
    'Hypothyroïdie': 1.15,
    'Hyperthyroïdie': 1.1,
    'Goutte': 1.15,
    'Allergie alimentaire': 1.2,

    # ══════════════════════════════════════════════════════════════
    # STANDARD — pas de modification (×1.0 implicite)
    # Pneumonie, Appendicite, Cholécystite, etc.
    # ══════════════════════════════════════════════════════════════
    'Pneumonie communautaire': 1.1,
    'Appendicite': 1.05,
    'Cholécystite': 1.05,
    'Pancréatite aiguë': 1.0,
    'Diverticulite aiguë': 1.0,
    'Prostatite aiguë': 1.0,
    'Zona': 1.0,
    'Coqueluche': 1.0,

    # ══════════════════════════════════════════════════════════════
    # PEU COURANTES au Maroc (×0.7-0.85)
    # ══════════════════════════════════════════════════════════════
    'Brucellose': 0.7,
    'Fièvre typhoïde': 0.75,
    'Leishmaniose viscérale': 0.65,
    'Leishmaniose cutanée': 0.75,
    'Paludisme / Malaria': 0.7,
    'Leptospirose': 0.6,
    'Fièvre Q': 0.55,
    'Maladie de Crohn': 0.75,
    'Rectocolite hémorragique': 0.75,
    'Lupus érythémateux': 0.7,
    'Sclérodermie': 0.6,
    'Vascularite': 0.65,
    'Sarcoïdose': 0.6,
    'Mononucléose infectieuse': 0.8,
    'Tuberculose pulmonaire': 0.9,

    # ══════════════════════════════════════════════════════════════
    # RARES au Maroc (×0.4-0.6)
    # ══════════════════════════════════════════════════════════════
    'VIH primo-infection': 0.5,
    'Endocardite infectieuse': 0.5,
    'Myasthénie': 0.45,
    'Guillain-Barré': 0.45,
    'Phéochromocytome': 0.4,
    'Maladie de Behçet': 0.55,
    'Pemphigus': 0.4,
    'Purpura thrombopénique': 0.5,
    'Encéphalite': 0.55,
    'Convulsion fébrile': 0.7,
    'Myocardite': 0.5,
    'Péricardite aiguë': 0.6,
    'Embolie pulmonaire': 0.65,
}

'''

# Insérer avant WEIGHT_RULE_BASED
content = content.replace(
    'WEIGHT_RULE_BASED = 0.70',
    PREVALENCE_BLOCK + 'WEIGHT_RULE_BASED = 0.70'
)

# Ajouter l'application du facteur si pas déjà fait
if 'prevalence = PREVALENCE_MAROC' not in content:
    OLD = """        else:
            score_final = WEIGHT_RULE_BASED * score_rb + WEIGHT_XGBOOST * score_xgb

        if score_final < 0.01:"""

    NEW = """        else:
            score_final = WEIGHT_RULE_BASED * score_rb + WEIGHT_XGBOOST * score_xgb

        # Pondérer par la prévalence au Maroc
        prevalence = PREVALENCE_MAROC.get(nom, 1.0)
        score_final = score_final * prevalence

        if score_final < 0.01:"""
    content = content.replace(OLD, NEW)

# Augmenter top_k pour plus de candidats
content = content.replace('top_k=15', 'top_k=30')

with open(FILE, 'w') as f:
    f.write(content)

print('✅ Prévalence Maroc appliquée')
print('   - Très courantes (Grippe, Gastro, Angine): ×1.5-1.6')
print('   - Chroniques fréquentes (HTA, Diabète): ×1.2-1.3')
print('   - Standard: ×1.0')
print('   - Peu courantes (Brucellose, Leishmaniose): ×0.6-0.7')
print('   - Rares (VIH, Myasthénie): ×0.4-0.5')
print('   - top_k: 30 (plus de candidats)')
