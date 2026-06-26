import streamlit as st
import json
import os

# ==========================================
# CLASSES DO SISTEMA ESPECIALISTA
# ==========================================
class Regra:
    def __init__(self, id_regra, condicoes, conclusao):
        self.id = id_regra
        self.condicoes = condicoes
        self.conclusao = conclusao

class BaseDeConhecimento:
    def __init__(self):
        self.regras = []
        self.fatos = {}
        self.hipoteses = []
        self.arquivo_padrao = "base_conhecimento.json"
        
    def adicionar_regra(self, id_regra, condicoes, conclusao):
        self.regras.append(Regra(id_regra, condicoes, conclusao))
        self.salvar_base()
        
    def atualizar_regra(self, index, id_regra, condicoes, conclusao):
        self.regras[index] = Regra(id_regra, condicoes, conclusao)
        self.salvar_base()

    def remover_regra(self, index):
        self.regras.pop(index)
        self.salvar_base()

    def adicionar_fato(self, atributo, valor):
        self.fatos[atributo] = valor
        
    def carregar_base(self):
        if os.path.exists(self.arquivo_padrao):
            with open(self.arquivo_padrao, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                self.regras = [Regra(r['id'], r['condicoes'], r['conclusao']) for r in dados.get("regras", [])]
                self.hipoteses = dados.get("hipoteses", [])
        
    def salvar_base(self):
        dados = {
            "regras": [{"id": r.id, "condicoes": r.condicoes, "conclusao": r.conclusao} for r in self.regras],
            "hipoteses": self.hipoteses
        }
        with open(self.arquivo_padrao, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)

class MotorDeInferencia:
    def __init__(self, base_conhecimento):
        self.bc = base_conhecimento
        self.como_explicacao = {} 
        self.objetivo_atual = None 

    def forward_chaining(self):
        novos_fatos_inferidos = True
        while novos_fatos_inferidos:
            novos_fatos_inferidos = False
            for regra in self.bc.regras:
                atributo_conclusao, valor_conclusao = regra.conclusao.split(" = ")
                if self.bc.fatos.get(atributo_conclusao) == valor_conclusao:
                    continue
                
                condicoes_atendidas = True
                for condicao in regra.condicoes:
                    atr, val = condicao.split(" = ")
                    if self.bc.fatos.get(atr) != val:
                        condicoes_atendidas = False
                        break
                
                if condicoes_atendidas:
                    self.bc.adicionar_fato(atributo_conclusao, valor_conclusao)
                    self.como_explicacao[regra.conclusao] = regra
                    novos_fatos_inferidos = True

    def backward_chaining(self, objetivo_str):
        atr_obj, val_obj = objetivo_str.split(" = ")
        
        if self.bc.fatos.get(atr_obj) == val_obj:
            return True
        elif self.bc.fatos.get(atr_obj) is not None:
            return False 

        para_testar = [r for r in self.bc.regras if r.conclusao == objetivo_str]
        
        for regra in para_testar:
            todas_condicoes_verdadeiras = True
            for condicao in regra.condicoes:
                atr_cond, val_cond = condicao.split(" = ")
                self.objetivo_atual = objetivo_str 
                
                if atr_cond not in self.bc.fatos:
                    regras_dependentes = [r for r in self.bc.regras if r.conclusao.startswith(atr_cond + " = ")]
                    if regras_dependentes:
                        sucesso = self.backward_chaining(condicao)
                        if not sucesso:
                            todas_condicoes_verdadeiras = False
                            break
                    else:
                        if 'pergunta_pendente' not in st.session_state:
                            st.session_state.pergunta_pendente = atr_cond
                            st.session_state.objetivo_pendente = self.objetivo_atual
                            st.rerun() 
                        else:
                            if st.session_state.pergunta_pendente == atr_cond and 'resposta_pendente' in st.session_state:
                                resp = st.session_state.resposta_pendente
                                self.bc.adicionar_fato(atr_cond, resp)
                                del st.session_state['pergunta_pendente']
                                del st.session_state['resposta_pendente']
                                if resp != val_cond:
                                    todas_condicoes_verdadeiras = False
                                    break
                            else:
                                return False 
                elif self.bc.fatos[atr_cond] != val_cond:
                    todas_condicoes_verdadeiras = False
                    break
            
            if todas_condicoes_verdadeiras:
                self.bc.adicionar_fato(atr_obj, val_obj)
                self.como_explicacao[objetivo_str] = regra
                return True
                
        return False

    def hybrid_chaining(self):
        self.forward_chaining()
        for hip in self.bc.hipoteses:
            if self.backward_chaining(hip):
                return hip
        return None

    def explicar_como(self, fato_str):
        if fato_str in self.como_explicacao:
            regra = self.como_explicacao[fato_str]
            condicoes_str = " E ".join(regra.condicoes)
            return f"Porque a regra **{regra.id}** foi ativada. Sabíamos que `{condicoes_str}`, ENTÃO concluímos que `{regra.conclusao}`."
        return "Este fato foi informado diretamente por você durante a consulta."

# ==========================================
# INTERFACE STREAMLIT
# ==========================================
def main():
    st.set_page_config(page_title="Shell Especialista", layout="wide")
    
    # Inicializa base no estado da sessão
    if 'bc' not in st.session_state:
        st.session_state.bc = BaseDeConhecimento()
        st.session_state.bc.carregar_base()
        
    st.sidebar.title("Navegação")
    menu = st.sidebar.radio("Escolha o Módulo:", ["Consulta de Diagnóstico", "Editor da Base de Conhecimento"])
    
    # ------------------------------------------
    # MÓDULO: EDITOR DA BASE DE CONHECIMENTO
    # ------------------------------------------
    if menu == "Editor da Base de Conhecimento":
        st.title("⚙️ Editor da Base de Conhecimento")
        
        tab_add, tab_edit, tab_del, tab_view = st.tabs(["➕ Adicionar", "✏️ Editar", "❌ Excluir", "📋 Visualizar Base"])
        
        # --- TAB: ADICIONAR ---
        with tab_add:
            st.subheader("Adicionar Nova Regra")
            with st.form("nova_regra"):
                r_id = st.text_input("ID da Regra (ex: R21)")
                r_cond = st.text_area("Condições (uma por linha, ex: febre = sim)")
                r_conc = st.text_input("Conclusão (ex: suspeita = gripe)")
                if st.form_submit_button("Adicionar Regra"):
                    if r_id and r_cond and r_conc:
                        conds = [c.strip() for c in r_cond.split('\n') if c.strip()]
                        st.session_state.bc.adicionar_regra(r_id, conds, r_conc)
                        st.success(f"Regra {r_id} adicionada e guardada!")
                        st.rerun()

            st.subheader("Adicionar Hipótese")
            with st.form("nova_hipotese"):
                h_str = st.text_input("Hipótese (ex: diagnostico = gripe)")
                if st.form_submit_button("Adicionar Hipótese"):
                    if h_str and h_str not in st.session_state.bc.hipoteses:
                        st.session_state.bc.hipoteses.append(h_str)
                        st.session_state.bc.salvar_base()
                        st.success("Hipótese adicionada!")
                        st.rerun()

        # --- TAB: EDITAR ---
        with tab_edit:
            st.subheader("Editar Regra Existente")
            if st.session_state.bc.regras:
                opcoes_regras = [f"{r.id} - {r.conclusao}" for r in st.session_state.bc.regras]
                regra_selecionada = st.selectbox("Selecione a Regra:", opcoes_regras)
                idx_regra = opcoes_regras.index(regra_selecionada)
                regra_atual = st.session_state.bc.regras[idx_regra]
                
                with st.form("editar_regra"):
                    novo_id = st.text_input("ID da Regra", value=regra_atual.id)
                    novas_conds = st.text_area("Condições (uma por linha)", value="\n".join(regra_atual.condicoes))
                    nova_conc = st.text_input("Conclusão", value=regra_atual.conclusao)
                    
                    if st.form_submit_button("Guardar Alterações na Regra"):
                        conds_lista = [c.strip() for c in novas_conds.split('\n') if c.strip()]
                        st.session_state.bc.atualizar_regra(idx_regra, novo_id, conds_lista, nova_conc)
                        st.success("Regra editada com sucesso!")
                        st.rerun()
            else:
                st.info("Nenhuma regra cadastrada.")

            st.markdown("---")
            st.subheader("Editar Hipótese Existente")
            if st.session_state.bc.hipoteses:
                hip_selecionada = st.selectbox("Selecione a Hipótese:", st.session_state.bc.hipoteses)
                idx_hip = st.session_state.bc.hipoteses.index(hip_selecionada)
                
                with st.form("editar_hipotese"):
                    nova_hip = st.text_input("Hipótese", value=hip_selecionada)
                    if st.form_submit_button("Guardar Alterações na Hipótese"):
                        st.session_state.bc.hipoteses[idx_hip] = nova_hip
                        st.session_state.bc.salvar_base()
                        st.success("Hipótese editada!")
                        st.rerun()

        # --- TAB: EXCLUIR ---
        with tab_del:
            st.subheader("Excluir Regra")
            if st.session_state.bc.regras:
                del_regra = st.selectbox("Selecione a Regra a apagar:", [f"{r.id} - {r.conclusao}" for r in st.session_state.bc.regras], key="del_r")
                if st.button("Apagar Regra Selecionada"):
                    idx_del_r = [f"{r.id} - {r.conclusao}" for r in st.session_state.bc.regras].index(del_regra)
                    st.session_state.bc.remover_regra(idx_del_r)
                    st.error("Regra apagada com sucesso!")
                    st.rerun()
                    
            st.markdown("---")
            st.subheader("Excluir Hipótese")
            if st.session_state.bc.hipoteses:
                del_hip = st.selectbox("Selecione a Hipótese a apagar:", st.session_state.bc.hipoteses, key="del_h")
                if st.button("Apagar Hipótese Selecionada"):
                    st.session_state.bc.hipoteses.remove(del_hip)
                    st.session_state.bc.salvar_base()
                    st.error("Hipótese apagada com sucesso!")
                    st.rerun()

        # --- TAB: VISUALIZAR ---
        with tab_view:
            st.subheader(f"Total de Regras: {len(st.session_state.bc.regras)}")
            st.json([{"id": r.id, "condicoes": r.condicoes, "conclusao": r.conclusao} for r in st.session_state.bc.regras])
            st.subheader(f"Total de Hipóteses: {len(st.session_state.bc.hipoteses)}")
            st.write(st.session_state.bc.hipoteses)

    # ------------------------------------------
    # MÓDULO: CONSULTA DE DIAGNÓSTICO
    # ------------------------------------------
    elif menu == "Consulta de Diagnóstico":
        st.title("🩺 Sistema de Diagnóstico")
        
        if 'motor' not in st.session_state:
            st.session_state.motor = MotorDeInferencia(st.session_state.bc)
            st.session_state.diagnostico_final = None
        
        if st.button("🔄 Reiniciar Consulta"):
            st.session_state.bc.fatos = {}
            st.session_state.motor = MotorDeInferencia(st.session_state.bc)
            st.session_state.diagnostico_final = None
            if 'pergunta_pendente' in st.session_state: del st.session_state['pergunta_pendente']
            if 'resposta_pendente' in st.session_state: del st.session_state['resposta_pendente']
            st.rerun()

        st.markdown("---")

        if st.session_state.diagnostico_final is None:
            resultado = st.session_state.motor.hybrid_chaining()
            
            if resultado:
                st.session_state.diagnostico_final = resultado
                st.rerun()
            elif 'pergunta_pendente' in st.session_state:
                pergunta = st.session_state.pergunta_pendente
                st.info(f"**Pergunta:** O(a) `{pergunta}` é/está 'sim' ou 'nao'?")
                
                col1, col2, col3 = st.columns(3)
                if col1.button("✅ Sim", use_container_width=True):
                    st.session_state.resposta_pendente = "sim"
                    st.rerun()
                if col2.button("❌ Não", use_container_width=True):
                    st.session_state.resposta_pendente = "nao"
                    st.rerun()
                if col3.button("🤔 Por quê?", use_container_width=True):
                    obj = st.session_state.objetivo_pendente
                    st.warning(f"**Explicação:** Estou a avaliar a hipótese `{obj}` e saber sobre `{pergunta}` é uma condição necessária para validá-la ou descartá-la.")
            else:
                st.error("Não foi possível chegar a um diagnóstico com as informações fornecidas.")
                
        else:
            st.success(f"### DIAGNÓSTICO FINAL: {st.session_state.diagnostico_final.upper()}")
            with st.expander("Como cheguei a esta conclusão?"):
                st.write(st.session_state.motor.explicar_como(st.session_state.diagnostico_final))

if __name__ == "__main__":
    main()