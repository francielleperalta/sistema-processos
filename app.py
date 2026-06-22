import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import smtplib

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema Empresarial", layout="wide")

# =========================
# BANCO
# =========================
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS dados (
    id INTEGER PRIMARY KEY,
    processo TEXT,
    interessado TEXT,
    assunto TEXT,
    data TEXT,
    situacao TEXT,
    prazo TEXT,
    email TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    usuario TEXT,
    senha TEXT,
    perfil TEXT,
    email TEXT
)
""")

conn.commit()

# usuário padrão
cursor.execute("SELECT * FROM usuarios")
if not cursor.fetchall():
    cursor.execute("INSERT INTO usuarios VALUES ('admin','1234','admin','seuemail@outlook.com')")
    conn.commit()

# =========================
# LOGIN
# =========================
st.sidebar.title("🔐 Login")

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    user = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")

    if st.sidebar.button("Entrar"):
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (user, senha))
        resultado = cursor.fetchone()

        if resultado:
            st.session_state["logado"] = True
            st.session_state["perfil"] = resultado[2]
            st.session_state["email"] = resultado[3]
        else:
            st.error("Login inválido")
    st.stop()

# =========================
# MENU
# =========================
menu = st.sidebar.selectbox("Menu", ["Inserir", "Pesquisar", "Editar", "Dashboard", "Usuários"])

# =========================
# ALERTA DE PRAZO
# =========================
def alerta_prazo():
    df = pd.read_sql("SELECT * FROM dados", conn)
    hoje = datetime.today()

    for _, row in df.iterrows():
        if row["prazo"]:
            prazo = datetime.strptime(row["prazo"], "%Y-%m-%d")
            if prazo <= hoje + timedelta(days=2):
                st.warning(f"⚠️ Processo {row['processo']} vence em breve!")

alerta_prazo()

# =========================
# INSERIR
# =========================
if menu == "Inserir":
    st.title("➕ Novo Registro")

    processo = st.text_input("Processo")
    interessado = st.text_input("Interessado")
    assunto = st.text_input("Assunto")
    data = st.date_input("Data")
    situacao = st.selectbox("Situação", ["Pendente", "Em andamento", "Concluído"])
    prazo = st.date_input("Prazo")
    email = st.text_input("E-mail responsável")

    if st.button("Salvar"):
        cursor.execute("""
        INSERT INTO dados (processo, interessado, assunto, data, situacao, prazo, email)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (processo, interessado, assunto, str(data), situacao, str(prazo), email))

        conn.commit()
        st.success("✅ Salvo!")

# =========================
# PESQUISA
# =========================
elif menu == "Pesquisar":
    st.title("🔎 Buscar Processo")

    busca = st.text_input("Digite qualquer informação")

    df = pd.read_sql("SELECT * FROM dados", conn)

    if busca:
        df = df[
            df["processo"].str.contains(busca, case=False, na=False) |
            df["interessado"].str.contains(busca, case=False, na=False) |
            df["assunto"].str.contains(busca, case=False, na=False)
        ]

    st.dataframe(df, use_container_width=True)

# =========================
# EDITAR / EXCLUIR
# =========================
elif menu == "Editar":
    st.title("✏️ Editar / Excluir")

    df = pd.read_sql("SELECT * FROM dados", conn)
    st.dataframe(df)

    id_registro = st.number_input("ID", step=1)

    if st.session_state["perfil"] == "admin":
        if st.button("Excluir"):
            cursor.execute("DELETE FROM dados WHERE id=?", (id_registro,))
            conn.commit()
            st.success("Excluído!")

    novo_status = st.selectbox("Novo status", ["Pendente", "Em andamento", "Concluído"])

    if st.button("Atualizar"):
        cursor.execute("UPDATE dados SET situacao=? WHERE id=?", (novo_status, id_registro))
        conn.commit()
        st.success("Atualizado!")

# =========================
# DASHBOARD
# =========================
elif menu == "Dashboard":
    st.title("📊 Dashboard")

    df = pd.read_sql("SELECT * FROM dados", conn)

    st.metric("Total de registros", len(df))
    st.bar_chart(df["situacao"].value_counts())

# =========================
# USUÁRIOS
# =========================
elif menu == "Usuários":
    st.title("👤 Cadastro de usuários")

    if st.session_state["perfil"] == "admin":
        user = st.text_input("Usuário")
        senha = st.text_input("Senha")
        perfil = st.selectbox("Perfil", ["admin", "user"])
        email = st.text_input("Email")

        if st.button("Cadastrar"):
            cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", (user, senha, perfil, email))
            conn.commit()
            st.success("Usuário criado!")
    else:
        st.warning("Apenas admin pode cadastrar usuários")
