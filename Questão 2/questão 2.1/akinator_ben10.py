# -*- coding: utf-8 -*-
"""
============================================================================
 AKINATOR DOS ALIENS DE BEN 10
============================================================================
Questão 2.1 - Sistema Inteligente de Perguntas e Respostas estilo Akinator

DOMÍNIO ESCOLHIDO:
    Personagens de desenhos -> os aliens (formas alienígenas) de Ben 10.

ESTRATÉGIA DE REPRESENTAÇÃO DO CONHECIMENTO:
    Modelo atributo-valor. Cada alien (entidade) é descrito por um conjunto
    de atributos booleanos (características). A base de conhecimento é a
    estrutura `ALIENS`, onde para cada alien guardamos o conjunto de
    atributos que ele POSSUI. Os atributos que não estão no conjunto são
    considerados ausentes.

MECANISMO DE INFERÊNCIA:
    Abordagem probabilística (Rede Bayesiana ingênua / "Naive Bayes" +
    busca no espaço de hipóteses).
      - Cada alien começa com uma probabilidade a priori igual.
      - A cada resposta do usuário, a crença em cada candidato é atualizada
        de forma multiplicativa (Teorema de Bayes), de acordo com a
        probabilidade de aquele alien gerar a resposta dada.
      - As probabilidades são renormalizadas a cada passo.
      - A próxima pergunta é escolhida por GANHO DE INFORMAÇÃO: o sistema
        seleciona o atributo que melhor divide a massa de probabilidade
        atual (atributo cuja probabilidade esperada de "sim" está mais
        próxima de 50%), reduzindo a incerteza o mais rápido possível.
    Essa abordagem trata naturalmente respostas "Não sei" e tolera
    eventuais erros/ruído nas respostas do usuário.

REQUISITOS ATENDIDOS:
    - 29 entidades (>= 20 exigidas)
    - 19 atributos (>= 15 exigidos)
    - Representação explícita do conhecimento
    - Perguntas sequenciais; respostas Sim / Não / Não sei
    - Exibe a hipótese mais provável e encerra ao identificar a solução
============================================================================
"""

import math

# ----------------------------------------------------------------------------
# 1) BASE DE CONHECIMENTO
# ----------------------------------------------------------------------------

# Dicionário: atributo -> pergunta apresentada ao usuário.
ATRIBUTOS = {
    "voa":               "Ele pode voar?",
    "humanoide":         "Ele tem formato humanoide (tronco, dois braços, duas pernas, anda em pé)?",
    "controla_fogo":     "Ele controla fogo ou calor?",
    "controla_gelo":     "Ele controla gelo ou frio?",
    "baseado_inseto":    "Ele é baseado em um inseto ou aracnídeo?",
    "baseado_reptil":    "Ele é baseado em um réptil ou dinossauro?",
    "aquatico":          "Ele é aquático / ligado à água?",
    "tem_cauda":         "Ele tem cauda?",
    "super_forca":       "Ele possui super força?",
    "pequeno":           "A altura dele é < 1,60m ?",
    "gigante":           "A altura dele é > 2,10m ?",
    "intangivel":        "Ele é intangível / fantasmagórico (pode atravessar paredes)?",
    "corpo_mineral":     "O corpo dele é feito de mineral (cristal, rocha, metal ou armadura)?",
    "energia":           "Ele manipula energia, eletricidade ou radiação?",
    "muitos_bracos":     "Ele tem quatro ou mais braços?",
    "felpudo":           "Ele tem pelos / pelagem?",
    "super_inteligente": "Ele é extremamente inteligente (gênio)?",
    "duplica":           "Ele consegue criar cópias de si mesmo?",
    "super_velocidade":  "Ele tem super velocidade?",
    "escava":            "Ele perfura ou escava o solo?",
    "rola_esfera":       "Ele se enrola em forma de esfera para atacar?",
    "cheiro":            "Ele é caracterizado pelo seu cheiro?",
}

