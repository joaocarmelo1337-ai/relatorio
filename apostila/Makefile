# Apostila de armadura de escadas - geracao completa
#
#   make                 gera a apostila do exemplo padrao (.docx e .pdf)
#   make CONFIG=...      gera a apostila de outro exemplo
#   make figuras         so redesenha as figuras
#   make teste           roda a suite de testes
#   make referencia      regenera o estilo do .docx (doc/referencia.docx)
#   make limpar          apaga out/

CONFIG ?= config/exemplo_padrao.yaml
PY     ?= python3

.PHONY: tudo figuras teste referencia limpar deps

tudo:
	$(PY) build.py $(CONFIG)

figuras:
	$(PY) build.py $(CONFIG) --so-figuras

teste:
	$(PY) -m pytest tests/ -q

referencia:
	$(PY) doc/gerar_referencia.py

deps:
	$(PY) -m pip install -r requirements.txt
	@echo "Falta ainda, fora do pip:"
	@echo "  pandoc              (apt install pandoc)          - obrigatorio"
	@echo "  libreoffice-writer  (apt install libreoffice-writer) - para o PDF"

limpar:
	rm -rf out
