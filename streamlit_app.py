import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="Agrocadena 🌱", layout="wide") # Cambiado a wide para mejor visualización

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if 'logeado' not in st.session_state:
    st.session_state.logeado = False
if 'usuario_tipo' not in st.session_state:
    st.session_state.usuario_tipo = None
if 'nombre_usuario' not in st.session_state:
    st.session_state.nombre_usuario = ""

# --- DATOS DE REFERENCIA (Precios Corabastos) ---
precios_corabastos = {
    "Papa": 2800, "Tomate": 3200, "Cebolla": 1800, 
    "Café": 11000, "Mango": 4500, "Zanahoria": 1500
}

# --- 1. PANTALLA DE INICIO (Login/Registro) ---
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
                    st.error(f"Error al conectar: Comparta el Excel con el correo de la Service Account.")

    with tab2:
        st.write("### Crear cuenta")
        new_user = st.text_input("Nombre completo")
        new_tel = st.text_input("Teléfono")
        new_pass = st.text_input("Crea una Contraseña", type="password")
        new_role = st.radio("Se identifica como:", ["Campesino", "Transportador", "Negocio"])
        
        if st.button("Finalizar Registro"):
            if new_user and new_tel and new_pass:
                nuevo_row = pd.DataFrame([{"Nombre": new_user, "Telefono": new_tel, "Contraseña": new_pass, "Rol": new_role}])
                try:
                    df_existente = conn.read(worksheet="Usuarios", usecols=[0,1,2,3])
                    df_final = pd.concat([df_existente, nuevo_row], ignore_index=True)
                    conn.update(worksheet="Usuarios", data=df_final)
                    st.session_state.logeado = True
                    st.session_state.nombre_usuario = new_user
                    st.session_state.usuario_tipo = new_role
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error("Error de permisos. Verifique los Secrets y el botón Compartir del Excel.")

# --- 2. VISTAS SEGÚN PERFIL ---
else:
    st.sidebar.title(f"Hola, {st.session_state.nombre_usuario}")
    st.sidebar.write(f"Perfil: **{st.session_state.usuario_tipo}**")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logeado = False
        st.rerun()

    # --- PERFIL CAMPESINO ---
    if st.session_state.usuario_tipo == "Campesino":
        st.title("🧑‍🌾 Panel del Productor")
        
        # A. FORMULARIO DE FINCA
        with st.expander("📝 Registrar Datos de mi Finca / Cultivo", expanded=False):
            with st.form("form_finca"):
                c1, c2 = st.columns(2)
                with c1:
                    nom_finca = st.text_input("Nombre de la Finca")
                    cultivo = st.selectbox("Cultivo", list(precios_corabastos.keys()))
                    inv_ini = st.number_input("Inversión Inicial ($)", min_value=0)
                    costo_mes = st.number_input("Costo Mensual ($)", min_value=0)
                with c2:
                    prod_est = st.number_input("Producción Est. (Kilos)", min_value=1)
                    precio_v = st.number_input("Tu Precio de Venta por Kg ($)", min_value=0)
                    ubicacion = st.text_input("Departamento/Municipio")
                    meses = st.number_input("Duración del cultivo (meses)", min_value=1)
                
                if st.form_submit_button("Guardar Datos"):
                    nueva_finca = pd.DataFrame([{
                        "Productor": st.session_state.nombre_usuario, "Finca": nom_finca,
                        "Cultivo": cultivo, "Inversion": inv_ini, "Costo_Mensual": costo_mes,
                        "Produccion": prod_est, "Unidad": "Kilos", "Ubicacion": ubicacion,
                        "Meses": meses, "Precio_Venta": precio_v
                    }])
                    try:
                        df_f = conn.read(worksheet="Fincas")
                        df_f_final = pd.concat([df_f, nueva_finca], ignore_index=True)
                        conn.update(worksheet="Fincas", data=df_f_final)
                        st.success("¡Datos guardados!")
                        st.rerun()
                    except:
                        conn.update(worksheet="Fincas", data=nueva_finca)
                        st.rerun()

        # B. DASHBOARD DE ANÁLISIS
        try:
            df_fincas = conn.read(worksheet="Fincas")
            mis_fincas = df_fincas[df_fincas['Productor'] == st.session_state.nombre_usuario]

            if not mis_fincas.empty:
                st.markdown("---")
                st.subheader("📊 Análisis y Diagnóstico")
                finca_sel = st.selectbox("Selecciona tu finca", mis_fincas['Finca'].unique())
                f = mis_fincas[mis_fincas['Finca'] == finca_sel].iloc[0]

                # Cálculos
                costo_total = f['Inversion'] + (f['Costo_Mensual'] * f['Meses'])
                costo_kg = costo_total / f['Produccion']
                precio_mercado = precios_corabastos.get(f['Cultivo'], 3000)
                ganancia = (f['Precio_Venta'] - costo_kg) * f['Produccion']
                brecha = precio_mercado - f['Precio_Venta']

                # Visualización
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Costo/Kg", f"${costo_kg:,.0f}")
                m2.metric("Producción", f"{f['Produccion']:,} Kg", f"{f['Produccion']/50:.1f} bultos")
                m3.metric("Eficiencia", f"{(precio_mercado/costo_kg*100):.1f}%" if costo_kg >0 else "0%")
                m4.metric("Ganancia Est.", f"${ganancia:,.0f}", delta=ganancia)

                st.subheader("⚖️ Comparativa Corabastos")
                c_a, c_b, c_c = st.columns(3)
                c_a.metric(f"Precio Corabastos", f"${precio_mercado:,.0f}")
                c_b.metric("Tu Precio", f"${f['Precio_Venta']:,.0f}")
                c_c.metric("Brecha", f"${brecha:,.0f}", delta=-brecha)

                # Recomendación
                if ganancia < 0:
                    st.error(f"🔴 La finca {finca_sel} presenta PÉRDIDA. Plan de Acción: Reducir costos urgentemente.")
                else:
                    st.success(f"✅ ¡Buen margen! Plan de Acción: Mantener calidad y buscar venta directa.")
            else:
                st.info("Aún no has registrado datos de finca. Usa el formulario de arriba.")
        except:
            st.info("Registra tu primera finca para ver el análisis.")

    elif st.session_state.usuario_tipo == "Negocio":
        st.title("🏪 Panel de Negocios")
        st.write("Próximamente: Catálogo de productos directo del campo.")

    elif st.session_state.usuario_tipo == "Transportador":
        st.title("🚛 Panel Logístico")
        st.write("Próximamente: Rutas disponibles para recolección.")
