"""Identidade e constantes da plataforma."""

from pathlib import Path

TITULO = "JOÃO CARMELO — TCC"
SUBTITULO = "Vistoria, Garantias e Manutenção Residencial"
LEMA = "Vistoriar antes para não descobrir depois."

ACADEMICO = "João Carmelo"
CURSO = "Engenharia Civil"
INSTITUICAO = "UFMS — Universidade Federal de Mato Grosso do Sul"
ORIENTADOR = "Sidiclei Formangini"
ANO = 2026

RAIZ = Path(__file__).resolve().parent
UPLOADS = RAIZ / "uploads"
FOTOS = UPLOADS / "fotos"
DOCUMENTOS = UPLOADS / "documentos"

# A paleta e os componentes de tela ficam em tcc/estilo.py.
LEMA_RODAPE = ("Planejamento", "Qualidade", "Segurança", "Durabilidade")

# (ícone do Bootstrap Icons, nome da página). Os nomes vêm de
# https://icons.getbootstrap.com -- o componente do menu os resolve.
MENU = [
    ("house-door", "Início"),
    ("buildings", "Residências"),
    ("clipboard-check", "Vistorias"),
    ("door-open", "Ambientes"),
    ("exclamation-triangle", "Patologias"),
    ("camera", "Catálogo Fotográfico"),
    ("bar-chart", "Classificação GUT"),
    ("shield-check", "Garantias"),
    ("clock-history", "Relógio de Garantias"),
    ("tools", "Manutenção"),
    ("calendar3", "Gantt 10 anos"),
    ("file-earmark-text", "Protocolos"),
    ("folder2-open", "Documentos"),
    ("graph-up", "Dados do TCC"),
    ("journal-text", "Relatórios"),
    ("database", "Excel / Banco de Dados"),
    ("gear", "Configurações"),
]

AVISO_RESPONSABILIDADE = (
    "Situação técnica indicativa de garantia. Confira sempre o Termo de "
    "Garantia, o Manual da Edificação, o histórico de manutenção, eventuais "
    "reformas, o contrato e a legislação aplicável. Nenhuma classificação "
    "automática substitui a avaliação técnica profissional."
)
