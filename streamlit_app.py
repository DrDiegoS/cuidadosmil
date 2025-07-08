
import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Autenticação com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope,
)
client = gspread.authorize(creds)

# URL da planilha do usuário
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1WJqod7rmn1aO20UyRulnC-XyUUdujPoICWwcbuX4BKc"
spreadsheet = client.open_by_url(spreadsheet_url)
worksheet = spreadsheet.sheet1

# Carregar dados da planilha
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# Corrigir nomes duplicados de status
df["Status"] = df["Status"].replace({"Não Iniciado": "Não iniciado"})

# Interface Streamlit
st.title("📊 Acompanhamento das Linhas de Cuidado")

# Filtros
col1, col2, col3 = st.columns(3)
with col1:
    filtro_linha = st.selectbox("🔍 Filtrar por Linha de Cuidado", ["Todas"] + sorted(df["Linha de Cuidado"].unique()))
with col2:
    filtro_fase = st.selectbox("📌 Filtrar por Fase", ["Todas"] + sorted(df["Fase"].unique()))
with col3:
    filtro_status = st.selectbox("⏱️ Filtrar por Status", ["Todos"] + sorted(df["Status"].unique()))

df_filtrado = df.copy()
if filtro_linha != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Linha de Cuidado"] == filtro_linha]
if filtro_fase != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Fase"] == filtro_fase]
if filtro_status != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Status"] == filtro_status]

# Seção: 📋 Tarefas Filtradas
st.subheader("📋 Tarefas Filtradas")

def cor_status(status):
    if status == "Concluído":
        return "background-color: #d4edda"
    elif status == "Em andamento":
        return "background-color: #fff3cd"
    elif status == "Ação contínua":
        return "background-color: #cce5ff"
    else:
        return "background-color: #f8d7da"

styled_df = df_filtrado.style.applymap(cor_status, subset=["Status"])
st.dataframe(styled_df, use_container_width=True)

# Seção: ✏️ Atualizar Status e Observações
st.subheader("✏️ Atualizar Status e Observações")
linha_edit = st.selectbox("Linha de Cuidado", sorted(df["Linha de Cuidado"].unique()), key="linha_edit")
fase_edit = st.selectbox("Fase", sorted(df[df["Linha de Cuidado"] == linha_edit]["Fase"].unique()), key="fase_edit")
tarefas_disponiveis = df[(df["Linha de Cuidado"] == linha_edit) & (df["Fase"] == fase_edit)]["Tarefa"].unique()
tarefa_edit = st.selectbox("Tarefa", sorted(tarefas_disponiveis), key="tarefa_edit")
status_edit = st.selectbox("Novo Status", ["Não iniciado", "Em andamento", "Concluído", "Ação contínua"], key="status_edit")
obs_edit = st.text_area("Observações", key="obs_edit")

if st.button("Salvar Alterações"):
    idx = df[(df["Linha de Cuidado"] == linha_edit) & (df["Fase"] == fase_edit) & (df["Tarefa"] == tarefa_edit)].index
    if not idx.empty:
        df.at[idx[0], "Status"] = status_edit
        df.at[idx[0], "Observações"] = obs_edit
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.success("Alterações salvas com sucesso!")

# Gráficos
st.subheader("📈 Progresso")

df["Concluído?"] = df["Status"].isin(["Concluído", "Ação contínua"])
progresso_total = df.groupby("Linha de Cuidado")["Concluído?"].mean().reset_index()
progresso_total["% Concluído"] = (progresso_total["Concluído?"] * 100).round(1)

fig = px.bar(progresso_total, x="Linha de Cuidado", y="% Concluído", title="Progresso por Linha de Cuidado")
st.plotly_chart(fig, use_container_width=True)

# Pizza com proporção por status
st.subheader("🥧 Distribuição de Status")
status_contagem = df[df["Status"] != "Ação contínua"]["Status"].value_counts().reset_index()
status_contagem.columns = ["Status", "Contagem"]
fig2 = px.pie(status_contagem, names="Status", values="Contagem", title="Distribuição das Tarefas por Status")
st.plotly_chart(fig2, use_container_width=True)
