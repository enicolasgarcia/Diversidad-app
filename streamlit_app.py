import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="Agrocadena 🌱", layout="centered")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if 'logeado' not in st.session_state:
    st.session_state.logeado = False
if 'usuario_tipo' not in st.session_state:
    st.session_state.usuario_tipo = None
if 'nombre_usuario' not in st.session_state:
    st.session_state.nombre_usuario = ""

# --- 1. PANTALLA DE INICIO / ONBOARDING ---
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
                # Aquí podrías validar contra la pestaña "Usuarios" más adelante
                st.session_state.logeado = True
                st.session_state.nombre_usuario = user
                st.session_state.usuario_tipo = "Campesino" # Por defecto para prueba
                st.success("¡Bienvenido!")
                st.rerun()

    with tab2:
        st.write("### Crear cuenta")
        new_user = st.text_input("Nombre completo")
        new_tel = st.text_input("Teléfono")
        new_role = st.radio("Se identifica como:", ["Campesino", "Transportador", "Negocio"])
        btn_reg = st.button("Continuar")
        
        if btn_reg:
            # Lógica para guardar en pestaña 'Usuarios' más tarde
            st.session_state.logeado = True
            st.session_state.usuario_tipo = new_role
            st.session_state.nombre_usuario = new_user
            st.balloons()
            st.rerun()

# --- 2. VISTAS SEGÚN PERFIL (DENTRO DE LA APP) ---
else:
    # Sidebar común
    st.sidebar.title(f"Hola, {st.session_state.nombre_usuario}")
    st.sidebar.write(f"Perfil: **{st.session_state.usuario_tipo}**")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logeado = False
        st.rerun()

    # --- FLUJO 🧑‍🌾 CAMPESINO ---
    if st.session_state.usuario_tipo == "Campesino":
        st.title("🧑‍🌾 Panel del Productor")
        menu = st.sidebar.selectbox("Menú", ["🏠 Resumen", "📦 Publicar Cultivo", "🚜 Mis Costos"])

        if menu == "🏠 Resumen":
            st.markdown("#### Estado de tus ventas")
            col1, col2 = st.columns(2)
            col1.metric("Ingresos Mes", "$1.2M", "+5%")
            col2.metric("Pedidos Activos", "3")
            
        elif menu == "📦 Publicar Cultivo":
            st.subheader("Anuncia tu próxima cosecha")
            with st.form("pub_cultivo"):
                prod = st.text_input("Producto")
                cant = st.number_input("Cantidad disponible (kg)", min_value=1)
                pre = st.number_input("Precio por kg ($)")
                if st.form_submit_button("Publicar en Marketplace"):
                    st.success(f"¡Tu {prod} ya está disponible para los restaurantes!")

        elif menu == "🚜 Mis Costos":
            st.info("Aquí conectaremos con tu pestaña antigua de cálculos financieros.")

    # --- FLUJO 🚛 TRANSPORTADOR ---
    elif st.session_state.usuario_tipo == "Transportador":
        st.title("🚛 Panel de Logística")
        st.subheader("📍 Viajes disponibles en tu zona")
        
        viajes = [
            {"id": 1, "carga": "200 kg Papa", "origen": "Zipaquirá", "pago": "$120.000"},
            {"id": 2, "carga": "50 kg Cilantro", "origen": "Cajicá", "pago": "$45.000"}
        ]
        
        for v in viajes:
            with st.expander(f"🚚 {v['carga']} - {v['origen']}"):
                st.write(f"**Pago:** {v['pago']}")
                if st.button(f"Aceptar Viaje #{v['id']}"):
                    st.success("Viaje asignado. ¡Buen camino!")

    # --- FLUJO 🏪 NEGOCIO ---
    elif st.session_state.usuario_tipo == "Negocio":
        st.title("🏪 Portal de Compras")
        st.subheader("🛒 Frutas y Verduras Frescas")
        
        # Simulación de catálogo
        col1, col2 = st.columns(2)
        with col1:
            st.image("https://images.unsplash.com/photo-1518977676601-b53f02ac6d31?q=80&w=200", caption="Papa Sabanera")
            st.write("$2.000 / kg")
            st.button("Comprar Papa")
        with col2:
            st.image("https://images.unsplash.com/photo-1596040033229-a9821ebd058d?q=80&w=200", caption="Tomate Chonto")
            st.write("$3.500 / kg")
            st.button("Comprar Tomate")

# Menú inferior visual (opcional informativo)
st.sidebar.markdown("---")
st.sidebar.caption("Agrocadena v1.0 - Gestión de Datos Agronegocios")
