"""Motor de cálculo da apostila de escadas.

Fluxo: config/*.yaml -> engine.api.calcular() -> dict de resultados, consumido
tanto pelos desenhos (desenho/) quanto pelo texto (doc/).
"""
from .api import calcular  # noqa: F401
