#!/usr/bin/env bash
# Installa le skill del tutor scolastico per Claude Code.
# Crea ~/Scuola con il venv Python e collega le skill in ~/.claude/skills.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
SCUOLA="$HOME/Scuola"
SKILLS="$HOME/.claude/skills"

mkdir -p "$SCUOLA" "$SKILLS"

if [ ! -d "$SCUOLA/venv" ]; then
    echo "Creo il venv in $SCUOLA/venv"
    python3 -m venv "$SCUOLA/venv"
fi
"$SCUOLA/venv/bin/pip" install -q -r "$REPO/requirements.txt"

for skill in "$REPO"/skills/*/; do
    nome="$(basename "$skill")"
    dest="$SKILLS/$nome"
    if [ -L "$dest" ]; then
        rm "$dest"
    elif [ -e "$dest" ]; then
        echo "Sposto la vecchia $dest in $dest.bak"
        mv "$dest" "$dest.bak"
    fi
    ln -s "${skill%/}" "$dest"
    echo "Skill $nome collegata in $dest"
done

if [ ! -f "$SCUOLA/.env" ]; then
    cp "$REPO/esempi/env.example" "$SCUOLA/.env"
    chmod 600 "$SCUOLA/.env"
    echo "Scrivi utente e password di Classeviva in $SCUOLA/.env"
fi
if [ ! -f "$SCUOLA/orario.md" ]; then
    cp "$REPO/esempi/orario.md" "$SCUOLA/orario.md"
    echo "Adatta $SCUOLA/orario.md al tuo orario"
fi

echo "Fatto. Apri Claude Code e scrivi /registro-giornaliero o /materiale-lezioni."
