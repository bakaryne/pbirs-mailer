# PBIRS Mailer

PBIRS Mailer automatise la capture d'une page d'un rapport **Power BI Report Server**,
puis l'envoie dans le corps d'un email. Il s'appuie sur Playwright et Microsoft Edge.

La V1 est volontairement simple : les utilisateurs modifient `config.json`, jamais le code.

## Fonctionnalités V1

- plusieurs abonnements dans un seul fichier de configuration ;
- navigation par identifiant interne Power BI ou par libellé visible ;
- attente de stabilisation des requêtes Power BI avant la capture ;
- image PNG intégrée au message avec un lien vers le rapport ;
- traitement indépendant des abonnements : un échec ne bloque pas les suivants ;
- journal tournant dans `logs/` et capture de diagnostic en cas d'erreur ;
- modes validation seule, capture seule et navigateur visible.

## Installation rapide sous Windows

Prérequis : Python 3.10 ou plus récent et Microsoft Edge.

Après avoir cloné ou extrait le projet, ouvrez un terminal dans son dossier.

### Depuis PowerShell

```powershell
.\setup.cmd
```

PowerShell exige le préfixe `.\` pour exécuter un script situé dans le dossier courant.

### Depuis l'invite de commandes Windows (CMD)

```cmd
setup.cmd
```

Dans CMD, le préfixe `.\` n'est pas nécessaire. Il est également possible de
double-cliquer sur `setup.cmd` dans l'Explorateur de fichiers.

Ce script :

- vérifie la version de Python ;
- crée `.venv`, un environnement isolé du Python système ;
- installe PBIRS Mailer et Playwright ;
- crée `config.json` uniquement s'il n'existe pas ;
- détecte Microsoft Edge ;
- valide la configuration.

Il fonctionne également lorsque le projet se trouve sur un partage réseau UNC. Il ne
faut pas activer manuellement l'environnement Python.

Renseignez ensuite le serveur SMTP, l'expéditeur, les rapports, les pages et les
destinataires dans `config.json`. Utilisez `.\configure.cmd` dans PowerShell ou
`configure.cmd` dans CMD pour l'ouvrir directement dans le Bloc-notes. Ce fichier est
ignoré par Git.

## Tests progressifs

Valider la configuration sans ouvrir Edge :

```powershell
.\run.cmd --dry-run
```

Créer les captures sans envoyer de mail :

```powershell
.\run.cmd --no-send
```

Edge reste invisible par défaut grâce à `browser.headless: true`. L'option `--headed`
doit être utilisée uniquement pour diagnostiquer un problème de navigation.

Afficher Edge pour diagnostiquer la navigation d'un seul abonnement :

```powershell
.\run.cmd --no-send --headed --subscription "Example report" --verbose
```

Activer ensuite `smtp.enabled` dans `config.json`, puis lancer :

```powershell
.\run.cmd
```

Le code de sortie vaut `0` si tous les abonnements réussissent, `1` si au moins un
abonnement échoue et `2` si la configuration ou l'environnement est invalide.

Depuis CMD, utilisez les mêmes commandes sans le préfixe `.\`, par exemple :

```cmd
run.cmd --dry-run
run.cmd --no-send
run.cmd
```

## Installation manuelle pour les développeurs

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest
```

L'activation de `.venv` est facultative : les scripts `.\setup.cmd` et `.\run.cmd`
appellent toujours le bon interpréteur explicitement.

### Projet placé sur un partage réseau UNC

`CMD.EXE` peut afficher un avertissement avec un chemin commençant par `\\serveur`.
Pour une installation sans cet avertissement, lancez directement :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

## Choisir la page du rapport

La méthode prioritaire à tester est `page.internal_name`, par exemple
`ReportSection42`. Elle ajoute `pageName` à l'URL et évite de dépendre du texte
affiché. Son comportement doit être validé sur la version de PBIRS utilisée : le
paramètre est documenté pour les rapports Power BI intégrés, mais la documentation
PBIRS ne garantit explicitement que `rs:embed=true`.

Si cet identifiant n'est pas connu ou n'est pas pris en charge, laissez
`internal_name` à `null` et renseignez
`page.display_name`. PBIRS Mailer cherchera alors un onglet, un bouton ou un lien
accessible portant ce libellé. En cas d'échec, lancez le test avec `--headed --verbose` ;
une image `*-error.png` sera aussi créée dans `captures/`.

Une souscription correspond à une page et produit une image. Pour capturer plusieurs
pages d'un même rapport, dupliquez la souscription avec un nom, une page et un nom de
fichier PNG uniques.

## Exécution planifiée

Pour une première mise en production, utilisez le Planificateur de tâches Windows avec
le même compte technique que celui qui peut ouvrir les rapports PBIRS et joindre le
relais SMTP. Définissez le dossier du projet comme répertoire de démarrage.

## Sécurité et publication

- ne publiez jamais `config.json`, les captures, les journaux ni les données métier ;
- utilisez des exemples synthétiques dans les copies d'écran et la documentation ;
- vérifiez les droits du compte d'exécution sur chaque rapport PBIRS ;
- commencez avec `smtp.enabled: false` et un seul abonnement de test.

## Développement

```powershell
pytest
ruff check .
```

Licence : MIT.

## Documentation

- [Guide de dépannage](docs/TROUBLESHOOTING.md)
- [Checklist de validation](docs/ACCEPTANCE_TEST_CHECKLIST.md)
- [Historique des versions](CHANGELOG.md)
- [Politique de sécurité](SECURITY.md)
- [Contribuer au projet](CONTRIBUTING.md)

## État du projet

La version `1.0.0` a validé le parcours complet : installation, navigation vers une
page, capture silencieuse et envoi SMTP. Consultez le changelog pour les limites et
évolutions prévues.
