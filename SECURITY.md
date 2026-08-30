# Sécurité

PBIRS Mailer est conçu pour fonctionner dans un environnement interne. Ne joignez
jamais de configuration réelle, de capture, de journal ou de donnée métier à une issue
publique.

Pour signaler une vulnérabilité, utilisez un canal privé auprès du mainteneur du dépôt
plutôt qu'une issue GitHub publique. Décrivez le problème avec des données synthétiques.

Avant toute mise en production, appliquez le principe du moindre privilège au compte
d'exécution et vérifiez séparément ses droits PBIRS et SMTP.

Le Configurator crée une copie de sécurité avant de remplacer `config.json`. Ces
fichiers `config.backup-*.json` contiennent les mêmes paramètres que le fichier actif :
protégez-les avec les mêmes droits Windows et ne les publiez jamais.

PBIRS Mailer ne stocke aucun mot de passe Windows ou SMTP. Si une authentification
SMTP est ajoutée dans une version ultérieure, les secrets ne devront pas être écrits
dans le document JSON.
