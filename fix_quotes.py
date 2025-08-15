#!/usr/bin/env python3
# Script pour corriger les guillemets échappés dans assistant_ia_simple.py

import re

# Lire le fichier
with open('assistant_ia_simple.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacer les guillemets échappés par des guillemets normaux
content = content.replace('\\"', '"')
content = content.replace('\\n', '\n')
content = content.replace('\\t', '\t')

# Corrections spécifiques pour les f-strings problématiques dans les return statements
patterns = [
    (r'f\\"([^"]+)\\"', r'f"\1"'),
    (r'\\\"([^"]+)\\\"', r'"\1"'),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

# Sauvegarder le fichier corrigé
with open('assistant_ia_simple.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Corrections appliquées à assistant_ia_simple.py")