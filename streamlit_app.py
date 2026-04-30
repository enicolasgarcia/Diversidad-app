import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="DIVERSIDAD 🌱", layout="wide") # Cambiado a wide para mejor visualización

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
    st.title("🌱 DIVERSIDAD")
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

    # ==========================================
    # 1. PERFIL CAMPESINO
    # ==========================================
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
                    # Dividimos c2 en dos pequeñas columnas para Cantidad y Unidad
                    col_cant, col_unid = st.columns([2, 1])
                    with col_cant:
                        prod_est = st.number_input("Producción Est.", min_value=1)
                    with col_unid:
                        # Selector de unidades solicitado
                        unidad_elegida = st.selectbox("Unidad", ["Kilos", "Quintales", "Libras", "Bultos"])
                    
                    precio_v = st.number_input(f"Precio de Venta por {unidad_elegida} ($)", min_value=0)
                    ubicacion = st.text_input("Departamento / Municipio") # Añadí espacio para que no pegue
                    meses = st.number_input("Duración del cultivo (meses)", min_value=1)
                
                submit_finca = st.form_submit_button("Guardar Datos")

                if submit_finca:
                    if nom_finca and ubicacion:
                        nueva_finca = pd.DataFrame([{
                            "Productor": st.session_state.nombre_usuario, "Finca": nom_finca,
                            "Cultivo": cultivo, "Inversion": inv_ini, "Costo_Mensual": costo_mes,
                            "Produccion": prod_est, "Unidad": unidad_elegida, "Ubicacion": ubicacion,
                            "Meses": meses, "Precio_Venta": precio_v
                        }])
                        try:
                            df_f = conn.read(worksheet="Fincas", ttl=0)
                            df_f_final = pd.concat([df_f, nueva_finca], ignore_index=True)
                            conn.update(worksheet="Fincas", data=df_f_final)
                        except:
                            conn.update(worksheet="Fincas", data=nueva_finca)
                        st.success("¡Datos guardados!")
                        st.rerun()

        # --- B. BUZÓN DE NOTIFICACIONES ---
        st.markdown("---")
        st.subheader("🔔 Notificaciones de Interés")
        try:
            df_o_read = conn.read(worksheet="Ofertas", ttl=0)
            df_u_read = conn.read(worksheet="Usuarios", ttl=0)
            df_f_read = conn.read(worksheet="Fincas", ttl=0) 
            
            u_clean = str(st.session_state.nombre_usuario).strip().lower()
            df_o_read['Estado'] = df_o_read['Estado'].fillna('Pendiente')
            
            mis_notas = df_o_read[
                (df_o_read['Productor'].astype(str).str.strip().str.lower() == u_clean) & 
                (df_o_read['Estado'] != 'Vendido')
            ]
            
            if not mis_notas.empty:
                for i, o in mis_notas.iterrows():
                    # 1. Buscamos la unidad guardada en Fincas
                    detalle = df_f_read[
                        (df_f_read['Productor'].astype(str).str.strip().str.lower() == u_clean) & 
                        (df_f_read['Cultivo'].astype(str).str.strip() == str(o['Producto']).strip())
                    ]
                    
                    # 2. Construimos el texto de cantidad de forma limpia
                    if not detalle.empty:
                        valor = detalle.iloc[0]['Produccion']
                        # Si no tienes columna 'Unidad' aún, por defecto dirá Kilos
                        u_medida = detalle.iloc[0]['Unidad'] if 'Unidad' in detalle.columns else "Kilos"
                        cantidad_texto = f"{valor} {u_medida}"
                    else:
                        cantidad_texto = "la cantidad acordada"
                    
                    interesado_nombre = str(o['Interesado']).strip()
                    user_data = df_u_read[df_u_read['Nombre'].astype(str).str.strip() == interesado_nombre]
                    
                    # --- DISEÑO MEJORADO ---
                    with st.container():
                        col_info, col_whatsapp, col_accion = st.columns([2, 1, 1])
                        
                        with col_info:
                            # Texto con espacios y negritas claras
                            st.markdown(f"📩 **{o['Interesado']}** está interesado en:")
                            st.info(f"📦 {cantidad_texto} de **{o['Producto']}**")
                        
                        with col_whatsapp:
                            if not user_data.empty:
                                tel = "".join(filter(str.isdigit, str(user_data.iloc[0]['Telefono'])))
                                if not tel.startswith("57"): tel = "57" + tel
                                
                                # Mensaje de WhatsApp con espacios (usando %20 para URL segura)
                                msg_wa = f"Hola, vi que estás interesado en mis {cantidad_texto} de {o['Producto']}. ¿Hablamos?"
                                url_wa = f"https://wa.me/{tel}?text={msg_wa.replace(' ', '%20')}"
                                
                                st.write("") # Espacio visual
                                st.link_button("💬 Hablar", url_wa)
                        
                        with col_accion:
                            st.write("") # Espacio visual
                            if st.button("✅ Vendido", key=f"btn_{i}"):
                                df_o_read.at[i, 'Estado'] = 'Vendido'
                                conn.update(worksheet="Ofertas", data=df_o_read)
                                st.success("¡Venta registrada!")
                                st.rerun()
                        st.divider() # Línea sutil para separar cada oferta
            else:
                st.write("No tienes ofertas pendientes por ahora.")

        except Exception as e:
            st.error(f"Error al cargar el buzón: {e}")

        # --- C. DASHBOARD DE ANÁLISIS ---
        try:
            df_fincas = conn.read(worksheet="Fincas", ttl=0)
            df_fincas['Productor'] = df_fincas['Productor'].astype(str).str.strip()
            usuario_actual = str(st.session_state.nombre_usuario).strip()
            mis_fincas = df_fincas[df_fincas['Productor'] == usuario_actual]

            if not mis_fincas.empty:
                st.markdown("---")
                st.subheader("📊 Análisis y Diagnóstico")
                finca_sel = st.selectbox("Selecciona tu finca", mis_fincas['Finca'].unique())
                f = mis_fincas[mis_fincas['Finca'] == finca_sel].iloc[0]

                # Cálculos
                inv = float(f['Inversion']); c_mes = float(f['Costo_Mensual']); t_meses = float(f['Meses'])
                prod = float(f['Produccion']); p_venta = float(f['Precio_Venta'])
                costo_kg = (inv + (c_mes * t_meses)) / prod if prod > 0 else 0
                precio_m = precios_corabastos.get(f['Cultivo'], 3000)
                ganancia = (p_venta - costo_kg) * prod

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Costo/Kg", f"${costo_kg:,.0f}")
                m2.metric("Producción", f"{prod:,.0f} Kg")
                m3.metric("Eficiencia", f"{(precio_m/costo_kg*100 if costo_kg>0 else 0):.1f}%")
                m4.metric("Ganancia Est.", f"${ganancia:,.0f}", delta=ganancia)

                # --- 1. CÁLCULO DE BRECHA (Importante añadirlo) ---
                brecha = precio_m - p_venta

                # --- 2. RECOMENDACIÓN DE CONSULTORÍA ---
                st.markdown("---")
                st.subheader("💡 Recomendación de Consultoría")

                try:
                    # Buscamos la unidad de forma segura
                    # Si 'row' existe, la tomamos de ahí. Si no, usamos "Kilos"
                    if 'Unidad' in row:
                        u_medida = row['Unidad']
                    else:
                        u_medida = "Kilos"

                    if ganancia < 0:
                        st.error(f"🔴 La finca {finca_sel} presenta PÉRDIDA.")
                        # Agregamos espacios antes y después de las variables ()
                        st.warning(f"Análisis: Tus costos por {u_medida} (${costo_kg:,.0f}) superan a tu precio de venta (${p_venta:,.0f}).")
                    else:
                        st.success(f"✅ ¡Tu finca es rentable!")
                        # Usamos comas en el f-string para asegurar que Python separe los bloques
                        texto_exito = f"Análisis: Tus costos por {u_medida} (${costo_kg:,.0f}) " + "comparados con tu precio " + f"(${p_venta:,.0f})."
                        st.info(texto_exito)

                except Exception as e:
                    # Forzamos el espacio con un "+" para que no haya duda
                    texto_error = f"Análisis: Tus costos por unidad (${costo_kg:,.0f}) " + "comparados con tu precio " + f"(${p_venta:,.0f})."
                    st.info(texto_error)

                # --- 3. COMPARATIVA CORABASTOS ---
                st.subheader("⚖️ Comparativa Corabastos")
                c_a, c_b, c_c = st.columns(3)
                c_a.metric(f"Precio Corabastos", f"${precio_m:,.0f}")
                c_b.metric("Tu Precio", f"${p_venta:,.0f}")
                c_c.metric("Brecha", f"${brecha:,.0f}", delta=-brecha)
                
                # D. TABLA HISTÓRICA
                st.markdown("---")
                st.subheader("📋 Tu Historial de Cultivos")
                st.dataframe(mis_fincas, use_container_width=True)
                
                with st.expander("🗑️ Zona de Borrado"):
                    f_borrar = st.selectbox("Finca a eliminar", mis_fincas['Finca'].unique())
                    if st.button("Confirmar Eliminación"):
                        df_act = df_fincas[~((df_fincas['Productor'] == usuario_actual) & (df_fincas['Finca'] == f_borrar))]
                        conn.update(worksheet="Fincas", data=df_act)
                        st.rerun()
            else:
                st.info("Registra una finca para ver el análisis.")
        except:
            st.error("Error al cargar datos de fincas.")

    # ==========================================
    # 2. PERFIL NEGOCIO
    # ==========================================
    elif st.session_state.usuario_tipo == "Negocio":
        st.title("🏪 Marketplace: Abastecimiento Directo")
        st.write("Explora los productos disponibles directamente de las fincas.")

        try:
            # Leemos Fincas para el mercado y Usuarios para los teléfonos
            df_market = conn.read(worksheet="Fincas", ttl=0)
            df_u_read = conn.read(worksheet="Usuarios", ttl=0) 

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
                                # 1. Preparamos el registro con estado 'Pendiente'
                                nueva_o = pd.DataFrame([{
                                    "Productor": row['Productor'],
                                    "Interesado": st.session_state.nombre_usuario,
                                    "Producto": row['Cultivo'],
                                    "Finca": row['Finca'],
                                    "Fecha": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                                    "Estado": "Pendiente" # <-- Esto automatiza tu Excel
                                }])
                                
                                # 2. Guardado en Google Sheets
                                try:
                                    df_o = conn.read(worksheet="Ofertas", ttl=0)
                                    df_o_final = pd.concat([df_o, nueva_o], ignore_index=True)
                                    conn.update(worksheet="Ofertas", data=df_o_final)
                                except:
                                    conn.update(worksheet="Ofertas", data=nueva_o)
                                
                                st.success(f"¡Oferta enviada a {row['Productor']}!")

                                # --- BOTÓN DE WHATSAPP PARA EL NEGOCIO ---
                                user_prod = df_u_read[df_u_read['Nombre'].astype(str).str.strip() == str(row['Productor']).strip()]
                                if not user_prod.empty:
                                    tel_p = "".join(filter(str.isdigit, str(user_prod.iloc[0]['Telefono'])))
                                    if not tel_p.startswith("57"): tel_p = "57" + tel_p
                                    
                                    mensaje_n = f"Hola {row['Productor']}, soy de {st.session_state.nombre_usuario}. Acabo de enviarte una oferta por tu {row['Cultivo']} en DIVERSIDAD 🦁."
                                    url_n = f"https://wa.me/{tel_p}?text={mensaje_n.replace(' ', '%20')}"
                                    
                                    st.link_button(f"💬 Hablar con el Productor", url_n)
                        
                        st.divider() 
            else:
                st.info("No hay productos en el mercado.")
        except Exception as e:
            st.error(f"Error al cargar el marketplace: {e}") 

    # ==========================================
    # 3. PERFIL TRANSPORTADOR
    # ==========================================
    elif st.session_state.usuario_tipo == "Transportador":
        st.title("🚛 Panel Logístico")
        st.write("Gestiona las rutas de recolección disponibles.")
        
        try:
            # 1. Leemos Ofertas y Usuarios
            df_o_log = conn.read(worksheet="Ofertas", ttl=0)
            df_u_log = conn.read(worksheet="Usuarios", ttl=0)
            
            # 2. Filtramos: Solo lo que está "Vendido"
            df_o_log['Estado'] = df_o_log['Estado'].fillna('Pendiente')
            rutas_disponibles = df_o_log[df_o_log['Estado'] == 'Vendido']
            
            if not rutas_disponibles.empty:
                st.success(f"¡Hay {len(rutas_disponibles)} rutas listas para recolección!")
                
                for i, r in rutas_disponibles.iterrows():
                    with st.container():
                        col_text, col_btns = st.columns([2, 1])
                        
                        with col_text:
                            st.markdown(f"""
                            ### 📦 {r['Producto']}
                            * **Origen:** Finca {r['Finca']} ({r['Productor']})
                            * **Destino:** {r['Interesado']}
                            """)
                        
                        with col_btns:
                            # --- OPCIÓN 1: Contacto Directo ---
                            # Buscamos el teléfono del productor
                            prod_info = df_u_log[df_u_log['Nombre'].astype(str).str.strip() == str(r['Productor']).strip()]
                            
                            if not prod_info.empty:
                                tel = "".join(filter(str.isdigit, str(prod_info.iloc[0]['Telefono'])))
                                if not tel.startswith("57"): tel = "57" + tel
                                
                                mensaje_t = f"Hola {r['Productor']}, soy el transportador de DIVERSIDAD 🦁. Voy en camino por tu cosecha de {r['Producto']}."
                                url_t = f"https://wa.me/{tel}?text={mensaje_t.replace(' ', '%20')}"
                                st.link_button("📞 Coordinar Recogida", url_t)
                            
                            # --- OPCIÓN 2: Cambiar Estado a "En Camino" ---
                            if st.button("🚚 Aceptar y Recoger", key=f"ship_{i}"):
                                df_o_log.at[i, 'Estado'] = 'En Camino'
                                conn.update(worksheet="Ofertas", data=df_o_log)
                                st.balloons()
                                st.success("Estado actualizado: ¡Producto en camino!")
                                st.rerun()
            else:
                st.info("No hay rutas vendidas esperando transporte.")
                
        except Exception as e:
            st.error(f"Error en logística: {e}")
