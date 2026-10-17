# MediGo — Plateforme de téléconsultation médicale intelligente

![Statut : prototype académique](https://img.shields.io/badge/statut-prototype_acad%C3%A9mique-orange)
![Projet : PFA 2025–2026](https://img.shields.io/badge/PFA-2025%E2%80%932026-blue)
![Plateforme : Raspberry Pi 4B](https://img.shields.io/badge/plateforme-Raspberry_Pi_4B-C51A4A)
![Interface : FR / AR](https://img.shields.io/badge/interface-FR_%2F_AR-008080)

> Un kit de télémédecine associant logiciel, intelligence artificielle et capteurs IoT, conçu autour d’un **Raspberry Pi 4B** pour explorer l’accès aux soins à distance dans les zones rurales marocaines.

**Projet de Fin d’Année 2025–2026 — Génie Digital en Santé, UM6SS / ESM6ISS**  

> [!WARNING]
> **Prototype académique : aucun usage public ou clinique réel autorisé dans le cadre de ce projet.** MediGo n’est pas présenté comme un dispositif médical validé. Les suggestions de l’IA, mesures des capteurs, rapports et ordonnances de démonstration ne doivent pas servir à prendre une décision médicale réelle. Le prototype ne constitue pas un service d’urgence.

## Sommaire

- [Contexte et objectifs](#contexte-et-objectifs)
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Technologies](#technologies)
- [Installation](#installation)
- [Matériel et boîtier](#matériel-et-boîtier)
- [Captures et schéma](#captures-et-schéma)
- [Tests et mesures rapportés](#tests-et-mesures-rapportés)
- [Sécurité et confidentialité](#sécurité-et-confidentialité)
- [Perspectives](#perspectives)
- [Équipe](#équipe)
  

## Contexte et objectifs

MediGo s’inscrit dans une démarche académique visant à réduire les obstacles d’accès à la consultation dans les territoires éloignés des pôles de soins. Le projet explore un kit portable réunissant :

- une communication à distance entre patient et médecin ;
- l’acquisition de signes vitaux par capteurs IoT ;
- une aide au raisonnement diagnostique intégrant des paramètres de prévalence marocaine ;
- un dossier patient structuré ;
- la génération de rapports de consultation et d’ordonnances de démonstration.

Le kit nécessite une alimentation électrique et, pour les fonctions à distance, une connexion réseau adaptée. Son autonomie sur batterie et son fonctionnement hors ligne ne sont pas établis.

## Fonctionnalités

### Téléconsultation

- **Cycle de vie contrôlé** : machine à états avec les états `en_attente`, `acceptee`, `en_cours`, `cloturee` et `expiree`. Les transitions exactes et les conditions d’expiration doivent être confirmées dans le code.
- **Priorité au médecin traitant** : délai annoncé de 90 secondes avant diffusion de la demande aux autres médecins disponibles.
- **Visioconférence WebRTC** : signalisation SDP et négociation ICE ; configuration annoncée de 2 serveurs STUN et 4 serveurs TURN. Selon le réseau, les médias peuvent passer par un relais TURN.
- **Chat temps réel** : WebSocket via Django Channels, persistance des messages et partage de photos médicales depuis la caméra arrière de la tablette.

### IoT et signes vitaux

| Capteur | Mesures visées | Adresse I2C annoncée |
|---|---|---|
| MAX30102 | SpO₂ et fréquence cardiaque par photopléthysmographie | `0x57` |
| MLX90614 | Température infrarouge sans contact | `0x5A` |

Le médecin active les capteurs depuis son interface. Le script embarqué `reader.py` est décrit comme interrogeant les capteurs toutes les **2 secondes**, puis transmettant les mesures par POST à l’API Django. Le serveur les enregistre et les diffuse aux interfaces par WebSocket.

Les mesures constituent des données expérimentales. La température mesurée et l’estimation de la SpO₂ dépendent notamment du montage, de l’algorithme, de l’étalonnage et des conditions d’acquisition ; aucune précision clinique générale n’est établie ici.

### Intelligence artificielle : aide au raisonnement diagnostique

Le moteur décrit combine une base de connaissances et un modèle XGBoost :

```text
Score hybride = 0,70 × score de la base de connaissances + 0,30 × score XGBoost
```

Un ajustement par des coefficients de prévalence marocaine est ensuite annoncé. Ces pondérations décrivent une méthode de calcul ; elles ne mesurent pas la fiabilité clinique et les scores ne sont pas présentés comme des probabilités calibrées.

- Base annoncée : plus de 100 maladies, 213 symptômes, plus de 200 synonymes médicaux, 14 signaux d’alerte (« red flags ») et plus de 50 coefficients de prévalence marocaine.
- Normalisation du texte libre par correspondance exacte puis approximative (*fuzzy matching*), avec suggestions en cas de correspondance insuffisante.
- Alertes prioritaires sur certaines combinaisons de symptômes, indépendamment du score.
- Le service d’inférence fourni retourne jusqu’à **10 hypothèses diagnostiques** et des questions complémentaires (`merged[:10]`). L’affichage annoncé de quatre hypothèses dans l’interface reste à confirmer.
- Modèle XGBoost décrit initialement avec **228 variables**, entraîné sur des **données synthétiques issues de la base de connaissances**. La dimension effective du modèle enregistré reste à vérifier.

Le fichier `medigo_features.py` fourni concatène le vecteur retourné par `vectoriser_symptomes` avec **15 variables patient** : âge, deux indicateurs de sexe, grossesse, six mesures vitales et cinq indicateurs d’antécédents. Plusieurs valeurs sont numériques et normalisées ; le vecteur complet ne doit donc pas être décrit comme entièrement binaire. Si le vecteur de symptômes comporte effectivement 213 composantes, le total serait de 228, mais cette dimension doit encore être confirmée dans la base de connaissances et le modèle enregistré. Le paramètre facultatif `expected_num_symptom_features` contrôle la longueur du vecteur de symptômes lorsqu’il est renseigné.

Les données numériques absentes ou non convertibles sont remplacées par zéro dans les 15 variables patient ; la gestion des valeurs manquantes, les unités, les bornes et leur cohérence avec l’entraînement restent à documenter. Les sources, dates et méthodes de construction des coefficients de prévalence doivent également être précisées. La génération synthétique à partir de la même base ne constitue pas une validation sur une population clinique indépendante. Les alertes ne garantissent pas la détection de toutes les urgences.

#### Écarts observés dans le service d’inférence fourni

- Les constantes exécutées fixent les poids à **70 % / 30 %** ; certains commentaires indiquent encore 65 % / 35 % et doivent être actualisés.
- `joblib.load` charge le modèle enregistré, puis le service appelle `predict_proba`. Aucun import direct de XGBoost n’est présent ; la dépendance effective dépend de la classe sérialisée dans le modèle.
- Si la prédiction du modèle échoue, le service journalise un avertissement et retourne des résultats issus des règles seules. Un résultat affiché ne démontre donc pas que la branche XGBoost a fonctionné. NumPy étant importé au niveau du module, son absence peut empêcher le chargement du service avant ce mécanisme de repli.
- Dans `build_patient_context`, la température, la SpO₂ et la fréquence cardiaque sont explicitement fixées à `None`. Leur alimentation par les capteurs ou une saisie manuelle n’est pas implémentée dans ce passage, malgré les objectifs décrits pour le projet.
- Les scores issus des règles sont multipliés par les coefficients de prévalence avant fusion, puis le score hybride est multiplié à nouveau dans `merge_scores`. Cette double application au terme issu des règles doit être examinée avant de présenter la formule simplifiée comme une description exacte du calcul.

Ces constats proviennent d’une lecture du service partagé, sans exécution ni inspection du modèle sérialisé.

### Dossier patient et rapports

- Vue longitudinale : antécédents, allergies, IMC, tension et historique des consultations.
- Accès décrit pour le médecin et le patient, sous réserve des autorisations applicatives.
- Rapport généré à la clôture : identité, symptômes, diagnostic et traitement saisis.

La génération automatique d’un document n’établit ni son exactitude ni sa validation médicale.

### Ordonnances numériques de démonstration

- Base pharmaceutique marocaine désignée « AMMPS » dans la description ; source exacte, version, droits de réutilisation et fréquence de mise à jour à documenter.
- Autocomplétion AJAX à partir de deux caractères, par nom commercial ou DCI.
- Suggestions selon le diagnostic, avec posologie, durée et notes par médicament.
- PDF A4 produit avec ReportLab, cachet graphique dynamique et QR code contenant une URL de consultation du document.
- Accès patient décrit par code à six chiffres, sans création de compte.

> Un cachet graphique et un QR code ne prouvent pas, à eux seuls, l’authenticité d’une ordonnance, l’identité du prescripteur ou l’existence d’une signature électronique. Les documents du prototype doivent être clairement identifiés comme des démonstrations, sans valeur de prescription réelle.

### Administration et interface

- Gestion des comptes médecins et patients et affectation du médecin traitant.
- Génération de codes à six chiffres et tableau de bord global.
- Interface patient en **français et arabe**, affichage RTL et police Cairo.
- Plus de 90 clés de traduction annoncées et langue conservée en session.
- Modification du statut du médecin en AJAX et actualisation par WebSocket.

## Architecture

Architecture logique à trois couches : interfaces clientes, serveur applicatif et stockage. La pile serveur est décrite comme hébergée sur un **Raspberry Pi 4B avec 4 Go de RAM**. La tablette sert de terminal ; les capteurs sont reliés au bus I2C du Raspberry Pi.

### Services décrits dans Docker Compose

| Conteneur annoncé | Image ou environnement annoncé | Port annoncé* | Rôle |
|---|---|---|---|
| `medigo_django` | Python 3.11, Uvicorn | 8000 | Application ASGI : Django et Channels |
| `medigo_db` | PostgreSQL 15 Alpine | 5432 | Base de données relationnelle |
| `medigo_redis` | Redis 7 Alpine | 6379 | Couche de communication Channels et cache |
| `medigo_nginx` | Nginx Alpine | 80 | Reverse proxy et fichiers statiques |

*Le fichier Compose fourni ne publie que le port `80:80` de Nginx. Aucun port hôte n’est déclaré pour Django, PostgreSQL ou Redis. Les services partagent le réseau bridge `teleconsultation_net` ; cela ne constitue pas un isolement vis-à-vis de l’hôte ou des autres services de ce réseau.*

Les noms de services Compose sont `postgres`, `redis`, `django` et `nginx`. PostgreSQL conserve ses données dans le volume nommé `postgres_data`. Les médias sont montés depuis `./media`, et Nginx sert les fichiers statiques depuis `./backend/static_collected`. Le dossier `./backend` est monté dans `/app` pour Django.

Le démon `cloudflared` est décrit comme installé directement sur le Raspberry Pi pour établir un tunnel sortant vers Cloudflare. Ce choix vise à éviter une ouverture entrante sur le routeur. La configuration TLS, le trajet entre les composants et les règles d’accès doivent être vérifiés ; le tunnel ne suffit pas à sécuriser l’application.

Un démarrage d’environ **45 secondes** et une consommation d’environ **2,1 Go de RAM** sont rapportés, sans protocole de mesure fourni.

### Configuration Nginx examinée

Le contenu Nginx fourni définit un serveur HTTP sur le port 80 et relaie les requêtes applicatives vers `django:8000`. Le chemin `/ws/` transmet les en-têtes de mise à niveau WebSocket et utilise des délais de lecture, d’envoi et de connexion de 3 600 secondes. La taille maximale du corps des requêtes est fixée à `20M`.

Les fichiers `/static/` et `/media/` sont servis directement par des directives `alias`. **Aucun contrôle d’accès n’est défini dans le bloc `/media/` fourni** : un fichier existant dont l’URL est connue peut être servi sans passer par les autorisations Django, sauf protection externe non fournie. Cela concerne potentiellement les pièces jointes du chat, images, ordonnances et QR codes. L’absence de liste de répertoire ne constitue pas une protection de ces fichiers. Avant toute exposition de données sensibles, remplacer ce service direct par un mécanisme de téléchargement autorisé, par exemple une vérification Django suivie d’une redirection interne Nginx vers un emplacement `internal`.


## Technologies

### Dépendances du serveur vérifiées dans les fichiers fournis

Le Dockerfile utilise `python:3.11-slim`, définit `/app` comme répertoire de travail, installe `gcc` et `libpq-dev`, puis installe les dépendances depuis `requirements.txt` avant de copier le code. Il déclare `EXPOSE 8000`, ce qui ne publie pas le port sur l’hôte. Il ne définit ni `CMD` ni `ENTRYPOINT` : la commande de démarrage est fournie par Compose.

| Dépendance | Version déclarée |
|---|---|
| Django | 4.2.9 |
| Django REST framework | 3.14.0 |
| Channels / channels-redis | 4.0.0 / 4.1.0 |
| psycopg2-binary | 2.9.9 |
| Uvicorn avec extras `standard` | 0.27.0 |
| Gunicorn | 21.2.0 |
| python-dotenv | 1.0.0 |
| Pillow | 10.2.0 |
| Simple JWT | 5.3.1 |
| ReportLab / qrcode | 4.1.0 / 7.4.2 |
| django-fsm | 2.8.1 |
| WhiteNoise | 6.6.0 |

Gunicorn et WhiteNoise sont déclarés comme dépendances ; leur installation ne prouve pas leur utilisation. Compose lance Uvicorn. Le Dockerfile ne définit pas d’utilisateur applicatif non privilégié : en l’absence d’une autre configuration, le processus utilise l’utilisateur par défaut de l’image.

### Ensemble de technologies décrit par l’équipe

| Domaine | Technologies annoncées |
|---|---|
| Serveur | Python 3.11, Django 4.2, Django Channels, Uvicorn |
| Temps réel | WebSocket, WebRTC, STUN / TURN |
| Données | PostgreSQL 15, Redis 7 ; 17 entités et clés UUID annoncées |
| IA | Base de connaissances, XGBoost, recherche approximative |
| IoT | Raspberry Pi 4B, MAX30102, MLX90614, I2C |
| Documents | ReportLab, bibliothèque `qrcode`, base pharmaceutique |
| Interface | Templates Django, AJAX, FR / AR, RTL, Cairo |
| Infrastructure | Docker, Docker Compose, Nginx, Cloudflare Tunnel |
| Boîtier | Shapr3D et impression 3D en PLA |

Ces versions reprennent la description initiale ; elles ne constituent pas une recommandation de versions maintenues ou une vérification des dépendances installées.

## Installation

> [!IMPORTANT]
> **Vérification partielle, sans exécution.** Le dépôt a été consulté sur main au commit c5db2dda7ddccdaaf926db27b873495dc0869150 : arborescence, Compose, dépendances serveur et lecteur de capteurs. Les paramètres Django, Nginx, Dockerfile et le service IA ont aussi été examinés à partir des textes fournis. Aucun démarrage complet ni test matériel ne sont attestés.

### Prérequis à confirmer

- Accès au dépôt GitHub exact et à sa documentation.
- Docker et Docker Compose compatibles avec la plateforme cible, notamment ARM64 sur Raspberry Pi.
- Pour l’IoT : Raspberry Pi, bus I2C activé, câblage vérifié et dépendances du lecteur de capteurs.
- Pour l’accès distant : configuration du tunnel, du domaine et des services STUN / TURN réellement utilisés.

### Préparer le dossier de démarrage

Le dépôt est privé : une authentification GitHub autorisée est nécessaire pour le cloner.

```bash
git clone https://github.com/AyaA-23/MediGo.git
cd MediGo/medigo_full/medigo
```

Cette arborescence correspond au dossier local indiqué par l’équipe ; l’adapter si la racine du dépôt est différente. Le dossier courant doit contenir `docker-compose.yml`, `backend`, `nginx` et le fichier de configuration local `.env`.

Compose charge `.env` pour PostgreSQL et Django. Les variables suivantes sont explicitement référencées :

```bash
SECRET_KEY=<CLE_DJANGO_ALEATOIRE_LONGUE>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=<NOM_DE_BASE>
DB_USER=<UTILISATEUR_DE_BASE>
DB_PASSWORD=<MOT_DE_PASSE_FORT>
DB_HOST=postgres
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
```

Ces variables correspondent aux accès à l’environnement observés dans les paramètres Django et Compose fournis. Les valeurs entre chevrons doivent être remplacées. `postgres` et `redis` sont les noms des services accessibles depuis le conteneur Django ; ils ne conviennent pas nécessairement à une exécution directe sur l’hôte. Ajouter à `ALLOWED_HOSTS` l’adresse IP ou le domaine réellement utilisé, sans protocole et sans espace après les virgules. Éviter `*`. Les autres modules peuvent nécessiter des variables supplémentaires. Aucun fichier `.env.example` n’a été confirmé. Ne pas remplacer une configuration existante sans en préserver les valeurs utiles.

Les origines CSRF sont définies en dur dans `config/settings.py` ; elles ne sont pas lues depuis une variable d’environnement dans le code partagé. Adapter cette liste aux origines réelles, avec leur protocole. Elle contient notamment une IP locale fixe et `https://*.trycloudflare.com` : limiter les origines de confiance aux besoins de la démonstration.

## Matériel et boîtier

### Lecteur de capteurs consulté dans le dépôt

Le script calcule une estimation de SpO₂ par formule empirique et la borne entre 70 et 100 ; ce bornage n’atteste pas une précision clinique. Le calcul du pouls utilise une fréquence supposée de 25 échantillons/s, tandis que les commentaires d’initialisation indiquent 100 échantillons/s sans moyennage. La cohérence entre configuration matérielle, lecture FIFO, fréquence effective et calcul du pouls nécessite une vérification sur le matériel avant de retenir les résultats annoncés.

Le kit décrit comprend un Raspberry Pi 4B, un MAX30102, un MLX90614, une alimentation USB-C et une tablette Samsung A7 Lite.

Le boîtier est conçu avec Shapr3D et imprimé en PLA : logement principal, supports, passages de câbles I2C, ventilation et accès aux ports et aux capteurs. Le texte initial cite un gabarit de **85,6 × 56,5 × 17 mm** pour le Raspberry Pi ; les dimensions mécaniques et jeux d’assemblage doivent être vérifiés avant fabrication.

Les fichiers CAO, modèles d’impression, schémas de câblage et nomenclature détaillée restent à référencer lorsqu’ils seront disponibles.

## Captures et schéma

Les emplacements suivants sont réservés à de vrais visuels du projet. 

| Visuel à ajouter | Contenu attendu |
|---|---|
| Architecture globale | Clients, tunnel, reverse proxy, application, données et capteurs |
| Interface patient | Parcours de demande de consultation |
| Interface médecin | Consultation, chat et mesures IoT |
| Aide au diagnostic | Hypothèses et alertes sur un cas fictif |
| Rapport et ordonnance | Documents de démonstration avec données fictives |
| Interface arabe | Exemple RTL |
| Kit et boîtier | Montage réel et disposition des capteurs |

## Tests et mesures rapportés



| Module | Identifiants annoncés | Nombre d’identifiants | Résultat rapporté, non vérifié |
|---|---|---:|---|
| Téléconsultation | T1 à T6 | 6 | 6/6 |
| Visioconférence WebRTC | T7 à T10 | 4 | 4/4 |
| IoT et capteurs | T11 à T13 | 3 | 3/3 |
| Intelligence artificielle | T14 à T16 | 3 | 3/3 |
| Ordonnances et PDF | T17 à T20 | **4** | **7/7 — divergence à expliquer** |
| Internationalisation et UX | T21 à T29 | 9 | 9/9 |
| Déploiement Docker | T30 à T33 | 4 | 4/4 |
| **Total** | **T1 à T33** | **33** | **36/36 par addition des lignes** |

Il faut consulter le plan de tests et les rapports d’exécution pour déterminer s’il s’agit de sous-tests, d’une erreur de résultat ou d’une erreur de numérotation. **Aucun total validé ni taux de réussite global n’est retenu dans ce README.** Aucun test n’a été exécuté pour sa rédaction.

### Performances et comparaison des capteurs

Les valeurs suivantes sont rapportées dans la description initiale, sans journaux, taille d’échantillon ou protocole joints :

| Mesure | Valeur rapportée | Seuil ou tolérance mentionné dans le projet |
|---|---|---|
| Latence entre mesure et affichage | Environ 46 ms | 500 ms |
| SpO₂ : écart par rapport à la référence | −1 point de pourcentage | ±2 points de pourcentage |
| Fréquence cardiaque : écart | +2 battements/minute | ±3 battements/minute |
| Température : écart | +0,2 °C | ±0,5 °C |

La description mentionne une comparaison à un oxymètre certifié et à un thermomètre clinique, sans identifier ces instruments. Les tolérances sont celles annoncées pour le projet ; aucune conformité à une norme n’est établie.

La latence de 46 ms doit être distinguée de l’intervalle d’acquisition de 2 secondes : elle ne démontre pas une actualisation des mesures toutes les 46 ms. Le point de départ du chronométrage, les conditions réseau et la distribution des latences restent à préciser.

## Sécurité et confidentialité

### Mécanismes décrits

- Clés primaires UUID sur les entités.
- Accès HTTPS via Cloudflare Tunnel.
- JWT d’une durée de vie annoncée de cinq minutes pour certains appels API du médecin.

Ces mécanismes n’ont pas été audités. Un UUID ne remplace pas un contrôle d’autorisation ; un JWT court ne suffit pas à garantir la sécurité d’une session ; HTTPS ne prouve pas le chiffrement des données au repos ou de bout en bout sur l’ensemble du système.

### Conditions à vérifier avant toute exposition réseau

La lecture du `settings.py` fourni confirme l’authentification JWT et la permission `IsAuthenticated` par défaut pour Django REST framework. Cela ne prouve pas les contrôles par objet ni la protection des vues Django et WebSocket ; les vues peuvent aussi modifier ces valeurs. WhiteNoise est présent dans les middlewares et configuré pour les fichiers statiques. `DEBUG` vaut faux par défaut et la clé secrète provient de l’environnement.

Aucun réglage explicite `SIMPLE_JWT` ne figure dans ce fichier : la durée de cinq minutes reste une valeur annoncée, sans personnalisation attestée ici. Aucun réglage explicite `SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` ou `SECURE_SSL_REDIRECT` n’y apparaît. Vérifier ces paramètres avec la chaîne de proxy et de tunnel réelle avant d’activer des redirections HTTPS, afin d’éviter une mauvaise détection du protocole ou une boucle de redirection. Le fichier ne permet pas de conclure que les sessions sont sécurisées pour une exposition publique.

- **Autorisations** : contrôler l’accès à chaque dossier, consultation, message, mesure, PDF et connexion WebSocket selon l’identité et le rôle.
- **Codes à six chiffres** : prévoir expiration, limitation des tentatives, protection contre l’énumération et révocation. Un code de cette taille ne doit pas être l’unique protection durable de données de santé.
- **QR codes et liens** : limiter leur portée et leur durée de validité ; éviter les données personnelles directement encodées et les documents accessibles sans contrôle adapté.
- **Secrets** : exclure clés, mots de passe, jetons, identifiants TURN et fichiers d’environnement du dépôt ; renouveler tout secret exposé.
- **Configuration** : vérifier le mode de débogage, les hôtes et origines autorisés, les cookies, la protection CSRF, l’authentification IoT et l’exposition des ports. PostgreSQL et Redis doivent rester sur un réseau privé approprié.
- **Données** : définir conservation, suppression, journalisation, sauvegardes et restauration ; éviter les données sensibles dans les journaux.
- **Dépendances** : vérifier les versions maintenues, les mises à jour et les vulnérabilités des images et bibliothèques.

Ces points sont des vérifications attendues, **pas des protections dont l’implémentation est attestée**. Utiliser des données fictives pour les démonstrations. Aucun audit de sécurité, agrément ou conformité réglementaire relative aux données de santé n’est revendiqué ici.

## Perspectives

### Perspectives envisagées

- Intégration de capteurs supplémentaires : ECG, tensiomètre et glucomètre connecté.
- Application mobile native et exploration de fonctions hors ligne.
- Prise de rendez-vous et suivi après consultation.
- Étude d’un pilote avec un dispensaire rural partenaire de l’UM6SS, sous réserve des validations et autorisations nécessaires. Aucun pilote réalisé n’est revendiqué.

## Équipe

| Membre | Responsabilités annoncées |
|---|---|
| **OUAKIL Zakaria** | Architecture globale, temps réel, IoT, boîtier 3D et déploiement |
| **ADRIF Aya** | Base de données, infrastructure Docker, intelligence artificielle et rapports médicaux |
| **GUIHIA Imane** | UX/UI, ordonnances numériques, PDF / QR code et internationalisation FR / AR |

