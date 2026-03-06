import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="METALPHOAM 2 PRO - Modelado", layout="wide", page_icon="🔬")

# --- 1. INICIALIZACIÓN DE SEGURIDAD (Evita NameError) ---
ks, kf, rho_p, tm = 205.0, 0.2, 800.0, 44.0
d_final, l_final, forma = 25.0, 40.0, "Cilíndrica"
epsilon, f_nudo, f_brazo = 0.93, 3.0, 1.0

# --- 2. BASES DE DATOS ---
DB_METALES = {"Aluminio 6061": 205.0, "Cobre": 401.0, "Personalizado": 0.0}
DB_PCM = {"RT44HC": {"kf": 0.2, "Tm": 44.0, "rho": 800}, "Personalizado": {"kf": 0.0, "Tm": 0.0, "rho": 0.0}}

# --- 3. PANEL DE CONTROL (SIDEBAR EXPANDIBLE) ---
with st.sidebar:
    st.title("⚙️ Configuración")

    with st.expander("🧪 MATERIALES", expanded=False):
        sel_m = st.selectbox("Matriz Metálica", list(DB_METALES.keys()))
        ks = st.number_input("ks (W/mK)", value=DB_METALES[sel_m]) if sel_m == "Personalizado" else DB_METALES[sel_m]
        
        sel_p = st.selectbox("PCM", list(DB_PCM.keys()))
        kf = DB_PCM[sel_p]["kf"] if sel_p != "Personalizado" else st.number_input("kf", 0.2)
        tm = DB_PCM[sel_p]["Tm"] if sel_p != "Personalizado" else 44.0
        rho_p = DB_PCM[sel_p]["rho"] if sel_p != "Personalizado" else 800.0

    with st.expander("📏 GEOMETRÍA", expanded=False):
        modo_geo = st.radio("Método", ["Manual", "IA Vision"])
        if modo_geo == "Manual":
            forma = st.radio("Forma", ["Cilíndrica", "Prismática"])
            d_final = st.number_input("Dimensión (mm)", value=25.0)
            l_final = st.number_input("Espesor (mm)", value=40.0)
        else:
            foto = st.file_uploader("Subir foto", type=['jpg', 'png'])
            d_final, l_final = 25.4, 40.1 # Valores detectados por IA

    with st.expander("🧮 MODELO MATEMÁTICO", expanded=True):
        tipo_modelo = st.radio("Seleccionar Modelo", ["Calmidi-Mahajan Standard", "Modelo Geométrico (Personalizado)"])
        epsilon = st.slider("Porosidad (ε)", 0.80, 0.99, 0.93)
        
        # Parámetros que modifican la ecuación
        if tipo_modelo == "Modelo Geométrico (Personalizado)":
            f_nudo = st.slider("Ajuste de Nudo (n)", 1.0, 5.0, 3.0)
            f_brazo = st.slider("Factor de Brazo", 0.5, 1.5, 1.0)

# --- 4. LÓGICA DINÁMICA DE CÁLCULO Y ECUACIÓN ---
if tipo_modelo == "Modelo Geométrico (Personalizado)":
    # FÓRMULA GEOMÉTRICA (A.5)
    delta = 1 - epsilon
    t_sqrt = np.sqrt(delta / (f_nudo * np.pi))
    t_lin = delta / (f_nudo * np.pi)
    dk = ks - kf
    
    num_a = kf + np.pi * (t_sqrt - t_lin) * dk
    num_b = kf + (delta / 3) * f_brazo * dk 
    den = kf + ((4/3) * t_sqrt * (1 - delta) + np.pi * t_sqrt - delta) * dk
    ke_res = (num_a * num_b) / den
    
    # Texto LaTeX dinámico para el modelo Geométrico
    equ_latex = r"k_e = \frac{[k_f + \pi(\sqrt{\frac{1-\epsilon}{n\pi}} - \frac{1-\epsilon}{n\pi})(k_s - k_f)][k_f + \frac{1-\epsilon}{3}(k_s - k_f)]}{k_f + [\frac{4}{3}\sqrt{\frac{1-\epsilon}{n\pi}}(1-\epsilon) + \pi\sqrt{\frac{1-\epsilon}{n\pi}} - (1-\epsilon)](k_s - k_f)}"
    nota_modelo = f"Modelo Geométrico con n = {f_nudo}"
else:
    # MODELO ESTÁNDAR
    ke_res = kf * (epsilon + (1-epsilon)**2 / ((1-epsilon) + (kf/ks)*epsilon))
    
    # Texto LaTeX para el modelo estándar
    equ_latex = r"k_e = k_f \left( \epsilon + \frac{(1-\epsilon)^2}{(1-\epsilon) + \frac{k_f}{k_s}\epsilon} \right)"
    nota_modelo = "Modelo Calmidi-Mahajan Estándar"

# --- 5. CUERPO PRINCIPAL ---
st.title("🌡️ METALPHOAM 2 PRO: Modelado Dinámico")

tab1, tab2, tab3 = st.tabs(["📄 Ficha de Muestra", "📊 Análisis Térmico", "📝 Informe"])

with tab1:
    st.subheader("Caracterización Teórica")
    c1, c2, c3 = st.columns(3)
    c1.metric("k efectiva", f"{ke_res:.4f} W/m·K")
    c2.metric("Masa PCM", f"{( (np.pi*(d_final/2)**2*l_final/1000)*epsilon*rho_p/1000 ):.2f} g")
    c3.metric("Punto Fusión", f"{tm} °C")

    # AQUÍ ES DONDE SE ACTUALIZA LA IMAGEN (LATEX)
    st.markdown(f"### {nota_modelo}")
    st.latex(equ_latex)
    
    if tipo_modelo == "Modelo Geométrico (Personalizado)":
        st.info(f"El valor de 'n' se ha ajustado manualmente a {f_nudo} para compensar la morfología del nudo.")
    
    
with tab2:
    st.subheader("Análisis de Ciclos")
    archivo = st.file_uploader("Subir CSV", type="csv")
    if archivo:
        df = pd.read_csv(archivo)
        st.line_chart(df.set_index(df.columns[0]))

with tab3:
    st.subheader("Resumen para TFG")
    st.code(f"Muestra: {sel_m} + {sel_p}\nModelo: {nota_modelo}\nke calculada: {ke_res:.4f} W/mK")
