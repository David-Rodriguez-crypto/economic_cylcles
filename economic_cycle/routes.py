from flask import Blueprint, render_template, request, send_file, session, redirect, url_for,flash
import pandas as pd
import os
from .services.analyzer import EconomicAnalyzer
from .services.pdf_report import create_pdf

from .services.database import (
    get_countries,
    get_gdp_by_country,
    create_country,
    save_gdp,
    save_gdp_bulk,
    get_or_create_country
)





economic_cycle = Blueprint(
    "economic_cycle",
    __name__,
    template_folder="templates",
    static_folder="static"
)


# ==========================================================
# INICIO
# ==========================================================
@economic_cycle.route('/crear-pais', methods=['GET', 'POST'])
def crear_pais():

    if request.method == 'POST':

        name = request.form['name'].strip()
        code = request.form['code'].strip().upper()

        # Validar nombre
        if not name:
            flash('Debe ingresar un nombre para el país.', 'danger')
            return redirect(url_for('economic_cycle.crear_pais'))

        # Validar código
        if len(code) != 3:
            flash('El código del país debe tener exactamente 3 caracteres.', 'danger')
            return redirect(url_for('economic_cycle.crear_pais'))

        try:

            country_id = create_country(name, code)

            flash(
                f'¡País "{name}" creado correctamente!',
                'success'
            )

            return redirect(url_for('economic_cycle.home'))

        except Exception as e:

            flash(
                f'No fue posible crear el país: {str(e)}',
                'danger'
            )

            return redirect(url_for('economic_cycle.crear_pais'))

    return render_template('create_country.html')

@economic_cycle.route("/")
def home():

    countries = get_countries()

    return render_template(
        "economic_cycle/index.html",
        countries=countries
    )


# ==========================================================
# ANALIZAR PAÍS DESDE MYSQL
# ==========================================================

@economic_cycle.route("/analyze-country", methods=["POST"])
def analyze_country():

    country_id = request.form.get("country_id")

    if not country_id:
        return "Debe seleccionar un país."

    try:

        # Obtener PIB desde MySQL
        data = get_gdp_by_country(int(country_id))

        if not data:
            return "Este país no tiene datos de PIB."

        # Convertir a DataFrame
        df = pd.DataFrame(data)

        # Analizar
        analyzer = EconomicAnalyzer(df)

        results = analyzer.run_analysis()

        # ==============================================
        # GUARDAR DATOS PARA EL PDF
        # ==============================================

        pdf_results = results.copy()

        # No guardar el HTML de Plotly en la sesión
        pdf_results["graph"] = ""

        session["results"] = pdf_results

        # ==============================================
        # MOSTRAR DASHBOARD
        # ==============================================

        return render_template(
            "economic_cycle/dashboard.html",
            results=results
        )

    except Exception as e:

        return f"Error al analizar los datos: {str(e)}"


# ==========================================================
# INGRESAR DATOS ECONÓMICOS DE UN PAÍS
# ==========================================================


@economic_cycle.route("/country-data", methods=["GET", "POST"])
def country_data():

    # Valores que se mostrarán nuevamente en el formulario
    form_data = {
        "country_name": "",
        "country_code": "",
        "year": "",
        "value": ""
    }

    if request.method == "POST":

        name = request.form.get("country_name", "").strip()
        code = request.form.get("country_code", "").strip().upper()
        year_text = request.form.get("year", "")
        value_text = request.form.get("value", "").strip()

        # Conservar los valores escritos por el usuario
        form_data = {
            "country_name": name,
            "country_code": code,
            "year": year_text,
            "value": value_text
        }

        if not name or not code or year_text is None or not value_text:
            flash("Completa todos los campos.", "danger")
            return redirect(url_for("economic_cycle.country_data"))

        if len(code) != 3 or not code.isalpha():
            flash("El código debe tener 3 letras, por ejemplo ARG.", "danger")
            return redirect(url_for("economic_cycle.country_data"))
        else:
            try:
                year = int(year_text)
                value = float(value_text)

                if not 1800 <= year <= 2100:
                    raise ValueError("El año debe estar entre 1800 y 2100.")

                if not pd.notna(value) or not 0 <= value < float("inf"):
                    raise ValueError("El PIB debe ser un número válido y no negativo.")

                country_id = get_or_create_country(name, code)
                save_gdp(country_id, year, value)

                flash(
                    f"Datos del PIB de {name} guardados correctamente.",
                    "success"
                )

            except ValueError as error:
                print("ERROR DE VALIDACIÓN:", repr(error))
                flash(str(error), "danger")

            except Exception as error:
                print("ERROR REAL AL GUARDAR EL PIB:", repr(error))

                if "1062" in str(error) or "Duplicate entry" in str(error):
                    flash(
                        "Ese país ya tiene datos registrados para ese año, "
                        "o el código pertenece a otro país.",
                        "danger"
                    )
                else:
                    flash(
                        f"No fue posible guardar los datos económicos: {error}",
                        "danger"
                    )
        return render_template(
            "economic_cycle/country_data.html",
            countries=get_countries(),
            form_data=form_data
        )
    return render_template(
        "economic_cycle/country_data.html",
        countries=get_countries(),
        form_data=form_data
    )        