# Para cada alien, o CONJUNTO de atributos que ele POSSUI.
# (Os atributos ausentes do conjunto são considerados "não possui".)
ALIENS = {
    "Friagem":          {"voa", "humanoide", "controla_gelo", "baseado_inseto", "intangivel"},
    "Fantasmático":     {"voa", "humanoide", "intangivel"},
    "Chama":            {"humanoide", "controla_fogo", "corpo_mineral"},
    "Diamante":         {"humanoide", "super_forca", "corpo_mineral", "gigante"},
    "Massa Cinzenta":   {"humanoide", "pequeno", "super_inteligente"},
    "Bloxx":            {"humanoide", "super_forca", "corpo_mineral", "gigante", "rola_esfera"},
    "Macaco Aranha":    {"humanoide", "baseado_inseto", "muitos_bracos", "felpudo", "tem_cauda", "pequeno", "super_forca"},
    "Enormossauro":     {"humanoide", "baseado_reptil", "super_forca", "gigante", "tem_cauda"},
    "Fogo Fátuo":       {"humanoide", "controla_fogo", "gigante"},
    "Eco Eco":          {"humanoide", "pequeno", "duplica", "corpo_mineral"},
    "Aquático":         {"humanoide", "aquatico", "tem_cauda"},
    "Ultra T":          {"humanoide", "energia"},
    "Bala de Canhão":   {"humanoide", "super_forca", "corpo_mineral", "rola_esfera", "gigante"},
    "Ameaça Aquática":  {"humanoide", "aquatico", "corpo_mineral"},
    "Acelerado":        {"humanoide", "super_velocidade", "felpudo"},
    "Alien X":          {"humanoide", "super_forca", "super_inteligente", "voa", "energia", "controla_fogo", "controla_gelo", "gigante"},
    "Anfíbio":          {"aquatico", "energia", "voa"},
    "Armatu":           {"humanoide", "super_forca", "corpo_mineral", "escava", "gigante"},
    "NRG":              {"humanoide", "energia", "corpo_mineral", "super_forca"},
    "Tartagira":        {"humanoide", "baseado_reptil", "voa"},
    "XLR8":             {"humanoide", "baseado_reptil", "super_velocidade", "tem_cauda"},
    "Glutão":           {"humanoide", "pequeno"},
    "Gigante":          {"humanoide", "gigante", "super_forca", "energia"},
    "Podrão":           {"humanoide", "cheiros", "gigante"},
    "Quatro Braços":    {"humanoide", "muitos_bracos", "super_forca", "gigante"},
    "Rath":             {"humanoide", "felpudo", "super_forca", "gigante"},
    "Idem":             {"humanoide", "pequeno", "duplica"},
    "Iguana Ártica":    {"humanoide", "baseado_reptil", "controla_gelo", "tem_cauda"},
    "Insectóide":       {"baseado_inseto", "voa", "tem_cauda", "cheiros", "gigante"},
    "Artrópode":        {"super_inteligente", "baseado_inseto", "energia"},
    "Feedback":         {"humanoide", "energia", "cauda", "super_velocidade"},
    "Cromático":        {"humanoide", "energia", "voa", "corpo_mineral"},
}

# ----------------------------------------------------------------------------
# 2) PARÂMETROS DO MODELO PROBABILÍSTICO
# ----------------------------------------------------------------------------

# P(usuário responder "sim" | alien possui o atributo)
P_SIM_SE_POSSUI = 0.95
# P(usuário responder "sim" | alien NÃO possui o atributo)
P_SIM_SE_NAO_POSSUI = 0.05
# (o restante da massa corresponde a "não"; "não sei" não altera a crença)

# Limiar de confiança para o sistema arriscar um palpite.
LIMIAR_CONFIANCA = 0.90
# Máximo de perguntas antes de chutar mesmo assim.
MAX_PERGUNTAS = 20


def prob_sim(alien, atributo):
    """Probabilidade de o usuário dizer 'sim' para `atributo`, dado `alien`."""
    if atributo in ALIENS[alien]:
        return P_SIM_SE_POSSUI
    return P_SIM_SE_NAO_POSSUI


# ----------------------------------------------------------------------------
# 3) MOTOR DE INFERÊNCIA
# ----------------------------------------------------------------------------

def normalizar(crencas):
    """Renormaliza as probabilidades para somarem 1."""
    total = sum(crencas.values())
    if total <= 0:
        # Evita divisão por zero: redistribui uniformemente.
        n = len(crencas)
        return {a: 1.0 / n for a in crencas}
    return {a: p / total for a, p in crencas.items()}


