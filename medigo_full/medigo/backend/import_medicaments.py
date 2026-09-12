import csv
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/app')
django.setup()

from apps.ordonnances.models import Medicament

# Vider les anciens
deleted = Medicament.objects.all().delete()
print(f"Nettoyé: {deleted}")

CSV_PATH = '/tmp/medicaments.csv'

def clean(val):
    return val.strip() if val else ''

def trunc(val, length):
    return val[:length] if val else ''

def import_medicaments():
    created = 0
    skipped = 0
    seen = set()

    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            statut_amm = clean(row.get('STATUT AMM', ''))
            statut_com = clean(row.get('STATUT COMMERCIALISATION', ''))

            if 'ENREGISTREE' not in statut_amm:
                skipped += 1
                continue
            if 'Commercialis' not in statut_com and 'Commrcialisé' not in statut_com:
                skipped += 1
                continue

            nom = clean(row.get('SPECIALITE', ''))
            dosage = clean(row.get('DOSAGE', ''))
            forme = clean(row.get('FORME', ''))
            dci = clean(row.get('SUBSTANCE ACTIVE', ''))
            categorie = clean(row.get('CLASSE THERAPEUTIQUE', ''))

            if not nom:
                skipped += 1
                continue

            key = f"{nom}|{dosage}|{forme}".upper()
            if key in seen:
                skipped += 1
                continue
            seen.add(key)

            if categorie in ('NA', '0', ''):
                categorie = 'Autre'

            Medicament.objects.create(
                nom=trunc(nom.title(), 200),
                dci=trunc(dci.title(), 500),
                forme=trunc(forme.title(), 200),
                dosage=trunc(dosage, 100),
                categorie=trunc(categorie.title(), 500),
            )
            created += 1

    print(f"Imported: {created} medicaments, skipped: {skipped}")

if __name__ == '__main__':
    import_medicaments()
