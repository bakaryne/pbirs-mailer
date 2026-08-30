# PBIRS Mailer 1.1.0

PBIRS Mailer 1.1.0 ajoute un Configurator Windows local à la version 1.0.1. Le moteur
de navigation, d'attente du rendu, de capture et d'envoi reste inchangé.

## Nouveautés

- interface locale pour le navigateur, le relais SMTP et les souscriptions ;
- ajout, modification, duplication, activation et suppression des souscriptions ;
- URL du rapport visible dans le tableau ;
- validation avec les mêmes règles que la ligne de commande ;
- sauvegarde atomique de `config.json` avec copie de sécurité de l'ancienne version ;
- détection des modifications non enregistrées ;
- capture sans envoi et diagnostic copiable depuis l'interface.

## Compatibilité

- Windows avec Microsoft Edge ;
- Python 3.10 ou plus récent ;
- format `config.json` version 1, identique à PBIRS Mailer 1.0.1 ;
- Planificateur de tâches Windows et SQL Server Agent inchangés : ils continuent
  d'exécuter `run.cmd`.

## Sécurité

Le Configurator fonctionne localement, ne lance aucun serveur web, n'ajoute aucune
télémétrie et ne stocke aucun mot de passe. Les fichiers `config.json` et
`config.backup-*.json` doivent rester protégés et exclus du dépôt Git.

## Mise à niveau

Installez cette version dans un nouveau dossier et copiez uniquement le
`config.json` de la version 1.0.1. Consultez le guide de migration avant de modifier
une tâche planifiée existante.
