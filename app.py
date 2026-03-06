import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="METALPHOAM 2 PRO - Dashboard", layout="wide", page_icon="🔬")

# --- BASE DE DATOS EXTENDIDA DE METALES ---
DB_METALES = {
    "Aluminio 6061": {"ks": 205.0, "rho": 2700, "cp": 900},
    "Aluminio 1050": {"ks": 229.0, "rho": 2700, "cp": 900},
    "Cobre Puro": {"ks": 401.0, "rho": 8960, "cp": 385},
    "Níquel": {"ks": 90.7, "rho": 8900, "cp": 444},
    "Acero Inoxidable 304": {"ks": 16.2, "rho": 8000, "cp": 500},
    "Titanio (Grado 2)": {"ks": 16.4, "rho": 4500, "cp": 520},
    "Personalizado (Manual)": {"ks": 0.0, "rho": 0.0, "cp": 0.0}
}

# --- BASE DE DATOS EXTENDIDA DE PCMs (Rubitherm y otros) ---
DB_PCM = {
    "RT22HC (Bio-based)": {"kf": 0.2, "rho_s": 800, "Tm": 22.0, "L": 190000},
    "RT27 (Parafina)": {"kf": 0.2, "rho_s": 870, "Tm": 27.0, "L": 184000},
    "RT35HC (Bio-based)": {"kf": 0.2, "rho_s": 820, "Tm": 35.0, "L": 240000},
    "RT44HC (Alta Capacidad)": {"kf": 0.2, "rho_s": 800, "Tm": 44.0, "L": 250000},
    "RT55 (Parafina)": {"kf": 0.2, "rho_s": 880, "Tm": 55.0, "L": 170000},
    "RT64HC (Parafina)": {"kf": 0.2, "rho_s": 800, "Tm": 64.0, "L": 230000},
    "Ácido Láurico": {"kf": 0.15, "rho_s": 940, "Tm": 43.0, "L": 178000},
    "Personalizado (Manual)": {"kf": 0.0, "rho_s": 0.0, "Tm": 0.0, "L": 0.0}
}

# --- FÓRMULA DE CALMIDI & MAHAJAN (CORREGIDA) ---
def calcular_ke_ideal(kf, ks, epsilon):
    if ks <= 0 or kf <= 0: return 0.0
    t_sqrt = np.sqrt((1 - epsilon) / (3 * np.pi))
    t_lin = (1 - epsilon) / (3 * np.pi)
    dk = ks - kf
    num_a = kf + np.pi * (t_sqrt - t_lin) * dk
    num_b = kf + ((1 - epsilon) / 3) * dk 
    den = kf + ((4/3) * t_sqrt * (1 - epsilon) + np.pi * t_sqrt - (1 - epsilon)) * dk
    return abs((num_a * num_b) / den)

# --- PANEL DE CONTROL LATERAL ---
with st.sidebar:
    st.header("🔬 Configuración de Materiales")
    
    # Selección de Metal
    sel_metal = st.selectbox("Seleccione la Matriz Metálica", list(DB_METALES.keys()))
    if sel_metal == "Personalizado (Manual)":
        ks = st.number_input("ks personalizada (W/mK)", value=100.0)
        rho_m = st.number_input("Densidad metal (kg/m3)", value=2700.0)
    else:
        ks = DB_METALES[sel_metal]["ks"]
        rho_m = DB_METALES[sel_metal]["rho"]

    # Selección de PCM
    sel_pcm = st.selectbox("Seleccione el PCM", list(DB_PCM.keys()))
    if sel_pcm == "Personalizado (Manual)":
        kf = st.number_input("kf personalizada (W/mK)", value=0.2)
        tm = st.number_input("Punto fusión (ºC)", value=40.0)
        latent = st.number_input("Calor Latente (J/kg)", value=200000)
        rho_p = st.number_input("Densidad PCM (kg/m3)", value=800.0)
    else:
        kf = DB_PCM[sel_pcm]["kf"]
        tm = DB_PCM[sel_pcm]["Tm"]
        latent = DB_PCM[sel_pcm]["L"]
        rho_p = DB_PCM[sel_pcm]["rho_s"]

    st.markdown("---")
    st.header("📏 Geometría")
    forma = st.radio("Forma", ["Cilíndrica", "Prismática"])
    if forma == "Cilíndrica":
        d = st.number_input("Diámetro (mm)", value=25.0)
        l = st.number_input("Espesor (mm)", value=40.0)
        vol = (np.pi * (d/2)**2 * l) / 1000
    else:
        ancho = st.number_input("Ancho (mm)", value=20.0)
        l = st.number_input("Espesor (mm)", value=40.0)
        vol = (ancho * ancho * l) / 1000

    epsilon = st.slider("Porosidad (ε)", 0.80, 0.99, 0.93, 0.01)

# --- CÁLCULOS ---
ke_res = calcular_ke_ideal(kf, ks, epsilon)
masa_teorica = vol * epsilon * (rho_p / 1000)

# --- INTERFAZ PRINCIPAL ---
st.title("🌡️ METALPHOAM 2 PRO: Suite Multi-Material")
st.write(f"Estudio compuesto: **{sel_metal}** + **{sel_pcm}**")

t1, t2, t3 = st.tabs(["📋 Ficha Técnica", "📈 Datos Experimentales", "📄 Resumen para TFG"])

with t1:
    st.subheader("Propiedades del Compuesto")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("k efectiva", f"{ke_res:.3f} W/m·K")
    c2.metric("Punto Fusión", f"{tm} ºC")
    c3.metric("Masa PCM", f"{masa_teorica:.2f} g")
    c4.metric("Mejora térmica", f"x{ke_res/kf:.1f}")

    st.markdown("---")
    st.write("### Detalles de los Componentes")
    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"**Matriz:** {sel_metal}\n- k: {ks} W/mK\n- ρ: {rho_m} kg/m³")
    with col_b:
        st.success(f"**PCM:** {sel_pcm}\n- k: {kf} W/mK\n- Calor Latente: {latent/1000:.1f} kJ/kg")

with t2:
    st.subheader("Análisis de Datos")
    f = st.file_uploader("Subir CSV de termopares", type="csv")
    if f:
        df = pd.read_csv(f)
        st.line_chart(df.set_index(df.columns[0]))

with t3:
    st.subheader("Generador de Texto para Word")
    txt = f"""
    MATERIALES Y MÉTODOS:
    Se ha empleado una matriz de {sel_metal} con una porosidad de {epsilon*100}%. 
    Como material de cambio de fase (PCM) se ha utilizado {sel_pcm}, con un punto de fusión de {tm}ºC 
    y una entalpía de fusión de {latent/1000} kJ/kg. 
    
    La conductividad térmica efectiva calculada mediante el modelo de Calmidi & Mahajan es de {ke_res:.4f} W/m·K, 
    lo que supone un incremento de {ke_res/kf:.1f} veces respecto a la conductividad del PCM puro ({kf} W/m·K).
    """
    st.text_area("Copiar contenido:", txt, height=200)
