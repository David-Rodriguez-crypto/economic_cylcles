from io import BytesIO

import plotly.graph_objects as go

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)


def create_pdf(results):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        spaceAfter=20
    )

    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=styles["Heading2"],
        fontSize=15,
        spaceBefore=12,
        spaceAfter=8
    )

    normal = styles["BodyText"]

    elementos = []

    # ==========================================
    # TÍTULO
    # ==========================================

    elementos.append(
        Paragraph(
            "📊 REPORTE DEL ANÁLISIS ECONÓMICO",
            titulo
        )
    )

    elementos.append(
        Paragraph(
            "Sistema de Análisis de Tendencias y Ciclos Económicos",
            normal
        )
    )

    elementos.append(Spacer(1, 15))

    # ==========================================
    # INDICADORES
    # ==========================================

    elementos.append(
        Paragraph("Resumen ejecutivo", subtitulo)
    )

    resumen = [
        ["Indicador", "Resultado"],
        [
            "Crecimiento promedio",
            f"{results.get('avg_growth', 0):.2f} %"
        ],
        [
            "Fase actual",
            results.get("current_phase", "Sin datos")
        ],
        [
            "Número de alertas",
            str(results.get("num_alerts", 0))
        ],
        [
            "Años atípicos",
            str(results.get("num_anomalies", 0))
        ],
        [
            "Cambios estructurales",
            str(len(results.get("breaks", [])))
        ]
    ]

    tabla_resumen = Table(
        resumen,
        colWidths=[9 * cm, 7 * cm]
    )

    tabla_resumen.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d3557")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("PADDING", (0, 0), (-1, -1), 7)
        ])
    )

    elementos.append(tabla_resumen)

    # ==========================================
    # ALERTAS
    # ==========================================

    elementos.append(
        Paragraph("🚨 Alertas detectadas", subtitulo)
    )

    alerts = results.get("alerts", [])

    if alerts:

        for alert in alerts:

            elementos.append(
                Paragraph(
                    f"• {alert}",
                    normal
                )
            )

    else:

        elementos.append(
            Paragraph(
                "No se detectaron alertas económicas.",
                normal
            )
        )

    # ==========================================
    # CAMBIOS ESTRUCTURALES
    # ==========================================

    elementos.append(
        Paragraph("📉 Cambios estructurales", subtitulo)
    )

    breaks = results.get("breaks", [])

    if breaks:

        datos_breaks = [
            ["Año", "Valor"]
        ]

        for b in breaks:

            datos_breaks.append([
                str(b["year"]),
                f"{b['value']:,.0f}"
            ])

        tabla_breaks = Table(
            datos_breaks,
            colWidths=[5 * cm, 8 * cm]
        )

        tabla_breaks.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ffc107")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 6)
            ])
        )

        elementos.append(tabla_breaks)

    else:

        elementos.append(
            Paragraph(
                "No se detectaron cambios estructurales.",
                normal
            )
        )

    # ==========================================
    # ANOMALÍAS
    # ==========================================

    elementos.append(
        Paragraph("⚠️ Años atípicos", subtitulo)
    )

    anomalies = results.get("anomalies", [])

    if anomalies:

        datos_anomalias = [
            ["Año", "Crecimiento"]
        ]

        for a in anomalies:

            datos_anomalias.append([
                str(a["year"]),
                f"{a['growth']:.2f} %"
            ])

        tabla_anomalias = Table(
            datos_anomalias,
            colWidths=[5 * cm, 8 * cm]
        )

        tabla_anomalias.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ffc107")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 6)
            ])
        )

        elementos.append(tabla_anomalias)

    else:

        elementos.append(
            Paragraph(
                "No se detectaron anomalías.",
                normal
            )
        )

    # ==========================================
    # GRÁFICO
    # ==========================================

    elementos.append(
        Paragraph("📈 Evolución económica", subtitulo)
    )

    table_data = results.get("table_data", [])

    if table_data:

        fig = go.Figure()

        colores = {
            "Expansión": "green",
            "Recesión": "red",
            "Recuperación": "orange",
            "Estancamiento": "gray"
        }

        for i in range(len(table_data) - 1):

            fase = table_data[i + 1]["cycle"]

            fig.add_trace(
                go.Scatter(
                    x=[
                        table_data[i]["year"],
                        table_data[i + 1]["year"]
                    ],
                    y=[
                        table_data[i]["value"],
                        table_data[i + 1]["value"]
                    ],
                    mode="lines+markers",
                    line=dict(
                        color=colores.get(fase, "blue"),
                        width=4
                    ),
                    marker=dict(size=7),
                    showlegend=False
                )
            )

        fig.update_layout(
            title="Evolución de la serie económica",
            xaxis_title="Año",
            yaxis_title="Valor",
            template="plotly_white",
            height=450
        )

        imagen = fig.to_image(
            format="png",
            width=900,
            height=450
        )

        image_buffer = BytesIO(imagen)

        elementos.append(
            Image(
                image_buffer,
                width=17 * cm,
                height=8.5 * cm
            )
        )

    # ==========================================
    # TABLA DE RESULTADOS
    # ==========================================

    elementos.append(
        Paragraph("📋 Resultados completos", subtitulo)
    )

    datos = [
        [
            "Año",
            "Valor",
            "Crecimiento",
            "Fase"
        ]
    ]

    for row in table_data:

        datos.append([
            str(row["year"]),
            f"{row['value']:,.0f}",
            f"{row['growth']:.2f} %",
            row["cycle"]
        ])

    tabla = Table(
        datos,
        repeatRows=1,
        colWidths=[
            3 * cm,
            4 * cm,
            4 * cm,
            5 * cm
        ]
    )

    tabla.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d3557")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 5)
        ])
    )

    elementos.append(tabla)

    # ==========================================
    # PIE
    # ==========================================

    elementos.append(Spacer(1, 20))

    elementos.append(
        Paragraph(
            "Generado por el Sistema de Análisis Económico",
            normal
        )
    )

    doc.build(elementos)

    buffer.seek(0)

    return buffer