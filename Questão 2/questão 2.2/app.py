"""
Servidor Flask — Sistema de Diagnóstico Médico com Redes Bayesianas
"""

try:
    from flask import Flask, render_template, request, jsonify
except ImportError as exc:
    raise ImportError(
        "Flask is required to run this application. Install it with "
        "pip install Flask"
    ) from exc

from pgmpy.models import DiscreteBayesianNetwork as BayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
import warnings
import json

warnings.filterwarnings("ignore")

app = Flask(__name__)


def construir_rede():
    arestas = [
        ("Idoso", "Gripe"),
        ("Idoso", "Pneumonia"),
        ("Idoso", "COVID19"),
        ("Fumante", "Pneumonia"),
        ("Gripe", "Febre"),
        ("Gripe", "Tosse"),
        ("Gripe", "DorMuscular"),
        ("Pneumonia", "Febre"),
        ("Pneumonia", "Tosse"),
        ("Pneumonia", "Dispneia"),
        ("COVID19", "Febre"),
        ("COVID19", "Tosse"),
        ("COVID19", "DorMuscular"),
        ("COVID19", "Dispneia"),
        ("COVID19", "PerdaOlfato"),
    ]

    modelo = BayesianNetwork(arestas)

    cpd_idoso = TabularCPD("Idoso", 2, [[0.85], [0.15]])
    cpd_fumante = TabularCPD("Fumante", 2, [[0.88], [0.12]])

    cpd_gripe = TabularCPD(
        "Gripe", 2,
        [[0.90, 0.80], [0.10, 0.20]],
        evidence=["Idoso"], evidence_card=[2]
    )

    cpd_pneumonia = TabularCPD(
        "Pneumonia", 2,
        [[0.97, 0.92, 0.88, 0.75], [0.03, 0.08, 0.12, 0.25]],
        evidence=["Idoso", "Fumante"], evidence_card=[2, 2]
    )

    cpd_covid = TabularCPD(
        "COVID19", 2,
        [[0.95, 0.88], [0.05, 0.12]],
        evidence=["Idoso"], evidence_card=[2]
    )

    cpd_febre = TabularCPD(
        "Febre", 2,
        [[0.95, 0.12, 0.15, 0.05, 0.10, 0.05, 0.05, 0.02],
         [0.05, 0.88, 0.85, 0.95, 0.90, 0.95, 0.95, 0.98]],
        evidence=["Gripe", "Pneumonia", "COVID19"],
        evidence_card=[2, 2, 2]
    )

    cpd_tosse = TabularCPD(
        "Tosse", 2,
        [[0.90, 0.20, 0.15, 0.08, 0.25, 0.10, 0.08, 0.03],
         [0.10, 0.80, 0.85, 0.92, 0.75, 0.90, 0.92, 0.97]],
        evidence=["Gripe", "Pneumonia", "COVID19"],
        evidence_card=[2, 2, 2]
    )

    cpd_dor = TabularCPD(
        "DorMuscular", 2,
        [[0.92, 0.25, 0.20, 0.10], [0.08, 0.75, 0.80, 0.90]],
        evidence=["Gripe", "COVID19"], evidence_card=[2, 2]
    )

    cpd_dispneia = TabularCPD(
        "Dispneia", 2,
        [[0.96, 0.40, 0.30, 0.15], [0.04, 0.60, 0.70, 0.85]],
        evidence=["Pneumonia", "COVID19"], evidence_card=[2, 2]
    )

    cpd_olfato = TabularCPD(
        "PerdaOlfato", 2,
        [[0.98, 0.30], [0.02, 0.70]],
        evidence=["COVID19"], evidence_card=[2]
    )

    modelo.add_cpds(
        cpd_idoso, cpd_fumante,
        cpd_gripe, cpd_pneumonia, cpd_covid,
        cpd_febre, cpd_tosse, cpd_dor, cpd_dispneia, cpd_olfato
    )

    assert modelo.check_model()
    return modelo


modelo = construir_rede()
inferencia = VariableElimination(modelo)


def calcular_priori():
    resultados = {}
    for d in ["Gripe", "Pneumonia", "COVID19"]:
        q = inferencia.query([d])
        resultados[d] = round(float(q.values[1]) * 100, 2)
    return resultados


PRIORI = calcular_priori()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/diagnostico", methods=["POST"])
def diagnostico():
    dados = request.get_json()
    evidencias = {}

    if dados.get("idoso") is not None:
        evidencias["Idoso"] = int(dados["idoso"])
    if dados.get("fumante") is not None:
        evidencias["Fumante"] = int(dados["fumante"])
    if dados.get("febre") is not None:
        evidencias["Febre"] = int(dados["febre"])
    if dados.get("tosse") is not None:
        evidencias["Tosse"] = int(dados["tosse"])
    if dados.get("dor_muscular") is not None:
        evidencias["DorMuscular"] = int(dados["dor_muscular"])
    if dados.get("dispneia") is not None:
        evidencias["Dispneia"] = int(dados["dispneia"])
    if dados.get("perda_olfato") is not None:
        evidencias["PerdaOlfato"] = int(dados["perda_olfato"])

    if not evidencias:
        return jsonify({"erro": "Nenhuma evidência fornecida"}), 400

    doencas = ["Gripe", "Pneumonia", "COVID19"]
    resultados = {}
    etapas = []

    chaves_ordenadas = list(evidencias.keys())
    evidencias_acumuladas = {}

    for i, chave in enumerate(chaves_ordenadas):
        evidencias_acumuladas[chave] = evidencias[chave]

        etapa_resultado = {}
        for d in doencas:
            if d in evidencias_acumuladas:
                etapa_resultado[d] = round(float(evidencias_acumuladas[d]) * 100, 2)
            else:
                q = inferencia.query([d], evidence=evidencias_acumuladas)
                etapa_resultado[d] = round(float(q.values[1]) * 100, 2)

        nomes_bonitos = {
            "Idoso": "Idoso", "Fumante": "Fumante", "Febre": "Febre",
            "Tosse": "Tosse", "DorMuscular": "Dor Muscular",
            "Dispneia": "Falta de Ar", "PerdaOlfato": "Perda de Olfato"
        }
        ev_label = nomes_bonitos.get(chave, chave)
        val_label = "Sim" if evidencias_acumuladas[chave] == 1 else "Não"

        etapas.append({
            "evidencia_adicionada": f"{ev_label} = {val_label}",
            "evidencias_totais": {nomes_bonitos.get(k, k): ("Sim" if v == 1 else "Não")
                                  for k, v in evidencias_acumuladas.items()},
            "probabilidades": etapa_resultado
        })

    resultado_final = etapas[-1]["probabilidades"]

    doenca_principal = max(resultado_final, key=resultado_final.get)

    return jsonify({
        "priori": PRIORI,
        "etapas": etapas,
        "resultado_final": resultado_final,
        "doenca_principal": doenca_principal,
        "evidencias_usadas": {k: ("Sim" if v == 1 else "Não") for k, v in evidencias.items()}
    })


if __name__ == "__main__":
    print("\n  Sistema de Diagnostico Medico - Redes Bayesianas")
    print("  Acesse: http://localhost:5000\n")
    app.run(debug=True, port=5000)
