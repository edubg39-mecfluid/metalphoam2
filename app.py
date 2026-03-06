import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="METALPHOAM 2 - Dashboard", layout="wide")

# --- BASE DE DATOS TÉCNICA  ---
DB_METALES = {
    "Espuma de Aluminio": {"ks": 205.0, "rho": 2700},
    "Espuma de Cobre": {"ks": 401.0, "rho": 8960},
    "Espuma de Níquel": {"ks": 90.7, "rho": 8900}
}

DB_PCM = {
    "Parafina RT44": {"kf": 0.2, "rho": 800, "Tm": 44.0, "L": 170000}
}

# --- FUNCIÓN: FÓRMULA DE CALMIDI & MAHAJAN ---
def calcular_ke_ideal(kf, ks, epsilon):
    # Términos de la ecuación según el modelo de Calmidi & Mahajan
    t_sqrt = np.sqrt((1 - epsilon) / (3 * np.pi))
    t_lin = (1 - epsilon) / (3 * np.pi)
    dk = ks - kf
    
    num_a = kf + np.pi * (t_sqrt - t_lin) * dk
    num_b = kf - ((1 - epsilon) / 3) * dk
    den = kf + ((4/3) * t_sqrt * (1 - epsilon) + np.pi * t_sqrt - (1 - epsilon)) * dk
    
    return (num_a * num_b) / den

# --- MENÚ LATERAL DE CONTROL ---
with st.sidebar:
    st.header("⚙️ Configuración")
    matriz = st.selectbox("Material de la Matriz", list(DB_METALES.keys()))
    pcm = st.selectbox("Material del PCM", list(DB_PCM.keys()))
    
    st.markdown("---")
    st.subheader("📏 Geometría y Estructura")
    forma = st.radio("Forma de la probeta", ["Cilíndrica", "Prismática"])
    
    if forma == "Cilíndrica":
        d = st.number_input("Diámetro (mm)", value=25.0)
        l = st.number_input("Espesor (mm)", value=40.0)
        vol = (np.pi * (d/2)**2 * l) / 1000  # cm3
    else:
        an = st.number_input("Ancho (mm)", value=20.0)
        l = st.number_input("Espesor (mm)", value=40.0)
        vol = (an * an * l) / 1000  # cm3
        
    epsilon = st.slider("Porosidad (ε)", 0.80, 0.98, 0.93)
    ppi = st.number_input("Densidad de Poros (PPI)", value=10)

# --- PANEL PRINCIPAL ---
st.title("🌡️ METALPHOAM 2: Sistema de Gestión e Informes")
st.write(f"Análisis del compuesto: **{matriz}** + **{pcm}**")

# Cálculo automático de ke y masa de PCM
ke_ideal = calcular_ke_ideal(DB_PCM[pcm]["kf"], DB_METALES[matriz]["ks"], epsilon)
masa_pcm = vol * epsilon * (DB_PCM[pcm]["rho"] / 1000)

# Pestañas para organizar el contenido
tab1, tab2, tab3 = st.tabs(["📝 Ficha de Muestra", "📊 Análisis Térmico", "📄 Informe Final"])

with tab1:
    st.subheader("Caracterización Teórica")
    c1, c2, c3 = st.columns(3)
    c1.metric("Conductividad Ideal ($k_e$)", f"{ke_ideal:.4f} W/m·K")
    c2.metric("Masa PCM Estimada", f"{masa_pcm:.2f} g")
    c3.metric("Porosidad Seleccionada", f"{epsilon*100}%")
    
    st.info("El sistema aplica el modelo de Calmidi & Mahajan para la conductividad térmica efectiva.")
    

with tab2:
    st.subheader("Carga y Comparativa de Datos")
    file = st.file_uploader("Sube el archivo CSV con datos de termopares", type="csv")
    if file:
        df = pd.read_csv(file)
        st.line_chart(df.set_index(df.columns[0]))
        st.success("Datos cargados correctamente.")

with tab3:
    st.subheader("Resumen para el Informe del TFG")
    informe = f"""
    ### REPORTE DE CARACTERIZACIÓN - METALPHOAM 2
    
    **Muestra:** {matriz} impregnada con {pcm}.
    **Geometría:** {forma} ({l}mm de espesor).
    **Porosidad (ε):** {epsilon*100}%.
    **Densidad de poros:** {ppi} PPI.
    
    **RESULTADOS TEÓRICOS:**
    - Conductividad Efectiva ($k_{{eff}}$): {ke_ideal:.4f} W/m·K.
    - Masa de PCM teórica en la matriz: {masa_pcm:.2f} g.
    """
    st.markdown(informe)
    st.text_area("Copia este resumen para tu Word:", informe.replace("### ", ""), height=200)
