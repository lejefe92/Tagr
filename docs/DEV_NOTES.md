# Notes de reprise - Tagr

## Etat au 2026-05-05

Tagr etait lance depuis `/Users/basile/Desktop/Tagr.app`, mais ce bundle macOS ne contenait pas directement l'application compilee. Son executable etait un script shell qui lancait :

```bash
$HOME/Downloads/tagr.py
```

Le projet a ete range dans :

```text
/Users/basile/Documents/Tagr
```

Le code principal est maintenant :

```text
/Users/basile/Documents/Tagr/src/tagr.py
```

Le lanceur macOS `Tagr.app` a ete mis a jour pour lancer cette nouvelle source.

## Technologie

- Python
- PyQt6 pour l'interface
- Mutagen pour les tags audio
- Pillow pour les pochettes
- ffmpeg/afplay pour certaines fonctions audio macOS
- configuration locale dans `~/.tagr_config.json`

## Structure actuelle du code

Le code est encore dans un gros fichier unique d'environ 2700 lignes. C'est acceptable pour continuer a ameliorer l'app perso, mais les prochaines grosses evolutions devraient progressivement isoler :

- lecture/ecriture des tags
- recherche de pochettes et metadonnees
- fonctions audio/ffmpeg
- composants d'interface
- configuration et etat utilisateur

## Priorites conseillees

1. Verifier les workflows existants dans l'app et noter les irritants.
2. Corriger les bugs visibles avant de refactorer.
3. Ajouter quelques garde-fous : sauvegarde avant modification audio, messages d'erreur plus clairs, validation des champs.
4. Decouper le fichier seulement quand une zone doit etre modifiee en profondeur.
5. Garder `src/tagr.py` comme point d'entree tant que le decoupage n'est pas necessaire.

## Lancement

Depuis le dossier projet :

```bash
./scripts/run_tagr.sh
```

Pour creer un environnement Python local :

```bash
./scripts/setup_env.sh
```
