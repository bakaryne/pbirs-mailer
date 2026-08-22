# Kit de communication — PBIRS Mailer v1.0.0

Remplacez uniquement les marqueurs entre crochets avant publication.

## Description courte du dépôt GitHub

Automate Power BI Report Server page captures and email delivery with Python,
Playwright and Microsoft Edge. Windows-friendly, configurable and testable.

## Présentation GitHub en français

PBIRS Mailer est un outil Python open source qui ouvre une page Power BI Report Server,
attend la fin de son rendu, crée une capture PNG et l'envoie dans le corps d'un email.
La V1 privilégie une installation Windows simple, une configuration externe au code et
des tests progressifs avant tout envoi réel.

## Sujets GitHub suggérés

`power-bi` · `power-bi-report-server` · `playwright` · `python` · `automation` ·
`reporting` · `smtp` · `windows`

## Titre de la release GitHub

PBIRS Mailer v1.0.0 — première version stable

## Notes de release GitHub

PBIRS Mailer v1.0.0 automatise la capture d'une page Power BI Report Server et son
envoi sous forme d'image intégrée à un email.

### Fonctionnalités

- installation guidée sous Windows avec Python 3.10 ou plus récent ;
- prise en charge de PowerShell, CMD et des chemins réseau UNC ;
- navigation par identifiant interne ou libellé visible ;
- attente de stabilisation du rendu Power BI ;
- capture silencieuse avec Microsoft Edge ;
- envoi SMTP avec image intégrée ;
- plusieurs souscriptions indépendantes ;
- modes `--dry-run`, `--no-send`, `--headed` et `--verbose` ;
- journaux tournants et captures de diagnostic ;
- tests automatisés sous Linux et Windows.

### Démarrage rapide

```powershell
.\setup.cmd
.\run.cmd --dry-run
.\run.cmd --no-send
```

Copiez et adaptez uniquement `config.example.json`. Ne publiez jamais votre
`config.json`, vos captures ou vos journaux.

### Limites connues

- pas d'interface graphique ;
- pas de gestionnaire de secrets intégré ;
- une souscription par page à capturer ;
- navigation à valider selon la version et la structure du rapport PBIRS.

Documentation complète : [LIEN_DU_DEPOT_GITHUB]

## Publication LinkedIn

Je publie aujourd'hui **PBIRS Mailer v1.0.0**, un projet Python open source conçu pour
automatiser l'envoi de captures de rapports Power BI Report Server.

Le principe : ouvrir une page de rapport avec Playwright et Microsoft Edge, attendre
que les visuels soient chargés, créer une capture PNG puis l'intégrer directement dans
un email.

Le passage du POC à cette première version m'a surtout permis de travailler sur les
sujets qui rendent un outil réellement utilisable : installation Windows, chemins UNC,
versions de Python, navigation entre les pages, encodage de configuration, logs, modes
de test et protection des informations sensibles.

La V1 propose notamment :

✅ une installation guidée sous Windows  
✅ une capture silencieuse en arrière-plan  
✅ une navigation vers une page précise  
✅ plusieurs abonnements indépendants  
✅ un envoi SMTP avec l'image intégrée  
✅ des tests automatisés et une documentation complète

Le projet est disponible sous licence MIT : [LIEN_DU_DEPOT_GITHUB]

J'ai également détaillé la démarche technique dans cet article : [LIEN_MEDIUM]

Les retours d'expérience sur Power BI Report Server et l'automatisation on-premises
sont les bienvenus.

#PowerBI #PowerBIReportServer #Python #Playwright #BusinessIntelligence #OpenSource
#DataEngineering

## Publication LinkedIn courte

Je publie **PBIRS Mailer v1.0.0**, un outil Python open source qui automatise la capture
d'une page Power BI Report Server et son envoi par email.

Cette première version met l'accent sur une installation Windows simple, la navigation
entre les pages, la capture silencieuse, les tests progressifs et la protection des
configurations sensibles.

Dépôt : [LIEN_DU_DEPOT_GITHUB]  
Article : [LIEN_MEDIUM]

#PowerBI #Python #Playwright #OpenSource #BusinessIntelligence

## Texte d'annonce interne

Une première version de PBIRS Mailer est disponible pour test. Elle permet d'ouvrir
automatiquement une page Power BI Report Server, d'en créer une capture et de l'envoyer
par email.

Avant toute utilisation, le test doit être réalisé avec un rapport non sensible, un
seul destinataire et l'envoi SMTP désactivé. La documentation décrit ensuite les étapes
de validation progressive.

Documentation : [LIEN_DU_DEPOT_OU_DU_DOSSIER]

## Ordre de publication recommandé

1. Créer le dépôt GitHub et pousser la version nettoyée.
2. Vérifier le résultat de GitHub Actions.
3. Créer le tag et la release `v1.0.0`.
4. Remplacer `[LIEN_DU_DEPOT_GITHUB]` dans l'article Medium.
5. Publier l'article Medium.
6. Ajouter `[LIEN_MEDIUM]` dans la publication LinkedIn.
7. Publier le post LinkedIn avec une capture entièrement synthétique.

