# Automatiser l'envoi de captures Power BI Report Server avec Python et Playwright

Dans certaines organisations, les rapports Power BI restent volontairement hébergés
sur une infrastructure interne. [Power BI Report Server](https://learn.microsoft.com/en-us/power-bi/report-server/get-started)
répond à ce besoin en proposant un portail de rapports on-premises accessible depuis un
navigateur.

Mais un besoin simple revient souvent : envoyer régulièrement par email la vue exacte
d'une page de rapport, directement visible dans le corps du message.

Les [abonnements natifs de Reporting Services](https://learn.microsoft.com/en-us/sql/reporting-services/working-with-subscriptions-web-portal)
restent utiles et sont bien disponibles avec Power BI Report Server. Ils ne couvrent
toutefois pas forcément un scénario très
personnalisé : ouvrir une page précise d'un rapport interactif, attendre que ses visuels
soient réellement chargés, produire une image et l'intégrer à un email existant.

C'est pour expérimenter cette approche que j'ai créé **PBIRS Mailer**, un projet Python
open source basé sur Playwright.

> Le dépôt public contient uniquement des exemples fictifs. Aucune URL, adresse,
> capture ou donnée issue d'un environnement réel ne doit y être publiée.

## Le principe

PBIRS Mailer reproduit le parcours d'un utilisateur dans un navigateur :

1. ouvrir Microsoft Edge avec Playwright ;
2. accéder au rapport avec l'authentification Windows du compte d'exécution ;
3. atteindre la page demandée ;
4. attendre la stabilisation des requêtes de données ;
5. créer une capture PNG ;
6. intégrer l'image dans un email HTML ;
7. envoyer le message par un relais SMTP.

Playwright sait piloter des navigateurs basés sur Chromium ainsi que des navigateurs
distribués comme Microsoft Edge, comme l'indique sa
[documentation officielle](https://playwright.dev/python/docs/browsers).

Le projet utilise également le paramètre `rs:embed=true`, documenté par Microsoft pour
[intégrer un rapport Power BI Report Server dans une iframe](https://learn.microsoft.com/en-us/power-bi/report-server/quickstart-embed).
Il permet d'obtenir un affichage plus adapté à la capture. Il peut être retiré lorsqu'on
souhaite conserver les éléments de navigation du portail dans l'image.

## Pourquoi attendre les requêtes de données ?

Attendre uniquement le chargement HTML n'est pas suffisant. La structure de la page
peut être présente alors que les visuels Power BI continuent à interroger le modèle.
Une capture prise trop tôt contient alors des zones vides ou des indicateurs encore en
cours de chargement.

La V1 surveille donc les réponses réseau contenant `querydata`. Après la navigation,
elle attend une période sans nouvelle réponse avant de déclencher la capture. Un délai
maximal évite qu'un rapport très actif bloque indéfiniment l'exécution.

Cette approche reste une heuristique : elle doit être validée sur les rapports et la
version de Power BI Report Server réellement utilisés.

## Une configuration externe au code

Les informations d'exécution sont placées dans `config.json`, ignoré par Git. Le dépôt
fournit seulement un `config.example.json` fictif :

```json
{
  "version": 1,
  "browser": {
    "channel": "msedge",
    "headless": true,
    "viewport_width": 1920,
    "viewport_height": 1080
  },
  "smtp": {
    "enabled": false,
    "server": "smtp.example.org",
    "port": 25,
    "sender": "pbirs-mailer@example.org",
    "starttls": false
  },
  "subscriptions": [
    {
      "name": "Example report",
      "enabled": true,
      "url": "http://pbirs.example.org/Reports/powerbi/Folder/Report?rs:embed=true",
      "page": {
        "internal_name": null,
        "display_name": "Overview"
      },
      "recipients": ["recipient@example.org"],
      "subject": "Example report - Overview",
      "filename": "example-overview.png"
    }
  ]
}
```

Une souscription correspond à une page et à une image. Plusieurs pages d'un même
rapport peuvent être traitées en créant plusieurs souscriptions.

## Une installation pensée pour Windows

Le principal objectif de la V1 était de rendre le POC utilisable par une personne qui
clone ou extrait le projet sans connaître le packaging Python.

Depuis PowerShell :

```powershell
.\setup.cmd
.\run.cmd --dry-run
.\run.cmd --no-send
```

Depuis l'invite de commandes Windows :

```cmd
setup.cmd
run.cmd --dry-run
run.cmd --no-send
```

Le programme vérifie Python 3.10 ou une version plus récente, crée un environnement
virtuel local, installe les dépendances, génère la configuration si nécessaire et
contrôle la présence de Microsoft Edge.

Le mode `--dry-run` valide la configuration sans ouvrir le navigateur. Le mode
`--no-send` crée les images sans envoyer d'email. Enfin, `--headed` affiche Edge pour
diagnostiquer la navigation ; sans cette option, la capture reste invisible.

## Les difficultés rencontrées

### 1. Les différentes installations de Python

Sur un poste Windows, `python.exe` et le lanceur `py.exe` peuvent pointer vers des
versions différentes. Le script d'installation teste donc réellement chaque candidat
et sélectionne une version compatible au lieu de supposer que `py -3` convient.

### 2. Les chemins réseau UNC

CMD ne sait pas utiliser directement un chemin UNC comme dossier courant. Les scripts
`.cmd` utilisent `pushd` pour prendre en charge ce cas. Une commande PowerShell directe
vers `setup.ps1` reste également documentée pour le diagnostic.

### 3. L'encodage de `config.json`

Selon l'éditeur Windows, le fichier peut être enregistré en UTF-8, UTF-8 avec BOM ou
Windows-1252. La lecture accepte ces trois formats afin que les caractères accentués ne
bloquent pas le lancement.

### 4. Le profil Edge déjà utilisé

Dans certains environnements, une instance Edge ouverte ou une stratégie d'entreprise
peut provoquer l'erreur `Opening in existing browser session`. La V1 fournit désormais
un message dédié : fermer Edge, vérifier les processus résiduels puis contrôler les
stratégies de navigateur si le problème persiste.

### 5. La navigation entre les pages

La méthode la plus stable consiste à utiliser l'identifiant interne de page lorsqu'il
est connu. À défaut, PBIRS Mailer recherche un onglet, un bouton ou un lien accessible
portant le libellé configuré. Le mode visible reste indispensable pour valider ce point
sur chaque version de Power BI Report Server.

## Fiabiliser avant de planifier

La recette suit une progression volontairement prudente :

- valider la configuration ;
- tester un seul rapport sans email ;
- confirmer la page et la lisibilité de l'image ;
- tester un seul destinataire ;
- ajouter les autres souscriptions ;
- exécuter enfin le programme avec le compte prévu dans le Planificateur de tâches.

Chaque souscription est isolée : l'échec d'un rapport n'empêche pas le traitement des
suivants. Les journaux sont tournants et une capture de diagnostic est créée lorsque la
navigation échoue.

## Sécurité

Un outil de capture peut manipuler des données sensibles. Les règles minimales sont
donc simples :

- ne jamais versionner `config.json` ;
- ignorer les captures et les journaux ;
- utiliser uniquement des exemples synthétiques dans GitHub et dans cet article ;
- limiter les droits du compte d'exécution ;
- commencer avec l'envoi SMTP désactivé ;
- vérifier la liste des destinataires avant chaque test réel.

Le dépôt inclut un `.gitignore`, un guide de sécurité et une checklist de publication.

## Ce que valide la V1

La version 1.0.0 valide le parcours complet : installation Windows, authentification
dans le contexte du compte exécutant le programme, navigation vers une page, capture
silencieuse et envoi SMTP avec l'image intégrée au corps du message.

Le projet reste volontairement limité. Il ne fournit pas encore d'interface graphique,
de gestionnaire de secrets, de moteur de planification intégré ni de découverte
automatique de toutes les pages d'un rapport.

Ces limites laissent plusieurs pistes d'évolution : validation sur davantage de
versions PBIRS, modèles d'emails personnalisables, meilleure observabilité et
packaging Windows autonome.

## Conclusion

PBIRS Mailer est un petit projet, mais il illustre une idée utile : lorsqu'une API ne
couvre pas exactement le rendu attendu, l'automatisation d'un navigateur peut servir de
pont, à condition d'encadrer strictement la configuration, les délais, les erreurs et
la sécurité.

Le code est disponible sous licence MIT : **[LIEN_DU_DEPOT_GITHUB]**.

Les retours sur d'autres versions de Power BI Report Server et sur la robustesse de la
navigation sont les bienvenus.
