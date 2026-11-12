
import ruptures as rpt
import numpy as np


def detect_breaks(series, pen=5):

    # Eliminar valores nulos
    clean_series = series.dropna()

    # Evitar analizar series demasiado pequeñas
    if len(clean_series) < 5:
        return []

    # Convertir a un arreglo numérico
    values = clean_series.to_numpy(dtype=float)

    # Comprobar que los valores sean válidos
    if not np.isfinite(values).all():
        return []

    # Detectar cambios estructurales
    algo = rpt.Pelt(
        model="rbf",
        min_size=2,
        jump=1
    ).fit(values)

    breakpoints = algo.predict(pen=pen)

    # Excluir el último punto (final de la serie)
    breakpoints = [
        idx for idx in breakpoints
        if idx < len(values)
    ]

    return breakpoints
