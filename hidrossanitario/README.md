# Projeto hidrossanitário automático (protótipo)

`casa.json` (modelo) → `gerar_projeto.py` → `saida/` (DXF, PNG e `trechos.csv`).

    pip install ezdxf matplotlib
    python gerar_projeto.py

Edite `casa.json` (ambientes, portas, peças, tronco de água, coletores) e rode de novo.
`trechos.csv` traz o comprimento de cada trecho: é a entrada do futuro motor de cálculo
(NBR 5626 / 8160 / 17076).
