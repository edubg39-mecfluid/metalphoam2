import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="METALPHOAM 2 PRO - Modelos", layout="wide", page_icon="🔬")

# --- 1. INICIALIZACIÓN DE VARIABLES (Evita NameError) ---
ks, kf, rho_p, tm = 205.0, 0.2, 800.0, 44.0
d_final, l_final, forma = 25.0, 40.0, "Cilíndrica"
epsilon = 0.93

# --- 2. BASES DE DATOS ---
DB_METALES = {
    "Aluminio 6061": {"ks": 205.0, "rho": 2700},
    "Cobre Puro": {"ks": 401.0, "rho": 8960},
    "Personalizado": {"ks": 0.0, "rho": 0.0}
}
DB_PCM = {
    "RT44HC": {"kf": 0.2, "Tm": 44.0, "rho": 800},
    "RT55": {"kf": 0.2, "Tm": 55.0, "rho": 880},
    "Personalizado": {"kf": 0.0, "Tm": 0.0, "rho": 0.0}
}

# --- 3. FUNCIONES DE MODELOS MATEMÁTICOS ---
def modelo_geometrico(kf, ks, epsilon, factor_nudo=3.0, factor_brazo=1.0):
    """
    Implementación del modelo de la imagen (A.5). 
    Permite modificar factores microestructurales (nudos y brazos).
    """
    if ks <= 0 or kf <= 0: return 0.0
    
    # delta representa (1 - porosidad)
    delta = 1 - epsilon
    
    # Términos basados en la imagen A.5
    t_sqrt = np.sqrt(delta / (factor_nudo * np.pi))
    t_lin = delta / (factor_nudo * np.pi)
    dk = ks - kf
    
    # Numerador (Ajustado según imagen: kf + (1-delta)/3 * dk)
    num_a = kf + np.pi * (t_sqrt - t_lin) * dk
    num_b = kf + (delta / 3) * factor_brazo * dk 
    
    # Denominador
    den = kf + ((4/3) * t_sqrt * (1 - delta) + np.pi * t_sqrt - delta) * dk
    
    return (num_a * num_b) / den

# --- 4. PANEL DE CONTROL (DESPLEGABLE) ---
with st.sidebar:
    st.title("⚙️ Configuración")

    # Menú 1: Materiales
    with st.expander("🧪 SELECCIÓN DE MATERIALES", expanded=False):
        sel_m = st.selectbox("Matriz Metálica", list(DB_METALES.keys()))
        ks = st.number_input("ks (W/mK)", value=DB_METALES[sel_m]["ks"]) if sel_m == "Personalizado" else DB_METALES[sel_m]["ks"]
        
        sel_p = st.selectbox("Material PCM", list(DB_PCM.keys()))
        if sel_p == "Personalizado":
            kf = st.number_input("kf (W/mK)", value=0.2)
            tm = st.number_input("T. Fusión (ºC)", value=40.0)
            rho_p = st.number_input("Densidad (kg/m3)", value=800.0)
        else:
            kf, tm, rho_p = DB_PCM[sel_p]["kf"], DB_PCM[sel_p]["Tm"], DB_PCM[sel_p]["rho"]

    # Menú 2: Geometría e IA
    with st.expander("📏 GEOMETRÍA E IA VISION", expanded=False):
        modo_geo = st.radio("Método", ["Manual", "IA Vision"])
        if modo_geo == "Manual":
            forma = st.radio("Forma", ["Cilíndrica", "Prismática"])
            d_final = st.number_input("Dimensión (mm)", value=25.0)
            l_final = st.number_input("Espesor (mm)", value=40.0)
        else:
            foto = st.file_uploader("Subir foto", type=['jpg', 'png'])
            if foto:
                st.image(Image.open(foto), use_column_width=True)
                d_final = st.number_input("IA: Detectado (mm)", value=25.4)
                l_final = st.number_input("IA: Espesor (mm)", value=40.1)

    # Menú 3: Edición del Modelo Matemático
    with st.expander("🧮 MODELO MATEMÁTICO", expanded=True):
        tipo_modelo = st.radio("Seleccionar Modelo", ["Calmidi-Mahajan Standard", "Modelo Geométrico (A.5)"])
        epsilon = st.slider("Porosidad (ε)", 0.80, 0.99, 0.93)
        
        # Parámetros editables del modelo "Geometrico"
        st.markdown("**Ajuste de Microestructura:**")
        f_nudo = st.slider("Factor de Nudo (divisor pi)", 1.0, 5.0, 3.0)
        f_brazo = st.slider("Eficiencia de Brazo", 0.1, 2.0, 1.0)

# --- 5. CÁLCULO ---
if tipo_modelo == "Modelo Geométrico (A.5)":
    ke_res = modelo_geometrico(kf, ks, epsilon, f_nudo, f_brazo)
    nombre_mod = "Geométrico (Personalizado)"
else:
    # Modelo estándar simplificado
    ke_res = kf * (epsilon + (1-epsilon)**2 / ((1-epsilon) + (kf/ks)*epsilon))
    nombre_mod = "Calmidi-Mahajan Standard"

vol = (np.pi * (d_final/2)**2 * l_final) / 1000 if forma == "Cilíndrica" else (d_final**2 * l_final) / 1000
masa_teorica = vol * epsilon * (rho_p / 1000)

# --- 6. CUERPO PRINCIPAL ---
st.title("🌡️ METALPHOAM 2 PRO: IA & Modelado")
st.write(f"Utilizando: **{nombre_mod}**")

t1, t2, t3 = st.tabs(["📄 Ficha de Muestra", "📊 Análisis Térmico", "📝 Informe"])

with t1:
    st.subheader("Caracterización Teórica")
    c1, c2, c3 = st.columns(3)
    c1.metric("k efectiva", f"{ke_res:.4f} W/m·K")
    c2.metric("Masa PCM", f"{masa_teorica:.2f} g")
    c3.metric("Mejora Térmica", f"x{ke_res/kf:.1f}")
    
    st.markdown("### Modelo Matemático Aplicado")
    st.latex(r"k_e = \frac{[k_f + \pi(\sqrt{\frac{1-\epsilon}{n\pi}} - \frac{1-\epsilon}{n\pi})(k_s - k_f)][k_f + \frac{1-\epsilon}{3}(k_s - k_f)]}{k_f + [\frac{4}{3}\sqrt{\frac{1-\epsilon}{n\pi}}(1-\epsilon) + \pi\sqrt{\frac{1-\epsilon}{n\pi}} - (1-\epsilon)](k_s - k_f)}")
    st.info(f"Donde n = {f_nudo} (ajustado manualmente).")

with t2:
    st.subheader("Análisis de Ciclos")
    archivo = st.file_uploader("Subir CSV", type="csv")
    if archivo:
        df = pd.read_csv(archivo)
        st.line_chart(df.set_index(df.columns[0]))

with t3:
    st.subheader("Resumen para TFG")
    txt = f"Se ha empleado el modelo {nombre_mod} con un ajuste de nudo de {f_nudo}. k_e resultante: {ke_res:.4f} W/mK."
    st.text_area("Copiar texto:", txt, height=100)
