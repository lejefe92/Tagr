# Tagr

Tagr est une application macOS personnelle pour modifier les metadonnees de fichiers audio.

Elle est actuellement developpee en Python avec PyQt6. Le code principal se trouve dans `src/tagr.py`.

## Lancer l'application

Le plus simple :

```bash
./scripts/run_tagr.sh
```

Le double-clic sur `Tagr.app` utilise aussi cette copie du projet.

## Organisation

- `src/tagr.py` : application principale.
- `scripts/run_tagr.sh` : lance Tagr depuis ce dossier projet.
- `scripts/setup_env.sh` : cree un environnement Python local et installe les dependances.
- `backups/` : copies de securite de la version initiale.
- `docs/DEV_NOTES.md` : contexte technique pour reprendre le projet plus tard.

## Dependances

Dependances Python principales :

- PyQt6
- Mutagen
- Pillow

Dependance systeme utilisee par certaines fonctions audio :

- `ffmpeg`

Sur macOS, si `ffmpeg` manque :

```bash
brew install ffmpeg
```

## Configuration utilisateur

La configuration locale est stockee dans :

```text
~/.tagr_config.json
```

Ce fichier contient notamment les fichiers recents, le dernier dossier ouvert et le theme.
