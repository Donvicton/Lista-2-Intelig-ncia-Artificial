# -*- coding: utf-8 -*-
"""
============================================================================
 AKINATOR DOS ALIENS DE BEN 10  --  INTERFACE GRÁFICA (LOCALHOST)
============================================================================
Servidor web simples (somente biblioteca padrão do Python) que coloca uma
interface gráfica sobre o MESMO motor de inferência de `akinator_ben10.py`.

COMO USAR:
    1. Deixe este arquivo na MESMA pasta que `akinator_ben10.py`.
    2. Execute:   python akinator_web.py
    3. O navegador abre sozinho em http://localhost:8000
       (se não abrir, acesse esse endereço manualmente).

Não precisa instalar nada: usa apenas http.server / json do Python.
============================================================================
"""

import json
import random
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# --- Reaproveita a base de conhecimento e o motor de inferência ------------
try:
    from akinator_ben10 import (
        ALIENS, ATRIBUTOS, normalizar, atualizar_crencas,
        entropia, prob_sim, LIMIAR_CONFIANCA, MAX_PERGUNTAS,
    )
except ImportError:
    raise SystemExit(
        "ERRO: coloque este arquivo na mesma pasta que 'akinator_ben10.py'."
    )

PORTA = 8000

# Quão "variada" é a ordem das perguntas (0 = sempre a melhor pergunta;
# valores maiores sorteiam entre perguntas quase tão boas quanto a melhor).
VARIACAO = 0.30


def escolher_atributo(crencas, ja_perguntados):
    """
    Escolhe a próxima pergunta por GANHO DE INFORMAÇÃO, mas com VARIAÇÃO:
    em vez de pegar sempre a melhor pergunta (ordem fixa), sorteia entre
    todas as perguntas cujo ganho está perto do melhor. Assim a ordem das
    perguntas muda a cada partida, sem perder eficiência.
    """
    h_atual = entropia(crencas)
    candidatos = []
    for atributo in ATRIBUTOS:
        if atributo in ja_perguntados:
            continue
        p_sim = sum(crencas[a] * prob_sim(a, atributo) for a in crencas)
        p_nao = 1.0 - p_sim
        if p_sim <= 0 or p_nao <= 0:
            continue
        h_pos = entropia(atualizar_crencas(crencas, atributo, "sim"))
        h_neg = entropia(atualizar_crencas(crencas, atributo, "nao"))
        ganho = h_atual - (p_sim * h_pos + p_nao * h_neg)
        if ganho > 0:
            candidatos.append((ganho, atributo))

    if not candidatos:
        return None

    melhor_ganho = max(g for g, _ in candidatos)
    # Mantém só as perguntas "quase tão boas" quanto a melhor e sorteia.
    bons = [a for g, a in candidatos if g >= melhor_ganho * (1.0 - VARIACAO)]
    return random.choice(bons)

# ----------------------------------------------------------------------------
# ESTADO DO JOGO (uma partida por vez, suficiente para uso local)
# ----------------------------------------------------------------------------
ESTADO = {}


def novo_jogo():
    ESTADO.clear()
    ESTADO.update({
        "crencas": {a: 1.0 / len(ALIENS) for a in ALIENS},
        "ja_perguntados": set(),
        "descartados": set(),
        "n_perguntas": 0,
        "atributo_atual": None,
        "palpite": None,
    })


def proximo_passo():
    """Decide o que mostrar a seguir: pergunta, palpite, vitória ou derrota."""
    crencas = ESTADO["crencas"]
    ativos = normalizar({a: p for a, p in crencas.items()
                         if a not in ESTADO["descartados"]})
    topo = max(ativos, key=ativos.get)
    confianca = ativos[topo]
    vivos = [a for a, p in ativos.items() if p > 1e-6]

    # Condições de parada -> arrisca um palpite.
    if (confianca >= LIMIAR_CONFIANCA
            or ESTADO["n_perguntas"] >= MAX_PERGUNTAS
            or len(vivos) == 1):
        ESTADO["palpite"] = topo
        return {"tipo": "palpite", "alien": topo,
                "confianca": round(confianca * 100),
                "n": ESTADO["n_perguntas"]}

    atributo = escolher_atributo(ativos, ESTADO["ja_perguntados"])
    if atributo is None:
        ESTADO["palpite"] = topo
        return {"tipo": "palpite", "alien": topo,
                "confianca": round(confianca * 100),
                "n": ESTADO["n_perguntas"]}

    ESTADO["atributo_atual"] = atributo
    return {
        "tipo": "pergunta",
        "pergunta": ATRIBUTOS[atributo],
        "lider": topo,
        "confianca": round(confianca * 100),
        "n": ESTADO["n_perguntas"] + 1,
    }


def responder(resposta):
    """Aplica a resposta do usuário e devolve o próximo passo."""
    atributo = ESTADO["atributo_atual"]
    ESTADO["crencas"] = atualizar_crencas(ESTADO["crencas"], atributo, resposta)
    ESTADO["ja_perguntados"].add(atributo)
    ESTADO["n_perguntas"] += 1
    return proximo_passo()


