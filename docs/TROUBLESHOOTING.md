# Dépannage

## `No module named 'pbirs_mailer'`

Utilisez `.\setup.cmd`, puis `.\run.cmd`. Ne lancez pas le Python global directement.
La version 0.2.3 sait aussi charger le dossier `src` lors d'un lancement direct.

## Erreur `utf-8 codec can't decode byte`

À partir de la version 0.2.3, `config.json` peut être enregistré en UTF-8, UTF-8
avec BOM ou Windows-1252/ANSI. Les caractères accentués sont pris en charge.

## Version de Python incompatible

PBIRS Mailer nécessite Python 3.10 ou plus récent. `setup.cmd` affiche la version
détectée avant toute installation. Si plusieurs versions sont installées, le script
cherche automatiquement une version compatible au lieu d'utiliser aveuglément `py -3`.

## `Ignoring invalid distribution -ip`

Cet avertissement provient d'une installation globale de `pip` endommagée. Le dossier
`.venv` créé par `setup.cmd` isole PBIRS Mailer de cette installation.

## Microsoft Edge ne démarre pas

Vérifiez que Microsoft Edge est installé dans son emplacement Windows standard. Le
fichier `config.json` doit contenir `"channel": "msedge"`.

Si le journal indique `Opening in existing browser session` ou `profile is already in
use`, fermez toutes les fenêtres Edge. Vérifiez ensuite qu'aucun processus ne reste :

```powershell
Get-Process msedge -ErrorAction SilentlyContinue
```

Après avoir enregistré les onglets ouverts, les éventuels processus résiduels peuvent
être arrêtés avec `Stop-Process -Name msedge -Force`. Si l'erreur persiste sans aucun
processus Edge, vérifiez avec l'équipe système si une stratégie Edge impose un profil
utilisateur fixe.

## Edge s'affiche pendant la capture

Vérifiez que `browser.headless` vaut `true` dans `config.json` et retirez l'option
`--headed` de la commande. Cette option affiche volontairement Edge pour le diagnostic.

## Réinstallation propre

Le dossier `.venv` ne contient aucune configuration métier. Il peut être supprimé,
puis recréé en relançant `.\setup.cmd`. Ne supprimez pas `config.json`.

## La page du rapport est introuvable

Relancez avec :

```powershell
.\run.cmd --no-send --headed --verbose
```

Consultez ensuite `logs/pbirs-mailer.log` et la capture `*-error.png` dans
`captures/`. Si possible, renseignez `page.internal_name` dans `config.json`.

## Les visuels SSAS ne sont pas entièrement chargés

À partir de la version 1.0.1, la capture attend la fin des requêtes `querydata`, la
disparition des indicateurs de chargement et la stabilité du rendu. Pour un rapport
particulièrement lent, augmentez progressivement dans `config.json` :

```json
"render_timeout_seconds": 180,
"render_quiet_seconds": 5,
"render_stable_seconds": 3
```

Relancez d'abord avec `--no-send --headed --verbose`. Un dépassement du délai provoque
un échec et une capture `*-error.png` ; aucun email incomplet n'est envoyé.