def atualizar_crencas(crencas, atributo, resposta):
    """
    Aplica o Teorema de Bayes: multiplica a crença de cada alien pela
    verossimilhança da resposta observada.
        resposta: 'sim', 'nao' ou 'nao_sei'
    """
    if resposta == "nao_sei":
        return crencas  # não traz informação -> não altera nada

    novas = {}
    for alien, p in crencas.items():
        ps = prob_sim(alien, atributo)
        verossimilhanca = ps if resposta == "sim" else (1.0 - ps)
        novas[alien] = p * verossimilhanca
    return normalizar(novas)


def entropia(crencas):
    """Entropia de Shannon do conjunto de hipóteses (medida de incerteza)."""
    h = 0.0
    for p in crencas.values():
        if p > 0:
            h -= p * math.log2(p)
    return h


def melhor_atributo(crencas, ja_perguntados):
    """
    Escolhe o próximo atributo por GANHO DE INFORMAÇÃO.
    Calcula a entropia esperada após perguntar cada atributo ainda não
    usado e retorna aquele que mais reduz a incerteza.
    """
    melhor, melhor_ganho = None, -1.0
    h_atual = entropia(crencas)

    for atributo in ATRIBUTOS:
        if atributo in ja_perguntados:
            continue

        # Probabilidade esperada de o usuário responder "sim".
        p_sim = sum(crencas[a] * prob_sim(a, atributo) for a in crencas)
        p_nao = 1.0 - p_sim
        if p_sim <= 0 or p_nao <= 0:
            continue  # atributo não separa ninguém

        # Entropia esperada após a resposta (ignorando "não sei").
        h_pos = entropia(atualizar_crencas(crencas, atributo, "sim"))
        h_neg = entropia(atualizar_crencas(crencas, atributo, "nao"))
        h_esperada = p_sim * h_pos + p_nao * h_neg

        ganho = h_atual - h_esperada
        if ganho > melhor_ganho:
            melhor_ganho, melhor = ganho, atributo

    return melhor


# ----------------------------------------------------------------------------
# 4) INTERAÇÃO COM O USUÁRIO
# ----------------------------------------------------------------------------

RESPOSTAS = {
    "s": "sim", "sim": "sim", "1": "sim",
    "n": "nao", "nao": "nao", "não": "nao", "2": "nao",
    "?": "nao_sei", "ns": "nao_sei", "nao sei": "nao_sei",
    "não sei": "nao_sei", "3": "nao_sei",
}


def perguntar(texto):
    """Faz uma pergunta e devolve 'sim' / 'nao' / 'nao_sei'."""
    while True:
        bruto = input(f"\n{texto}\n  [S]im / [N]ão / [?] Não sei: ").strip().lower()
        if bruto in RESPOSTAS:
            return RESPOSTAS[bruto]
        print("  >> Resposta inválida. Digite S, N ou ?.")


def jogar():
    print("=" * 64)
    print("   AKINATOR DOS ALIENS DE BEN 10")
    print("=" * 64)
    print("Pense em um dos aliens do Ben 10 e responda às minhas perguntas.")
    print(f"(Conheço {len(ALIENS)} aliens.)")

    # Prior uniforme.
    crencas = {a: 1.0 / len(ALIENS) for a in ALIENS}
    ja_perguntados = set()
    descartados = set()
    n_perguntas = 0

    while True:
        # Considera apenas candidatos ainda não descartados por palpite errado.
        ativos = {a: p for a, p in crencas.items() if a not in descartados}
        ativos = normalizar(ativos)

        topo = max(ativos, key=ativos.get)
        confianca = ativos[topo]

        # Condições de parada: confiança alta, perguntas esgotadas
        # ou sobrou apenas um candidato.
        candidatos_vivos = [a for a, p in ativos.items() if p > 1e-6]
        if (confianca >= LIMIAR_CONFIANCA
                or n_perguntas >= MAX_PERGUNTAS
                or len(candidatos_vivos) == 1):
            if arriscar_palpite(topo, confianca):
                return
            # Palpite errado: descarta e continua, se ainda houver opções.
            descartados.add(topo)
            restantes = [a for a in candidatos_vivos if a not in descartados]
            if not restantes:
                print("\nDesisto! Não consegui descobrir o seu alien. Você venceu! 🛸")
                return
            continue

        atributo = melhor_atributo(ativos, ja_perguntados)
        if atributo is None:
            # Sem perguntas úteis -> arrisca o melhor.
            if not arriscar_palpite(topo, confianca):
                print("\nDesisto! Você venceu! 🛸")
            return

        resposta = perguntar(ATRIBUTOS[atributo])
        ja_perguntados.add(atributo)
        n_perguntas += 1
        crencas = atualizar_crencas(crencas, atributo, resposta)

        # Mostra a hipótese mais provável no momento (transparência).
        atual = normalizar({a: p for a, p in crencas.items() if a not in descartados})
        lider = max(atual, key=atual.get)
        print(f"   ...hipótese atual: {lider} ({atual[lider]*100:.0f}% de confiança)")


