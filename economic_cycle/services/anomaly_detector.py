import numpy as np


def detect_anomalies(series):

    mean = series.mean()
    std = series.std()

    # Evitar división por cero o desviación estándar inválida
    if std == 0 or np.isnan(std):
        return []

    anomalies = []

    for idx, value in enumerate(series):

        z = abs((value - mean) / std)

        if z > 2:
            anomalies.append(idx)

    return anomalies