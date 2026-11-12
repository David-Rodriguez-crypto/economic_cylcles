from .cycle_detector import detect_cycles
from .anomaly_detector import detect_anomalies
from .structural_breaks import detect_breaks

import plotly.graph_objects as go
import pandas as pd



    
class EconomicAnalyzer:

    def __init__(self, df):
        self.df = df.copy()

        # Convertir el año a número
        self.df["year"] = pd.to_numeric(
            self.df["year"],
            errors="coerce"
        )

        # Convertir valores económicos, incluyendo coma decimal
        def convertir_valor(valor):
            if pd.isna(valor):
                return float("nan")

            if isinstance(valor, str):
                valor = valor.strip()
                valor = valor.replace(",", ".")

            return pd.to_numeric(valor, errors="coerce")

        self.df["value"] = self.df["value"].apply(convertir_valor)

        # Eliminar únicamente filas con año o valor inválido
        self.df = self.df.dropna(subset=["year", "value"])

        # Mostrar resultados de la comprobación
        print("\n===== REVISIÓN DE DATOS =====")
        print("Filas originales:", len(df))
        print("Filas válidas:", len(self.df))
        print("Años procesados:", self.df["year"].tolist())
        print("==============================\n")


    def run_analysis(self):

        # Ordenar por año
        self.df = self.df.sort_values("year")
        self.df = self.df.reset_index(drop=True)
        print("DEBUG 2 - Filas al iniciar análisis:", len(self.df))

        # Crecimiento porcentual
        growth = self.df["value"].pct_change() * 100
        growth = growth.fillna(0)

        # Detectar fases
        cycles = detect_cycles(growth)
        print("DEBUG 3 - Filas después de detectar ciclos:", len(self.df))

        # Detectar anomalías
        anomalies_idx = detect_anomalies(growth)

        anomalies = []

        for idx in anomalies_idx:
            if idx < len(self.df):
                anomalies.append({
                    "year": int(self.df.iloc[idx]["year"]),
                    "growth": round(float(growth.iloc[idx]), 2)
                })

        # Detectar cambios estructurales
        breaks_idx = detect_breaks(self.df["value"])
        print("DEBUG 3 - Filas después de detectar ciclos:", len(self.df))

        breaks = []

        for idx in breaks_idx:
            if idx < len(self.df):
                breaks.append({
                    "year": int(self.df.iloc[idx]["year"]),
                    "value": float(self.df.iloc[idx]["value"])
                })

        # Alertas
        alerts = []

        if growth.iloc[-1] < 0:
            alerts.append("Posible recesión")

        elif growth.iloc[-1] < growth.mean():
            alerts.append("Desaceleración económica")

        # ==========================
        # GRÁFICO PLOTLY
        # ==========================

        colors = {
            "Expansión": "green",
            "Recesión": "red",
            "Recuperación": "orange",
            "Estancamiento": "gray"
        }

        fig = go.Figure()

        for i in range(len(self.df) - 1):

            fase = cycles[i + 1]

            fig.add_trace(
                go.Scatter(
                    x=[
                        self.df.iloc[i]["year"],
                        self.df.iloc[i + 1]["year"]
                    ],
                    y=[
                        self.df.iloc[i]["value"],
                        self.df.iloc[i + 1]["value"]
                    ],
                    mode="lines+markers",
                    line=dict(
                        color=colors.get(fase, "blue"),
                        width=4
                    ),
                    marker=dict(size=8),
                    showlegend=False,
                    hovertemplate=
                    "<b>Año:</b> %{x}<br>" +
                    "<b>Valor:</b> %{y:,.0f}<br>" +
                    "<b>Fase:</b> " + fase +
                    "<extra></extra>"
                )
            )

        # Leyenda
        for fase, color in colors.items():

            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="lines",
                    line=dict(color=color, width=4),
                    name=fase
                )
            )

        fig.update_layout(
            title="Serie Económica",
            template="plotly_white",
            title_x=0.5,
            xaxis_title="Año",
            yaxis_title="Valor",
            hovermode="x unified",
            height=500
        )

        graph = fig.to_html(
            full_html=False,
            include_plotlyjs="cdn"
        )

        # ==========================
        # TABLA
        # ==========================

        table_data = []

        for i in range(len(self.df)):
            table_data.append({
                "year": int(self.df.iloc[i]["year"]),
                "value": float(self.df.iloc[i]["value"]),
                "growth": round(float(growth.iloc[i]), 2),
                "cycle": cycles[i]
            })

        return {

            "graph": graph,

            "table_data": table_data,

            "growth": growth.round(2).tolist(),

            "cycles": cycles,

            "anomalies": anomalies,

            "breaks": breaks,

            "alerts": alerts,

            "avg_growth": round(growth.mean(), 2),

            "current_phase": cycles[-1] if cycles else "Sin datos",

            "num_alerts": len(alerts),

            "num_anomalies": len(anomalies)
        }