from flask import Blueprint, render_template, request
import pandas as pd
import numpy as np

proyeccion_pib = Blueprint(
    "proyeccion_pib",
    __name__,
    template_folder="templates"
)

@proyeccion_pib.route("/", methods=["GET", "POST"])
def index():

    resultados = None

    if (
        request.method == "POST"
        and request.form.get("accion") == "calcular"
    ):

        num_years = int(request.form["num_years"])

        years = []
        gdp_values = []

        for i in range(num_years):
            years.append(int(request.form[f"year_{i}"]))
            gdp_values.append(float(request.form[f"gdp_{i}"]))

        df = pd.DataFrame({
            "Año": years,
            "PIB": gdp_values
        })

        df = df.sort_values("Año")

        growth_rates = []

        for i in range(1, len(df)):
            previous = df.iloc[i - 1]["PIB"]
            current = df.iloc[i]["PIB"]

            growth = (current - previous) / previous
            growth_rates.append(growth)

        average_growth = np.mean(growth_rates)

        last_year = int(df.iloc[-1]["Año"])
        last_gdp = df.iloc[-1]["PIB"]

        projected_gdp = last_gdp * (1 + average_growth)

        next_year = last_year + 1

        chart_years = years + [next_year]
        chart_values = gdp_values + [projected_gdp]

        resultados = {
            "tabla": df.to_dict("records"),
            "average_growth": round(average_growth * 100, 2),
            "projected_gdp": round(projected_gdp, 2),
            "next_year": next_year,
            "chart_years": chart_years,
            "chart_values": chart_values
        }

    return render_template(
        "proyeccion_pib/index.html",
        resultados=resultados
    )