def arriscar_palpite(alien, confianca):
    """Faz o palpite final. Retorna True se acertou."""
    print("\n" + "-" * 64)
    print(f"Acho que o seu alien é: >>> {alien} <<<  "
          f"(confiança: {confianca*100:.0f}%)")
    resposta = perguntar("Acertei?")
    if resposta == "sim":
        print("\n🎉 Eba! Acertei! Obrigado por jogar.")
        return True
    return False


# ----------------------------------------------------------------------------
# 5) MODO DE TESTE AUTOMÁTICO (experimentos)
# ----------------------------------------------------------------------------

def simular(alien_alvo, ruido=0.0, seed=None):
    """
    Simula uma partida em que um 'usuário perfeito' responde com base nas
    características reais de `alien_alvo`. Útil para os experimentos pedidos
    no enunciado (número médio de perguntas, taxa de acerto).
    Retorna (acertou: bool, n_perguntas: int, palpite_final: str).
    """
    import random
    rng = random.Random(seed)

    crencas = {a: 1.0 / len(ALIENS) for a in ALIENS}
    ja_perguntados, descartados, n = set(), set(), 0

    while True:
        ativos = normalizar({a: p for a, p in crencas.items() if a not in descartados})
        topo = max(ativos, key=ativos.get)
        vivos = [a for a, p in ativos.items() if p > 1e-6]

        if ativos[topo] >= LIMIAR_CONFIANCA or n >= MAX_PERGUNTAS or len(vivos) == 1:
            if topo == alien_alvo:
                return True, n, topo
            descartados.add(topo)
            if not [a for a in vivos if a not in descartados]:
                return False, n, topo
            continue

        atributo = melhor_atributo(ativos, ja_perguntados)
        if atributo is None:
            return (topo == alien_alvo), n, topo

        # Resposta "honesta" do alien-alvo, com chance de ruído.
        possui = atributo in ALIENS[alien_alvo]
        if rng.random() < ruido:
            resposta = "sim" if not possui else "nao"  # responde errado
        else:
            resposta = "sim" if possui else "nao"

        ja_perguntados.add(atributo)
        n += 1
        crencas = atualizar_crencas(crencas, atributo, resposta)


def rodar_experimentos(ruido=0.0):
    """Testa todos os aliens e imprime as métricas do enunciado."""
    print("=" * 64)
    print(f"   EXPERIMENTOS  (ruído nas respostas = {ruido*100:.0f}%)")
    print("=" * 64)
    acertos, total_perguntas, falhas = 0, 0, []
    for alien in ALIENS:
        ok, n, palpite = simular(alien, ruido=ruido, seed=42)
        total_perguntas += n
        if ok:
            acertos += 1
        else:
            falhas.append((alien, palpite))
        status = "OK " if ok else "X  "
        print(f"  [{status}] alvo={alien:<16} perguntas={n:<2} palpite={palpite}")

    n_aliens = len(ALIENS)
    print("-" * 64)
    print(f"Taxa de acerto:            {acertos}/{n_aliens} "
          f"({acertos/n_aliens*100:.1f}%)")
    print(f"Média de perguntas:        {total_perguntas/n_aliens:.2f}")
    if falhas:
        print("Casos de falha:")
        for alvo, palpite in falhas:
            print(f"   - alvo {alvo} -> palpite {palpite}")
    else:
        print("Casos de falha:            nenhum")


# ----------------------------------------------------------------------------
# 6) MENU PRINCIPAL
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--teste":
        rodar_experimentos(ruido=0.0)
        print()
        rodar_experimentos(ruido=0.15)
    else:
        while True:
            jogar()
            again = input("\nJogar de novo? [S/N]: ").strip().lower()
            if again not in ("s", "sim", "1"):
                print("Ate a proxima!")
                break
