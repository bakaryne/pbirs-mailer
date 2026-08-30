# PBIRS Mailer Configurator

Le Configurator est une interface Windows locale qui modifie le même `config.json`
que la ligne de commande PBIRS Mailer. Il ne modifie pas le moteur de capture 1.0.1.

## Démarrage

Installez d'abord le projet, puis ouvrez l'interface :

```powershell
.\setup.cmd
.\configure.cmd
```

Le script crée `config.json` à partir de l'exemple uniquement si le fichier n'existe
pas encore.

## Onglets

### Navigateur et dossiers

Configure Microsoft Edge, la taille de la capture, les délais de rendu et les dossiers
de captures et de journaux.

### Serveur SMTP

Configure le relais, le port, l'expéditeur et STARTTLS. Aucun mot de passe n'est stocké
par le Configurator.

### Souscriptions

Permet d'ajouter, modifier, dupliquer, activer, désactiver ou supprimer une
souscription. Chaque modification apportée dans cet onglet est immédiatement validée
et enregistrée dans `config.json`. Chaque souscription conserve le format V1 : une
page, une capture PNG et un email.

Lorsqu'une seule souscription existe, elle est automatiquement sélectionnée. La
configuration doit toujours en contenir au moins une : pour retirer la dernière du
traitement, désactivez-la au lieu de la supprimer.

## Validation et sauvegarde

Le bouton **Vérifier la configuration** contrôle les valeurs en mémoire sans modifier
le fichier.

Le bouton **Enregistrer** :

1. construit le document JSON ;
2. le valide avec le moteur 1.0.1 ;
3. sauvegarde l'ancien fichier sous `config.backup-*.json` ;
4. remplace `config.json` de manière atomique.

Le fichier actif reste toujours `config.json`. Les fichiers
`config.backup-*.json` sont uniquement des copies de l'ancienne configuration.

Une configuration invalide ne remplace jamais le fichier existant.

Lorsque des paramètres du navigateur ou du serveur SMTP sont modifiés, l'interface
affiche **Modifications non enregistrées**. À la fermeture, elle propose de les
enregistrer, de les abandonner ou d'annuler la fermeture.

Une sauvegarde est créée uniquement lorsque le contenu de `config.json` change.

## Capture sans email

Le bouton **Capturer sans envoyer** enregistre d'abord la configuration, puis exécute
PBIRS Mailer avec `--no-send --verbose`. Le résultat et le chemin exact du fichier de
configuration utilisé sont affichés dans une fenêtre de diagnostic. Un bouton permet
de copier ce diagnostic dans le presse-papiers.

## Planification

Le Planificateur de tâches Windows ou SQL Server Agent continue d'appeler :

```powershell
.\run.cmd
```

Il ne faut pas lancer `configure.cmd` depuis une tâche planifiée.

## Revenir à une ancienne configuration

Fermez le Configurator, renommez la copie souhaitée en `config.json`, puis validez-la :

```powershell
.\run.cmd --dry-run
```

Les fichiers de sauvegarde contiennent les mêmes informations que la configuration
active et doivent rester confidentiels.
