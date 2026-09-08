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

MENU = [
    ("🏠", "Início"),
    ("🏘", "Residências"),
    ("🔎", "Vistorias"),
    ("🚪", "Ambientes"),
    ("⚠", "Patologias"),
    ("📷", "Catálogo Fotográfico"),
    ("📊", "Classificação GUT"),
    ("🛡", "Garantias"),
    ("⏱", "Relógio de Garantias"),
    ("🛠", "Manutenção"),
    ("📅", "Gantt 10 anos"),
    ("📑", "Protocolos"),
    ("📂", "Documentos"),
    ("📈", "Dados do TCC"),
    ("📄", "Relatórios"),
    ("📊", "Excel / Banco de Dados"),
    ("⚙", "Configurações"),
]

AVISO_RESPONSABILIDADE = (
    "Situação técnica indicativa de garantia. Confira sempre o Termo de "
    "Garantia, o Manual da Edificação, o histórico de manutenção, eventuais "
    "reformas, o contrato e a legislação aplicável. Nenhuma classificação "
    "automática substitui a avaliação técnica profissional."
)
