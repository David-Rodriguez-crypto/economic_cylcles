
import os
from flask import Flask, render_template
from calculadora_pib.routes import calculadora_pib
from proyeccion_pib.routes import proyeccion_pib
from economic_cycle.routes import economic_cycle
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "clave-temporal-solo-desarrollo"
)


app.register_blueprint(
    calculadora_pib,
    url_prefix="/calculadora"
)

app.register_blueprint(
    proyeccion_pib,
    url_prefix="/proyeccion"
)

app.register_blueprint(
    economic_cycle,
    url_prefix="/ciclos"
)


@app.route("/")
def menu():
    return render_template("menu.html")


if __name__ == "__main__":
    app.run(debug=False)
