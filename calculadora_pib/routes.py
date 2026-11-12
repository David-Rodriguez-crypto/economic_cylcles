from flask import Blueprint, render_template, request

calculadora_pib = Blueprint(
    "calculadora_pib",
    __name__,
    template_folder="templates"
)

def numero_a_palabras(n):

    unidades = (
        "", "uno", "dos", "tres", "cuatro",
        "cinco", "seis", "siete", "ocho", "nueve"
    )

    especiales = {
        10: "diez",
        11: "once",
        12: "doce",
        13: "trece",
        14: "catorce",
        15: "quince",
        16: "dieciséis",
        17: "diecisiete",
        18: "dieciocho",
        19: "diecinueve",
        20: "veinte"
    }

    decenas = (
        "", "", "veinte", "treinta", "cuarenta",
        "cincuenta", "sesenta", "setenta",
        "ochenta", "noventa"
    )

    centenas = (
        "", "ciento", "doscientos", "trescientos",
        "cuatrocientos", "quinientos",
        "seiscientos", "setecientos",
        "ochocientos", "novecientos"
    )

    grandes = [
        (10**18, "trillón", "trillones"),
        (10**12, "billón", "billones"),
        (10**6, "millón", "millones"),
        (1000, "mil", "mil")
    ]

    def convertir(num):

        if num == 0:
            return "cero"

        if num < 1000:

            if num == 100:
                return "cien"

            texto = ""

            if num >= 100:
                c = num // 100
                texto += centenas[c] + " "
                num %= 100

            if 10 <= num <= 20:
                texto += especiales[num]

            elif 21 <= num <= 29:
                texto += "veinti" + unidades[num - 20]

            elif num >= 30:
                d = num // 10
                u = num % 10

                texto += decenas[d]

                if u:
                    texto += " y " + unidades[u]

            else:
                texto += unidades[num]

            return texto.strip()

        for valor, singular, plural in grandes:

            if num >= valor:

                cantidad = num // valor
                resto = num % valor

                if valor == 1000:

                    if cantidad == 1:
                        texto = "mil"
                    else:
                        texto = convertir(cantidad) + " mil"

                else:

                    if cantidad == 1:
                        texto = "un " + singular
                    else:
                        texto = convertir(cantidad) + " " + plural

                if resto:
                    texto += " " + convertir(resto)

                return texto

    return convertir(n)


@calculadora_pib.route("/", methods=["GET", "POST"])
def index():

    datos = None

    if request.method == "POST":

        consumo = float(request.form["consumo"])
        inversion = float(request.form["inversion"])
        gasto = float(request.form["gasto"])
        exportaciones = float(request.form["exportaciones"])
        importaciones = float(request.form["importaciones"])

        pib = consumo + inversion + gasto + (exportaciones - importaciones)

        datos = {
            "pib": pib,
            "texto": numero_a_palabras(int(pib)),
            "categorias": [
                "Consumo",
                "Inversión",
                "Gasto Público",
                "Exportaciones",
                "Importaciones"
            ],
            "valores": [
                consumo,
                inversion,
                gasto,
                exportaciones,
                importaciones
            ]
        }

    return render_template(
        "calculadora_pib/index.html",
        datos=datos
    )