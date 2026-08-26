# Recette de la V1

## Avant le test

- [ ] Exécuter `.\setup.cmd` depuis le dossier du projet.
- [ ] Ouvrir `config.json` avec `.\configure.cmd`.
- [ ] Renseigner un seul rapport non sensible et un seul destinataire de test.
- [ ] Garder `smtp.enabled` à `false`.
- [ ] Exécuter `.\run.cmd --dry-run`.

## Capture

- [ ] Exécuter `.\run.cmd --no-send --headed --verbose` avec le compte cible.
- [ ] Vérifier l'accès PBIRS et l'authentification Windows.
- [ ] Vérifier que la bonne page est affichée.
- [ ] Tester un rapport SSAS lent et vérifier que tous les visuels sont terminés.
- [ ] Vérifier dans le journal la fin des `querydata`, l'absence de spinner et la
      stabilité du DOM.
- [ ] Vérifier la lisibilité de l'image dans `captures/`.
- [ ] Retirer `--headed` et confirmer que la capture fonctionne sans afficher Edge.
- [ ] En cas d'échec par libellé, renseigner `page.internal_name` si disponible.

## Email

- [ ] Conserver un seul destinataire de test.
- [ ] Activer `smtp.enabled`.
- [ ] Exécuter `.\run.cmd --subscription "Nom du test"`.
- [ ] Vérifier l'expéditeur, l'objet, l'image intégrée et le lien PBIRS.
- [ ] Vérifier le code de sortie et `logs/pbirs-mailer.log`.

## Validation finale

- [ ] Tester deux abonnements successifs.
- [ ] Provoquer un échec et confirmer que le second abonnement continue.
- [ ] Tester l'exécution non interactive avec le compte prévu.
- [ ] Valider l'exécution depuis le Planificateur de tâches Windows.
- [ ] Vérifier que le dépôt ne contient aucune URL, adresse, capture ou donnée réelle.
