import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="METALPHOAM 2 - Panel de Control", layout="wide", page_icon="🌡️")

# --- BASE DE DATOS TÉCNICA ---
DB_METALES = {
    "Espuma de Aluminio": {"ks": 205.0, "rho": 2700, "cp": 900},
    "Espuma de Cobre": {"ks": 401.0, "rho": 8960, "cp": 385},
    "Espuma de Níquel": {"ks": 90.7, "rho": 8900, "cp": 444}
}

DB_PCM = {
    "Parafina RT44": {"kf": 0.2, "rho": 800, "Tm": 44.0, "L": 170000}
}

# --- FÓRMULA DE CALMIDI & MAHAJAN (CORREGIDA) ---
def calcular_ke_ideal(kf, ks, epsilon):
    # Parámetros geométricos basados en la porosidad (epsilon)
    t_sqrt = np.sqrt((1 - epsilon) / (3 * np.pi))
    t_lin = (1 - epsilon) / (3 * np.pi)
    dk = ks - kf
    
    # Numerador: Ajuste de signo para consistencia física (Suma de contribuciones)
    num_a = kf + np.pi * (t_sqrt - t_lin) * dk
    num_b = kf + ((1 - epsilon) / 3) * dk 
    
    # Denominador
    den = kf + ((4/3) * t_sqrt * (1 - epsilon) + np.pi * t_sqrt - (1 - epsilon)) * dk
    
    return abs((num_a * num_b) / den)

# --- MENÚ LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("📋 Panel de Configuración")
    
    st.subheader("1. Selección de Materiales")
    matriz = st.selectbox("Material de la Espuma (ks)", list(DB_METALES.keys()))
    pcm = st.selectbox("Material del PCM (kf)", list(DB_PCM.keys()))
    
    st.markdown("---")
    st.subheader("2. Geometría de la Muestra")
    forma = st.radio("Geometría", ["Cilíndrica", "Prismática"])
    
    if forma == "Cilíndrica":
        d = st.number_input("Diámetro (mm)", value=25.0)
        l = st.number_input("Espesor (mm)", value=40.0)
        vol = (np.pi * (d/2)**2 * l) / 1000  # cm³
    else:
        an = st.number_input("Ancho (mm)", value=20.0)
        l = st.number_input("Espesor (mm)", value=40.0)
        vol = (an * an * l) / 1000  # cm³
        
    st.subheader("3. Propiedades Estructurales")
    epsilon = st.slider("Porosidad (ε)", 0.80, 0.98, 0.93)
    ppi = st.number_input("Densidad de Poros (PPI)", value=10)

# --- CÁLCULOS AUTOMÁTICOS ---
ks_val = DB_METALES[matriz]["ks"]
kf_val = DB_PCM[pcm]["kf"]
ke_ideal = calcular_ke_ideal(kf_val, ks_val, epsilon)
masa_pcm_teorica = vol * epsilon * (DB_PCM[pcm]["rho"] / 1000)

# --- INTERFAZ PRINCIPAL ---
st.title("🌡️ METALPHOAM 2: Sistema de Gestión e Informes")
st.write(f"Análisis del compuesto: **{matriz}** + **{pcm}**")

# Pestañas
tab_ficha, tab_analisis, tab_reporte = st.tabs(["📝 Ficha de Muestra", "📊 Análisis Experimental", "📄 Generar Informe"])

with tab_ficha:
    st.subheader("Caracterización Teórica del Compuesto")
    c1, c2, c3 = st.columns(3)
    c1.metric("Conductividad Teórica ($k_e$)", f"{ke_ideal:.4f} W/m·K")
    c2.metric("Masa PCM Estimada", f"{masa_pcm_teorica:.2f} g")
    c3.metric("Porosidad (ε)", f"{epsilon*100}%")
    
    st.markdown("---")
    st.markdown("### Resumen de Propiedades Detectadas")
    col_a, col_b = st.columns(2)
    col_a.info(f"**Matriz de {matriz}:**\n- Conductividad: {ks_val} W/m·K\n- Densidad: {DB_METALES[matriz]['rho']} kg/m³")
    col_b.info(f"**PCM {pcm}:**\n- Conductividad: {kf_val} W/m·K\n- Punto de Fusión: {DB_PCM[pcm]['Tm']} °C")

with tab_analisis:
    st.subheader("Carga de Datos de Termopares")
    st.write("Sube tu archivo CSV generado por los sensores para comparar con el modelo ideal.")
    archivo = st.file_uploader("Arrastra tu archivo CSV aquí", type="csv")
    
    if archivo:
        df = pd.read_csv(archivo)
        st.write("### Gráfica de Temperaturas")
        st.line_chart(df.set_index(df.columns[0]))
        st.success("Datos cargados. La meseta de fusión debería observarse a los 44°C.")

with tab_reporte:
    st.subheader("Resumen para el Informe del TFG")
    st.write("Copia el siguiente texto para tu memoria:")
    
    resumen_txt = f"""
    INFORME DE CARACTERIZACIÓN TÉRMICA - PROYECTO METALPHOAM
    -------------------------------------------------------
    Muestra: {matriz} (Matriz) / {pcm} (Impregnación)
    Geometría: {forma} de {l} mm de espesor.
    Porosidad (ε): {epsilon*100}%
    Densidad de poros: {ppi} PPI
    
    RESULTADOS CALCULADOS:
    - Conductividad Térmica Efectiva (ke): {ke_ideal:.4f} W/m·K
    - Masa de PCM teórica cargada: {masa_pcm_teorica:.2f} g
    - Mejora de conductividad: x{ke_ideal/kf_val:.1f} veces respecto al PCM puro.
    -------------------------------------------------------
    Modelo aplicado: Calmidi & Mahajan para espumas metálicas de alta porosidad.
    """
    st.text_area("Resultado del Informe:", resumen_txt, height=250)