# ==========================================================
# ANALIZAR ARCHIVO CSV / EXCEL
# ==========================================================
@economic_cycle.route("/download-template")
def download_template():

    archivo = os.path.join(
        economic_cycle.root_path,
        "static",
        "plantilla_datos_economicos.xlsx"
    )

    return send_file(
        archivo,
        as_attachment=True,
        download_name="plantilla_datos_economicos.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@economic_cycle.route("/analyze", methods=["POST"])
def analyze():

    file = request.files.get("file")

    if not file or file.filename == "":
        return "No se seleccionó ningún archivo."

    filename = file.filename.lower()

    try:

        # ==============================================
        # EXCEL
        # ==============================================

        if filename.endswith(".xlsx") or filename.endswith(".xls"):

            df = pd.read_excel(file)

        # ==============================================
        # CSV
        # ==============================================

        elif filename.endswith(".csv"):

            try:

                df = pd.read_csv(
                    file,
                    sep=";",
                    encoding="utf-8"
                )

            except UnicodeDecodeError:

                file.seek(0)

                df = pd.read_csv(
                    file,
                    sep=";",
                    encoding="latin1"
                )

        else:

            return "Formato de archivo no soportado."

        # ==============================================
        # LIMPIAR COLUMNAS
        # ==============================================

        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
        )

        print("\n===== VERIFICACIÓN DEL ARCHIVO =====")
        print("Filas leídas:", len(df))
        print("Columnas:", df.columns.tolist())
        print("Años encontrados:", df["year"].tolist())

        # ==============================================
        # ANALIZAR
        # ==============================================

        analyzer = EconomicAnalyzer(df)

        results = analyzer.run_analysis()

        print("Años procesados:", len(results["table_data"]))
        print("Tabla generada:", results["table_data"])
        print("====================================\n")
        # ==============================================
        # GUARDAR RESULTADOS PARA PDF
        # ==============================================

        pdf_results = results.copy()

        # No guardar Plotly en session
        pdf_results["graph"] = ""

        session["results"] = pdf_results

        # ==============================================
        # DASHBOARD
        # ==============================================

        return render_template(
            "economic_cycle/dashboard.html",
            results=results
        )

    except Exception as e:

        return f"Error al procesar el archivo: {str(e)}"


# ==========================================================
# GENERAR PDF
# ==========================================================

@economic_cycle.route("/pdf")
def pdf():

    results = session.get("results")

    if not results:

        return (
            "No existe un análisis para generar el PDF.",
            400
        )

    try:

        archivo = create_pdf(results)

        return send_file(
            archivo,
            as_attachment=True,
            download_name="reporte_economico.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:

        return f"Error al generar el PDF: {str(e)}"


# ==========================================================
# IMPORTAR DATOS ECONÓMICOS DESDE EXCEL
# ==========================================================


@economic_cycle.route("/import-gdp-excel", methods=["POST"])
def import_gdp_excel():

    name = request.form.get("country_name", "").strip()
    code = request.form.get("country_code", "").strip().upper()
    file = request.files.get("file")

    # Validar nombre y código
    if not name or len(name) > 100:
        flash("Introduce un nombre de país válido.", "danger")
        return redirect(url_for("economic_cycle.country_data"))

    if len(code) != 3 or not code.isalpha():
        flash("El código del país debe contener tres letras.", "danger")
        return redirect(url_for("economic_cycle.country_data"))

    # Validar archivo
    if not file or not file.filename:
        flash("Selecciona un archivo Excel.", "danger")
        return redirect(url_for("economic_cycle.country_data"))

    if not file.filename.lower().endswith(".xlsx"):
        flash("El archivo debe tener formato .xlsx.", "danger")
        return redirect(url_for("economic_cycle.country_data"))

    try:
        df = pd.read_excel(file, engine="openpyxl")

        # Normalizar nombres de columnas
        df.columns = [
            str(col).strip().lower()
            for col in df.columns
        ]

        if not {"year", "value"}.issubset(df.columns):
            raise ValueError(
                "El Excel debe contener las columnas year y value."
            )

        df = df[["year", "value"]].copy()

        if df.empty:
            raise ValueError("El archivo Excel no contiene registros.")

        # Validar datos numéricos
        df["year"] = pd.to_numeric(df["year"], errors="raise")
        df["value"] = pd.to_numeric(df["value"], errors="raise")

        if df.isnull().any().any():
            raise ValueError("Hay celdas vacías en year o value.")

        # Validar años enteros
        if not df["year"].apply(
            lambda x: float(x).is_integer()
        ).all():
            raise ValueError("Los años deben ser números enteros.")

        df["year"] = df["year"].astype(int)

        if not df["year"].between(1800, 2100).all():
            raise ValueError("Los años deben estar entre 1800 y 2100.")

        # Validar valores del PIB: finitos y no negativos
        if not df["value"].map(
            lambda x: pd.notna(x)
            and float("-inf") < float(x) < float("inf")
        ).all():
            raise ValueError("Los valores del PIB deben ser números finitos.")

        if (df["value"] < 0).any():
            raise ValueError("Los valores del PIB no pueden ser negativos.")

        if df["year"].duplicated().any():
            raise ValueError("El Excel contiene años repetidos.")

        records = [
            (int(row.year), round(float(row.value), 2))
            for row in df.itertuples(index=False)
        ]

        # Obtener el ID del país o crearlo
        country_id = get_or_create_country(name, code)

        # Guardar todos los registros
        save_gdp_bulk(country_id, records)

        flash(
            f"Se importaron {len(records)} registros del PIB "
            f"para {name} ({code}).",
            "success"
        )

    except ValueError as e:
        flash(f"No se pudo importar el Excel: {e}", "danger")

    except Exception as e:
        if "1062" in str(e) or "Duplicate entry" in str(e):
            flash(
                "La importación se canceló porque uno o más años "
                "ya existen para este país. No se guardaron "
                "registros nuevos.",
                "danger"
            )
        else:
            flash(
                "No fue posible procesar el Excel. "
                "Comprueba los datos y vuelve a intentarlo.",
                "danger"
            )

    return redirect(url_for("economic_cycle.country_data"))
