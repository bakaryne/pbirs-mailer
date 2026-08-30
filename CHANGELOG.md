# Changelog

## 1.1.0 - 2026-08-29

- Ajoute une interface Windows locale pour modifier `config.json` sans toucher au
  code.
- Gère les paramètres du navigateur, le relais SMTP et les souscriptions.
- Réutilise strictement la validation de configuration du moteur 1.0.1.
- Enregistre le JSON de manière atomique et sauvegarde la version précédente.
- Permet de lancer une capture sans email depuis l'interface.
- Enregistre immédiatement les ajouts et modifications de souscriptions afin
  d'éviter toute confusion entre vérification et sauvegarde.
- Affiche le chemin exact du `config.json` utilisé dans la fenêtre de diagnostic.
- Sélectionne automatiquement l'unique souscription afin que les boutons d'action
  fonctionnent immédiatement.
- Affiche clairement qu'une dernière souscription ne peut pas être supprimée, mais
  peut être désactivée.
- Force `configure.cmd` à charger le code de l'archive courante, même si un ancien
  Configurator était déjà installé dans `.venv`.
- Enregistre désormais la souscription directement depuis le bouton de la fenêtre de
  modification, avant de fermer celle-ci.
- Affiche l'URL du rapport dans le tableau pour rendre toute modification visible.
- Signale les modifications non enregistrées et propose de les sauvegarder à la
  fermeture.
- Évite de créer un fichier de sauvegarde lorsque la configuration n'a pas changé.
- Bloque les actions de configuration pendant une capture et permet de copier le
  diagnostic dans le presse-papiers.
- Conserve le moteur de navigation et de capture de la version 1.0.1 sans modification.

## 1.0.1 - 2026-08-26

- Attend la fin effective de toutes les requêtes `querydata`, y compris avec une
  connexion SSAS lente.
- Vérifie qu'aucun indicateur de chargement Power BI n'est encore visible.
- Exige un DOM de visuels stable pendant une durée configurable avant la capture.
- Porte les valeurs par défaut à 120 secondes de délai maximal, 5 secondes de calme
  réseau et 3 secondes de stabilité visuelle.
- Interrompt l'abonnement et crée une capture de diagnostic lorsque le rendu ne se
  stabilise pas, au lieu d'envoyer une image incomplète.

## 1.0.0 - 2026-08-22

- Valide le parcours complet sur une instance Power BI Report Server : installation,
  navigation, capture silencieuse et envoi SMTP.
- Clarifie le mode headless et l'utilisation diagnostique de `--headed`.
- Documente séparément l'installation depuis PowerShell et depuis CMD.
- Ajoute un diagnostic explicite lorsque le profil Microsoft Edge est déjà utilisé.
- Généralise la documentation et les listes de recette pour une publication publique.
- Ajoute un article Medium complet et un kit de communication GitHub/LinkedIn.
- Nettoie tous les exemples et fichiers distribués de leurs informations internes.

## 0.2.3 - 2026-08-22

- Accepte `config.json` en UTF-8, UTF-8 avec BOM et Windows-1252/ANSI.
- Ajoute des tests couvrant les caractères accentués issus des éditeurs Windows.

## 0.2.2 - 2026-08-22

- Teste `python.exe` avant le lanceur Windows `py.exe`.
- Neutralise les erreurs natives émises par un lanceur Python inutilisable sous
  Windows PowerShell 5.
- Supprime les sondes successives de versions Python absentes.

## 0.2.1 - 2026-08-22

- Sélectionne automatiquement un interpréteur compatible lorsque `py -3` pointe
  vers une ancienne version mais que `python.exe` est plus récent.
- Recrée un éventuel `.venv` incompatible sans toucher à `config.json`.
- Corrige les commandes PowerShell avec le préfixe `.\`.
- Documente le lancement direct de `setup.ps1` depuis un partage UNC.

## 0.2.0 - 2026-08-22

- Installation Windows guidée par `setup.cmd`, y compris depuis un partage réseau UNC.
- Environnement virtuel local isolé du Python système.
- Lancement simplifié par `run.cmd` sans activation manuelle de l'environnement.
- Création non destructive de `config.json` à partir de l'exemple.
- Prise en charge officielle de Python 3.10.
- Message explicite si Python, Playwright ou Microsoft Edge ne peut pas démarrer.
- Test GitHub Actions du parcours d'installation Windows.

## 0.1.1 - 2026-08-22

- Permet l'exécution directe de `python main.py` depuis l'archive extraite,
  sans installation préalable du paquet `pbirs_mailer`.

## 0.1.0 - 2026-08-22

- Externalisation des paramètres dans `config.json`.
- Capture de plusieurs abonnements PBIRS avec Playwright et Edge.
- Navigation par identifiant interne ou libellé visible.
- Attente de stabilisation des requêtes `querydata` avant capture.
- Envoi SMTP avec image intégrée au corps du message.
- Modes `--dry-run`, `--no-send`, `--headed` et sélection d'un abonnement.
- Journaux tournants, captures de diagnostic et codes de sortie exploitables.
- Tests unitaires et workflow GitHub Actions.
