# Migrer de PBIRS Mailer 1.0.1 vers 1.1.0

La version 1.1.0 conserve le moteur de capture et le format de configuration de la
version 1.0.1. La migration ne nécessite donc aucune conversion du JSON.

## Procédure recommandée

1. Conservez le dossier 1.0.1 comme solution de retour arrière.
2. Extrayez la version 1.1.0 dans un nouveau dossier.
3. Copiez uniquement le fichier `config.json` de l'ancien dossier vers le nouveau.
4. Ne copiez pas `.venv`, les captures, les journaux ou les fichiers de backup.
5. Exécutez `setup.cmd` dans le nouveau dossier.
6. Ouvrez `configure.cmd` et vérifiez les paramètres et les souscriptions.
7. Lancez une capture sans envoi depuis l'interface.
8. Validez enfin la ligne de commande avec :

```powershell
.\run.cmd --dry-run
.\run.cmd --no-send --verbose
```

La tâche planifiée ou le job SQL Server Agent continue d'appeler `run.cmd`. Après la
recette, mettez à jour son dossier de démarrage afin qu'il pointe vers la nouvelle
installation.

## Retour arrière

En cas de problème, arrêtez la nouvelle planification et remettez l'ancien dossier
1.0.1 comme dossier de démarrage. Aucun fichier de la version 1.0.1 n'est écrasé par
la procédure recommandée.
