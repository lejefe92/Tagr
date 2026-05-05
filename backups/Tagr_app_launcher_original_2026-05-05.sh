#!/bin/bash
source "$HOME/tagdrop-env/bin/activate"
exec python3 "$HOME/Downloads/tagr.py" "$@"
