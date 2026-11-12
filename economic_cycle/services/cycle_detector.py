
def detect_cycles(growth):

    phases = []
    previous_phase = None

    for g in growth:

        # Manejar datos faltantes
        if g is None:
            phases.append("Sin datos")
            continue

        # Recesión
        if g < -2:
            phase = "Recesión"

        # Recuperación después de una recesión
        elif previous_phase in ["Recesión", "Recuperación"] and g > 0 and g <= 3:
            phase = "Recuperación"

        # Expansión
        elif g > 3:
            phase = "Expansión"

        # Crecimiento positivo moderado
        elif g > 0:
            phase = "Expansión"

        # Estancamiento
        else:
            phase = "Estancamiento"

        phases.append(phase)
        previous_phase = phase

    return phases
