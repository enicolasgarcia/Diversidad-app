import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="Agrocadena 🌱", layout="centered")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

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
                except:
                    st.warning("No se pudo validar en la base de datos. Entrando como prueba.")
                    st.session_state.logeado = True
                    st.session_state.nombre_usuario = user
                    st.session_state.usuario_tipo = "Campesino"
                    st.rerun()

    with tab2:
        st.write("### Crear cuenta")
        new_user = st.text_input("Nombre completo")
        new_tel = st.text_input("Teléfono")
        new_pass = st.text_input("Crea una Contraseña", type="password")
        new_role = st.radio("Se identifica como:", ["Campesino", "Transportador", "Negocio"])
        
        if st.button("Finalizar Registro"):
            if new_user and new_tel and new_pass:
                nuevo_usuario = pd.DataFrame([{
                    "Nombre": new_user, 
                    "Telefono": new_tel, 
                    "Contraseña": new_pass, 
                    "Rol": new_role
                }])
                
                try:
                    # Intentamos leer datos existentes para no sobrescribir
                    try:
                        df_actual = conn.read(worksheet="Usuarios")
                        df_final = pd.concat([df_actual, nuevo_usuario], ignore_index=True)
                    except:
                        df_final = nuevo_usuario
                    
                    # Guardar en Google Sheets
                    conn.update(worksheet="Usuarios", data=df_final)
                    
                    st.session_state.logeado = True
                    st.session_state.usuario_tipo = new_role
                    st.session_state.nombre_usuario = new_user
                    st.success("¡Registro exitoso!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
                    st.info("Nota: Si el error persiste, verifica los permisos de 'Editor' en tu Google Sheets.")
            else:
                st.warning("Por favor completa todos los campos")

# --- 2. VISTAS SEGÚN PERFIL (DENTRO DE LA APP) ---
else:
    st.sidebar.title(f"Hola, {st.session_state.nombre_usuario}")
    st.sidebar.write(f"Perfil: **{st.session_state.usuario_tipo}**")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logeado = False
        st.rerun()

    # --- FLUJO 🧑‍🌾 CAMPESINO ---
    if st.session_state.usuario_tipo == "Campesino":
        st.title("🧑‍🌾 Panel del Productor")
        menu = st.sidebar.selectbox("Menú", ["🏠 Resumen", "💰 Calculadora de Costos", "📦 Publicar Cultivo"])

        if menu == "🏠 Resumen":
            st.markdown("#### Estado de tus ventas")
            col1, col2 = st.columns(2)
            col1.metric("Ingresos Mes", "$1.2M", "+5%")
            col2.metric("Pedidos Activos", "3")
            
        elif menu == "💰 Calculadora de Costos":
            st.subheader("🚜 Tu Calculadora de Producción")
            st.write("Registra tus gastos para calcular tu rentabilidad.")
            
            with st.form("form_costos"):
                col_a, col_b = st.columns(2)
                item = col_a.text_input("Concepto (Ej: Semillas, Fertilizante)")
                valor = col_b.number_input("Costo del Insumo ($)", min_value=0)
                btn_gasto = st.form_submit_button("Guardar en mi histórico")
                
                if btn_gasto:
                    nuevo_gasto = pd.DataFrame([{
                        "Usuario": st.session_state.nombre_usuario,
                        "Concepto": item,
                        "Valor": valor
                    }])
                    try:
                        try:
                            c_existentes = conn.read(worksheet="Calculadora")
                            c_actualizado = pd.concat([c_existentes, nuevo_gasto], ignore_index=True)
                        except:
                            c_actualizado = nuevo_gasto
                            
                        conn.update(worksheet="Calculadora", data=c_actualizado)
                        st.success("¡Gasto guardado exitosamente!")
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

            st.markdown("---")
            st.write("### Mis Gastos Registrados")
            try:
                historial = conn.read(worksheet="Calculadora")
                filtro = historial[historial['Usuario'] == st.session_state.nombre_usuario]
                st.dataframe(filtro, use_container_width=True)
                total = filtro['Valor'].sum()
                st.metric("Total Inversión", f"${total:,.0f}")
            except:
                st.info("Aún no tienes gastos registrados.")

        elif menu == "📦 Publicar Cultivo":
            st.subheader("Anuncia tu próxima cosecha")
            with st.form("pub_cultivo"):
                prod = st.text_input("Producto")
                cant = st.number_input("Cantidad disponible (kg)", min_value=1)
                pre = st.number_input("Precio por kg ($)")
                if st.form_submit_button("Publicar en Marketplace"):
                    st.success(f"¡Tu {prod} ya está disponible para los restaurantes!")

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
        
        col1, col2 = st.columns(2)
        with col1:
            st.image("https://images.unsplash.com/photo-1518977676601-b53f02ac6d31?q=80&w=200", caption="Papa Sabanera")
            st.write("$2.000 / kg")
            st.button("Comprar Papa")
        with col2:
            st.image("https://images.unsplash.com/photo-1596040033229-a9821ebd058d?q=80&w=200", caption="Tomate Chonto")
            st.write("$3.500 / kg")
            st.button("Comprar Tomate")

# Menú inferior
st.sidebar.markdown("---")
st.sidebar.caption("Agrocadena v1.1 - Gestión de Datos")