def resultado_palpite(acertou):
    """Trata o resultado do palpite: vitória, ou descarta e continua."""
    if acertou:
        return {"tipo": "vitoria", "alien": ESTADO["palpite"],
                "n": ESTADO["n_perguntas"]}

    ESTADO["descartados"].add(ESTADO["palpite"])
    crencas = ESTADO["crencas"]
    restantes = [a for a, p in crencas.items()
                 if p > 1e-6 and a not in ESTADO["descartados"]]
    if not restantes:
        return {"tipo": "derrota"}
    return proximo_passo()


# ----------------------------------------------------------------------------
# PÁGINA HTML (interface gráfica) -- tema Omnitrix / Ben 10
# ----------------------------------------------------------------------------
PAGINA = r"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Akinator dos Aliens de Ben 10</title>
<style>
  :root { --verde:#7cfc00; --verde2:#00d26a; --escuro:#0a1f12; --painel:#12301d; }
  * { box-sizing: border-box; }
  body {
    margin:0; min-height:100vh; font-family:'Segoe UI',system-ui,sans-serif;
    background: radial-gradient(circle at 50% 0%, #133a22 0%, #050d08 70%);
    color:#eafff0; display:flex; align-items:center; justify-content:center; padding:20px;
  }
  .card {
    width:100%; max-width:560px; background:rgba(18,48,29,.92);
    border:2px solid var(--verde2); border-radius:22px; padding:34px 30px;
    box-shadow:0 0 40px rgba(0,210,106,.35); text-align:center;
  }
  .omni {
    width:84px; height:84px; margin:0 auto 14px; border-radius:50%;
    background:var(--escuro); border:6px solid var(--verde2);
    display:flex; align-items:center; justify-content:center; position:relative;
    box-shadow:0 0 22px var(--verde2);
  }
  .omni::before {
    content:""; width:42px; height:42px; background:var(--verde);
    clip-path: polygon(50% 0,100% 30%,82% 100%,18% 100%,0 30%);
    transform: rotate(0deg); box-shadow:0 0 16px var(--verde);
  }
  h1 { font-size:1.45rem; margin:.2rem 0 .1rem; letter-spacing:.5px; }
  .sub { color:#9ad9b3; font-size:.86rem; margin-bottom:22px; }
  .pergunta { font-size:1.3rem; font-weight:600; min-height:3.2em;
    display:flex; align-items:center; justify-content:center; margin:8px 0 18px; }
  .meta { font-size:.82rem; color:#9ad9b3; margin-bottom:6px; }
  .barra { height:10px; background:#06140c; border-radius:6px; overflow:hidden;
    border:1px solid #1d4a2e; margin:6px 0 22px; }
  .fill { height:100%; width:0; background:linear-gradient(90deg,var(--verde2),var(--verde));
    transition:width .4s ease; }
  .botoes { display:flex; gap:12px; flex-wrap:wrap; justify-content:center; }
  button {
    flex:1 1 30%; min-width:120px; cursor:pointer; font-size:1rem; font-weight:700;
    padding:14px 10px; border-radius:14px; border:2px solid var(--verde2);
    background:var(--escuro); color:var(--verde); transition:.15s;
  }
  button:hover { background:var(--verde2); color:#04140a; transform:translateY(-2px); }
  button.sec { border-color:#3a6b4c; color:#bfe6cf; }
  .palpite-nome { font-size:2rem; font-weight:800; color:var(--verde);
    text-shadow:0 0 18px var(--verde2); margin:10px 0; }
  .toggle-aliens { flex:none; background:none; border:none; padding:0;
    margin:-12px 0 14px; color:var(--verde); font-size:.8rem; font-weight:600;
    text-decoration:underline; cursor:pointer; }
  .toggle-aliens:hover { background:none; transform:none; color:var(--verde2); }
  .lista-aliens { display:flex; flex-wrap:wrap; gap:6px; justify-content:center;
    max-height:170px; overflow:auto; margin:0 0 20px; padding:12px;
    background:#06140c; border:1px solid #1d4a2e; border-radius:12px; }
  .chip { font-size:.74rem; padding:4px 10px; border-radius:20px;
    background:#12301d; border:1px solid var(--verde2); color:#cdeed9; }
  .hidden { display:none; }
  .rodape { margin-top:20px; font-size:.74rem; color:#6fae87; }
</style>
</head>
<body>
  <div class="card">
    <div class="omni"></div>
    <h1>Akinator dos Aliens de Ben 10</h1>
    <div class="sub">Pense em um alien... eu vou adivinhar!</div>

    <!-- LISTA DE ALIENS POSSÍVEIS -->
    <button class="toggle-aliens" onclick="toggleAliens()">
      👽 Ver os <span id="qtd-aliens">?</span> aliens que conheço</button>
    <div id="lista-aliens" class="lista-aliens hidden"></div>

    <!-- TELA: PERGUNTA -->
    <div id="tela-pergunta" class="hidden">
      <div class="meta">Pergunta <span id="num">1</span> &nbsp;•&nbsp; hipótese atual:
        <b id="lider">—</b> (<span id="conf">0</span>%)</div>
      <div class="barra"><div class="fill" id="fill"></div></div>
      <div class="pergunta" id="texto-pergunta">...</div>
      <div class="botoes">
        <button onclick="responder('sim')">✔ Sim</button>
        <button onclick="responder('nao')">✖ Não</button>
        <button class="sec" onclick="responder('nao_sei')">? Não sei</button>
      </div>
    </div>

    <!-- TELA: PALPITE -->
    <div id="tela-palpite" class="hidden">
      <div class="meta">Acho que descobri! (confiança <span id="p-conf">0</span>%)</div>
      <div class="palpite-nome" id="p-nome">—</div>
      <div class="pergunta">É esse o seu alien?</div>
      <div class="botoes">
        <button onclick="palpite(true)">✔ Acertou!</button>
        <button class="sec" onclick="palpite(false)">✖ Errou</button>
      </div>
    </div>

    <!-- TELA: FIM -->
    <div id="tela-fim" class="hidden">
      <div class="palpite-nome" id="fim-titulo">—</div>
      <div class="pergunta" id="fim-texto"></div>
      <div class="botoes">
        <button onclick="iniciar()">🔄 Jogar de novo</button>
      </div>
    </div>

    <div class="rodape">Motor de inferência Bayesiano • base de conhecimento explícita</div>
  </div>

<script>
const $ = id => document.getElementById(id);
function mostrar(tela){ ['tela-pergunta','tela-palpite','tela-fim']
  .forEach(t => $(t).classList.toggle('hidden', t!==tela)); }

async function api(rota, dados){
  const r = await fetch(rota, {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(dados||{})});
  return r.json();
}

function render(d){
  if(d.tipo === 'pergunta'){
    $('texto-pergunta').textContent = d.pergunta;
    $('num').textContent = d.n;
    $('lider').textContent = d.lider;
    $('conf').textContent = d.confianca;
    $('fill').style.width = d.confianca + '%';
    mostrar('tela-pergunta');
  } else if(d.tipo === 'palpite'){
    $('p-nome').textContent = d.alien;
    $('p-conf').textContent = d.confianca;
    mostrar('tela-palpite');
  } else if(d.tipo === 'vitoria'){
    $('fim-titulo').textContent = '🎉 Acertei!';
    $('fim-texto').textContent = 'Seu alien era ' + d.alien + ' — descoberto em ' + d.n + ' perguntas.';
    mostrar('tela-fim');
  } else if(d.tipo === 'derrota'){
    $('fim-titulo').textContent = '🛸 Você venceu!';
    $('fim-texto').textContent = 'Desisto — não consegui descobrir o seu alien.';
    mostrar('tela-fim');
  }
}

function renderAliens(lista){
  $('qtd-aliens').textContent = lista.length;
  $('lista-aliens').innerHTML = lista.map(a => '<span class="chip">'+a+'</span>').join('');
}
function toggleAliens(){ $('lista-aliens').classList.toggle('hidden'); }

async function iniciar(){
  const d = await api('/api/iniciar');
  if(d.aliens) renderAliens(d.aliens);
  render(d);
}
async function responder(r){ render(await api('/api/responder', {resposta:r})); }
async function palpite(ac){ render(await api('/api/palpite', {acertou:ac})); }

iniciar();
</script>
</body>
</html>"""


# ----------------------------------------------------------------------------
# SERVIDOR HTTP
# ----------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def _json(self, dados):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _html(self):
        corpo = PAGINA.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _ler_json(self):
        tam = int(self.headers.get("Content-Length", 0))
        if tam == 0:
            return {}
        return json.loads(self.rfile.read(tam).decode("utf-8"))

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._html()
        else:
            self.send_error(404)

    def do_POST(self):
        try:
            if self.path == "/api/iniciar":
                novo_jogo()
                payload = proximo_passo()
                # Envia também a lista de aliens conhecidos (para a interface).
                payload["aliens"] = sorted(ALIENS.keys())
                self._json(payload)
            elif self.path == "/api/responder":
                resposta = self._ler_json().get("resposta", "nao_sei")
                self._json(responder(resposta))
            elif self.path == "/api/palpite":
                acertou = bool(self._ler_json().get("acertou", False))
                self._json(resultado_palpite(acertou))
            else:
                self.send_error(404)
        except Exception as e:  # noqa
            self._json({"tipo": "erro", "msg": str(e)})

    def log_message(self, *args):
        pass  # silencia o log no terminal


def main():
    novo_jogo()
    servidor = ThreadingHTTPServer(("127.0.0.1", PORTA), Handler)
    url = f"http://localhost:{PORTA}"
    print("=" * 56)
    print("  AKINATOR DOS ALIENS DE BEN 10  -  interface web")
    print(f"  Servidor rodando em: {url}")
    print("  Pressione Ctrl+C para encerrar.")
    print("=" * 56)
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando. Até a próxima!")
        servidor.shutdown()


if __name__ == "__main__":
    main()
