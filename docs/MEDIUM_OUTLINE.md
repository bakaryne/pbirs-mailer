# Brouillon d'article Medium

La version rédigée et prête à personnaliser se trouve dans
[`MEDIUM_ARTICLE.md`](MEDIUM_ARTICLE.md). Ce fichier conserve le plan de préparation
initial et les résultats à compléter si des mesures supplémentaires sont réalisées.

## Titre de travail

Automatiser l'envoi de captures Power BI Report Server avec Python et Playwright

## Angle

Power BI Report Server ne propose pas toutes les possibilités d'abonnement du service
cloud. PBIRS Mailer montre comment automatiser, dans un environnement on-premises, la
navigation vers une page de rapport, l'attente du rendu, la capture et l'envoi SMTP.

## Plan

1. Le besoin : diffuser une vue PBIRS sans dépendre du cloud.
2. Pourquoi un navigateur automatisé : reproduire le rendu réellement vu par l'utilisateur.
3. Le POC : Playwright, Edge, attente `querydata`, capture PNG et email CID.
4. Le passage à la V1 : configuration externe, logs, isolation des erreurs et modes de test.
5. Le point difficile : identifier et ouvrir une page de rapport de façon fiable.
6. La recette on-premises : compte technique, NTLM, relais SMTP et tâche planifiée.
7. Sécurité : aucune URL interne, adresse réelle, capture ou donnée métier dans GitHub.
8. Limites et suite : validation multi-versions PBIRS, packaging Windows et observabilité.

## Résultats à compléter après la recette

- Version exacte de Power BI Report Server testée : `[à compléter]`.
- Méthode de navigation retenue : `[internal_name / display_name]`.
- Durée moyenne d'une capture : `[à compléter]`.
- Résultat de l'exécution planifiée : `[à compléter]`.
- Principales erreurs rencontrées et corrections : `[à compléter]`.
