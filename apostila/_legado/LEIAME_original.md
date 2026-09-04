# Fontes da apostila de escadas

- scripts/build.js      -> monta o .docx (Node + docx-js). Le fig/*.png e scripts/sizes.json
- scripts/figs.py       -> gera as figuras simples (dominios, formatos de barra, vistas em planta)
- scripts/detalhe.py    -> gera o corte geral da escada com geometria real
- scripts/detalhe2.py   -> gera o corte da N2 dividida e o canto reentrante
- scripts/sizes.json    -> dimensoes em px de cada PNG (gerado com PIL)
- fig/                  -> figuras em PNG (usadas no docx) e SVG (fonte editavel)

## Como reconstruir
```
pip install cairosvg pillow --break-system-packages
python3 scripts/figs.py && python3 scripts/detalhe.py && python3 scripts/detalhe2.py
python3 -c "from PIL import Image; import json,glob; json.dump({f:list(Image.open(f).size) for f in glob.glob('fig/*.png')}, open('scripts/sizes.json','w'))"
node scripts/build.js
```

## Geometria do exemplo (cm)
piso s=28 | espelho e=18,5 | 8 degraus | patamares 120 | h=12 | cobrimento 2,5
C25 | CA-50 | As=10,22 cm2/m | Ø10 c/7,5 | lb,nec 25,7 (gancho) e 36,8 (reta)
