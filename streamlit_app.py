import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="Agrocadena 🌱", layout="centered")

# --- CONEXIÓN A GOOGLE SHEETS ---
# Forzamos a la conexión a usar los secretos explícitamente
conn = st.connection("gsheets", type=GSheetsConnection)

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if 'logeado' not in st.session_state:
    st.session_state.logeado = False
if 'usuario_tipo' not in st.session_state:
    st.session_state.usuario_tipo = None
if 'nombre_usuario' not in st.session_state:
    st.session_state.nombre_usuario = ""

# --- 1. PANTALLA DE INICIO ---
if not st.session_state.logeado:
    st.title("🌱 Agrocadena")
    st.markdown("### Conectando el campo con la ciudad")
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab1:
        with st.form("login"):
            user = st.text_input("Nombre de Usuario")
            password = st.text_input("Contraseña", type="password")
            btn_login = st.form_submit_button("Entrar")
            
            if btn_login:
                try:
                    df_usuarios = conn.read(worksheet="Usuarios")
                    validar = df_usuarios[(df_usuarios['Nombre'] == user) & (df_usuarios['Contraseña'] == password)]
                    if not validar.empty:
                        st.session_state.logeado = True
                        st.session_state.nombre_usuario = user
                        st.session_state.usuario_tipo = validar.iloc[0]['Rol']
                        st.success(f"¡Bienvenido de nuevo, {user}!")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
                except Exception as e:
                    st.error(f"Error al leer usuarios: {e}")

    with tab2:
        st.write("### Crear cuenta")
        new_user = st.text_input("Nombre completo")
        new_tel = st.text_input("Teléfono")
        new_pass = st.text_input("Crea una Contraseña", type="password")
        new_role = st.radio("Se identifica como:", ["Campesino", "Transportador", "Negocio"])
        
        if st.button("Finalizar Registro"):
            if new_user and new_tel and new_pass:
                nuevo_row = pd.DataFrame([{
                    "Nombre": new_user, 
                    "Telefono": new_tel, 
                    "Contraseña": new_pass, 
                    "Rol": new_role
                }])
                
                try:
                    # 1. Intentamos leer la hoja Usuarios
                    # En lugar de usar conn.read, usa esto que es más directo:
                    df_existente = conn.read(worksheet="Usuarios", usecols=[0,1,2,3])
                    df_final = pd.concat([df_existente, nuevo_row], ignore_index=True)
                    
                    # 2. Intentamos guardar los datos actualizados
                    conn.update(worksheet="Usuarios", data=df_final)
                    
                    # 3. Si todo sale bien, iniciamos sesión
                    st.session_state.logeado = True
                    st.session_state.usuario_tipo = new_role
                    st.session_state.nombre_usuario = new_user
                    st.balloons()
                    st.success("¡Cuenta creada exitosamente!")
                    st.rerun()
                    
                except Exception as e:
                    # ESTO ES LO MÁS IMPORTANTE: Nos mostrará el rastro real del error
                    st.error("🚨 DETALLES DEL ERROR:")
                    st.exception(e) 
                    st.info("Revisa si el error menciona 'Permission denied' o '403'.")
            else:
                st.warning("Por favor completa todos los campos")

# --- 2. VISTAS SEGÚN PERFIL ---
else:
    st.sidebar.title(f"Hola, {st.session_state.nombre_usuario}")
    st.sidebar.write(f"Perfil: **{st.session_state.usuario_tipo}**")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logeado = False
        st.rerun()

    if st.session_state.usuario_tipo == "Campesino":
        st.title("🧑‍🌾 Panel del Productor")
        st.write("Bienvenido a tu panel de control.")
        # ... resto del código del campesino ...
