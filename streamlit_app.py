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
            # Le ponemos un nombre claro al formulario: "form_finca"
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
                
                # --- ESTE BOTÓN DEBE ESTAR ADENTRO DEL "WITH ST.FORM" ---
                submit_finca = st.form_submit_button("Guardar Datos")

                if submit_finca:
                    if nom_finca and ubicacion: # Validación mínima
                        nueva_finca = pd.DataFrame([{
                            "Productor": st.session_state.nombre_usuario, 
                            "Finca": nom_finca,
                            "Cultivo": cultivo, 
                            "Inversion": inv_ini, 
                            "Costo_Mensual": costo_mes,
                            "Produccion": prod_est, 
                            "Unidad": "Kilos", 
                            "Ubicacion": ubicacion,
                            "Meses": meses, 
                            "Precio_Venta": precio_v
                        }])
                        try:
                            df_f = conn.read(worksheet="Fincas")
                            df_f_final = pd.concat([df_f, nueva_finca], ignore_index=True)
                            conn.update(worksheet="Fincas", data=df_f_final)
                            st.success("¡Datos guardados!")
                            st.rerun()
                        except:
                            conn.update(worksheet="Fincas", data=nueva_finca)
                            st.success("¡Primera finca registrada!")
                            st.rerun()
                    else:
                        st.warning("Completa el nombre y ubicación")

        # B. DASHBOARD DE ANÁLISIS
        try:
            # Forzamos la lectura sin caché para ver cambios inmediatos
            df_fincas = conn.read(worksheet="Fincas", ttl=0)
            
            # Convertimos a string y quitamos espacios para que el filtro no falle
            df_fincas['Productor'] = df_fincas['Productor'].astype(str).str.strip()
            usuario_actual = str(st.session_state.nombre_usuario).strip()
            
            # FILTRO: Buscamos las fincas del usuario
            mis_fincas = df_fincas[df_fincas['Productor'] == usuario_actual]

            if not mis_fincas.empty:
                st.markdown("---")
                st.subheader("📊 Análisis y Diagnóstico")
                
                # Selector de finca
                finca_sel = st.selectbox("Selecciona tu finca", mis_fincas['Finca'].unique())
                f = mis_fincas[mis_fincas['Finca'] == finca_sel].iloc[0]

                # Cálculos matemáticos
                # Aseguramos que los valores sean números para evitar errores
                inv = float(f['Inversion'])
                c_mes = float(f['Costo_Mensual'])
                t_meses = float(f['Meses'])
                prod = float(f['Produccion'])
                p_venta = float(f['Precio_Venta'])

                costo_total = inv + (c_mes * t_meses)
                costo_kg = costo_total / prod if prod > 0 else 0
                precio_mercado = precios_corabastos.get(f['Cultivo'], 3000)
                ganancia = (p_venta - costo_kg) * prod
                brecha = precio_mercado - p_venta

                # --- VISUALIZACIÓN DE MÉTRICAS ---
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Costo/Kg", f"${costo_kg:,.0f}")
                m2.metric("Producción", f"{prod:,.0f} Kg", f"{prod/50:.1f} bultos")
                
                # Eficiencia lógica
                eficiencia_val = (precio_mercado / costo_kg * 100) if costo_kg > 0 else 0
                m3.metric("Eficiencia", f"{eficiencia_val:.1f}%")
                m4.metric("Ganancia Est.", f"${ganancia:,.0f}", delta=ganancia)

                st.subheader("⚖️ Comparativa Corabastos")
                c_a, c_b, c_c = st.columns(3)
                c_a.metric(f"Precio Corabastos", f"${precio_mercado:,.0f}")
                c_b.metric("Tu Precio", f"${p_venta:,.0f}")
                
                # La brecha es mejor si es pequeña o negativa (estás vendiendo caro)
                c_c.metric("Brecha", f"${brecha:,.0f}", delta=-brecha)

                # --- RECOMENDACIÓN ---
                st.subheader("💡 Recomendación de Consultoría")
                if ganancia < 0:
                    st.error(f"🔴 La finca {finca_sel} presenta PÉRDIDA.")
                    st.warning(f"Análisis: Tus costos por Kg (${costo_kg:,.0f}) superan tu precio de venta (${p_venta:,.0f}).")
                else:
                    st.success(f"✅ ¡Tu finca es rentable! Tienes un margen de ${(p_venta - costo_kg):,.0f} por kilo.")

            else:
                st.info(f"Aún no hay fincas registradas para {usuario_actual}. ¡Usa el formulario de arriba!")

        # --- NUEVO: BUZÓN DE NOTIFICACIONES ---
                st.markdown("---")
                st.subheader("🔔 Notificaciones de Interés")
                try:
                    # Leemos la nueva pestaña de Ofertas
                    df_o_read = conn.read(worksheet="Ofertas", ttl=0)
                    # Limpiamos el nombre del usuario actual (quitar espacios y pasar a minúsculas)
            usuario_clean = str(st.session_state.nombre_usuario).strip().lower()
            
            # Limpiamos la columna de la base de datos para comparar igual a igual
            df_o_read['Productor_Match'] = df_o_read['Productor'].astype(str).str.strip().str.lower()
            
            # Filtramos las notas usando los nombres ya limpios
            mis_notas = df_o_read[df_o_read['Productor_Match'] == usuario_clean]
                    
                    if not mis_notas.empty:
                        for _, o in mis_notas.iterrows():
                            st.info(f"📩 **{o['Interesado']}** está interesado en tu **{o['Producto']}** (Finca: {o['Finca']})")
                    else:
                        st.write("No tienes ofertas nuevas por ahora.")
                except:
                    st.write("Aún no hay ofertas registradas en el sistema.")
                    
        except Exception as e:
            st.error("Error al cargar el análisis. Verifica que los datos en el Excel sean números.")
            # st.exception(e) # Descomenta esto si quieres ver el error técnico

        # C. TABLA DE REGISTROS HISTÓRICOS
        st.markdown("---")
        st.subheader("📋 Tu Historial de Cultivos")
        st.dataframe(mis_fincas, use_container_width=True)
        
        # D. ZONA DE BORRADO
        with st.expander("🗑️ Zona de Corrección (Borrar Registros)"):
            finca_a_borrar = st.selectbox("Selecciona la finca a eliminar", mis_fincas['Finca'].unique(), key="del_finca")
            if st.button("Eliminar Registro Permanentemente"):
                try:
                    # Filtramos el dataframe eliminando la fila seleccionada
                    df_actualizado = df_fincas[~((df_fincas['Productor'] == usuario_actual) & (df_fincas['Finca'] == finca_a_borrar))]
                    conn.update(worksheet="Fincas", data=df_actualizado)
                    st.warning(f"Registro de {finca_a_borrar} eliminado.")
                    st.rerun()
                except:
                    st.error("No se pudo eliminar el registro.")

    # ==========================================
    # 2. PERFIL NEGOCIO
    # ==========================================
    elif st.session_state.usuario_tipo == "Negocio":
        st.title("🏪 Marketplace: Abastecimiento Directo")
        st.write("Explora los productos disponibles directamente de las fincas.")

        try:
            df_market = conn.read(worksheet="Fincas", ttl=0)
            if not df_market.empty:
                filtro_cultivo = st.multiselect("Filtrar por producto", df_market['Cultivo'].unique())
                df_display = df_market[df_market['Cultivo'].isin(filtro_cultivo)] if filtro_cultivo else df_market

                st.markdown("### 🛒 Productos Disponibles")
                for index, row in df_display.iterrows():
                    with st.container():
                        c1, c2, c3 = st.columns([2, 2, 1])
                        with c1:
                            st.markdown(f"#### {row['Cultivo']} - Finca {row['Finca']}")
                            st.caption(f"📍 Ubicación: {row['Ubicacion']}")
                        with c2:
                            st.write(f"**Cantidad:** {row['Produccion']} Kg")
                            st.write(f"**Precio:** ${float(row['Precio_Venta']):,.0f} / Kg")
                        with c3:
                            if st.button(f"Ofertar", key=f"btn_{index}"):
                                # 1. Preparamos el registro de la oferta
                                nueva_o = pd.DataFrame([{
                                    "Productor": row['Productor'],
                                    "Interesado": st.session_state.nombre_usuario,
                                    "Producto": row['Cultivo'],
                                    "Finca": row['Finca'],
                                    "Fecha": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                                }])
                                
                                # 2. Lo guardamos en la pestaña "Ofertas"
                                try:
                                    df_o = conn.read(worksheet="Ofertas", ttl=0)
                                    df_o_final = pd.concat([df_o, nueva_o], ignore_index=True)
                                    conn.update(worksheet="Ofertas", data=df_o_final)
                                except:
                                    conn.update(worksheet="Ofertas", data=nueva_o)
                                
                                st.success(f"¡Oferta enviada a {row['Productor']}!")
                        
                        st.divider() 
            else:
                st.info("No hay productos en el mercado.")
        except:
            st.error("Error al cargar el marketplace.") 

    # ==========================================
    # 3. PERFIL TRANSPORTADOR
    # ==========================================
    elif st.session_state.usuario_tipo == "Transportador":
        st.title("🚛 Panel Logístico")
        st.write("Gestiona las rutas de recolección disponibles.")
        st.info("Próximamente: Mapa de rutas y asignación de fletes.")
