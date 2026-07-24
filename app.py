import streamlit as st
import pandas as pd
import sqlite3
import datetime

DB_FILE = "fospuca_operativo.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS fleet_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            week TEXT,
            sede TEXT,
            tot_unidades INTEGER,
            und_ruta INTEGER,
            und_sede INTEGER,
            und_taller INTEGER,
            fallas_gps INTEGER,
            analista TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS travel_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            week TEXT,
            unidad TEXT,
            conductor TEXT,
            desde TEXT,
            hasta TEXT,
            sede_resp TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS novedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            week TEXT,
            novedad TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Dashboard Operativo - Monitoreo y GPS", layout="wide", page_icon="🟢")

st.markdown('''
    <style>
    .main { background-color: #f4f9f4; }
    h1, h2, h3 { color: #1b4d3e; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #c8e6c9; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
''', unsafe_allow_html=True)

st.title("🟢 REPORTE OPERATIVO MONITOREO Y GPS")
st.markdown("---")

st.sidebar.header("⚙️ Panel de Control")
menu = st.sidebar.selectbox("Seleccione Vista", ["📊 Dashboard en Vivo", "📝 Registro de Datos", "📈 Estadísticas Históricas"])

SEDES_DEFAULT = [
    "Baruta", "Chacao", "Girardot", "Hatillo", 
    "Iribarren", "Maneiro", "Maracaibo", "San Diego"
]

LISTA_ANALISTAS = [
    "Crisópez Lua", 
    "Julio Moyano", 
    "Carlos Gonzales", 
    "Juan Bastardo", 
    "Pedro Camejo", 
    "José Manuel", 
    "Juan Juliani", 
    "Pedro Comaco"
]

if menu == "📝 Registro de Datos":
    st.subheader("📝 Cargar o Actualizar Reporte Operativo")
    
    col1, col2 = st.columns(2)
    with col1:
        report_date = st.date_input("Fecha del Reporte", datetime.date.today())
    with col2:
        report_week = st.text_input("Semana", "Semana 05 - 2026")
        
    st.markdown("### 1. Estatus de Flota y Asignación de Analistas por Sede")
    st.info("Configura los valores de unidades y selecciona el analista correspondiente a cada sede.")
    
    with st.form("fleet_form"):
        fleet_data = []
        for sede in SEDES_DEFAULT:
            st.markdown(f"**Sede: {sede}**")
            c_analista, c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1, 1])
            
            with c_analista:
                analista_seleccionado = st.selectbox(f"Analista ({sede})", LISTA_ANALISTAS, key=f"an_{sede}")
            with c1:
                tot = st.number_input(f"Tot ({sede})", min_value=0, value=10, key=f"tot_{sede}")
            with c2:
                ruta = st.number_input(f"Ruta ({sede})", min_value=0, value=7, key=f"ruta_{sede}")
            with c3:
                sede_u = st.number_input(f"Sede ({sede})", min_value=0, value=2, key=f"sed_{sede}")
            with c4:
                taller = st.number_input(f"Taller ({sede})", min_value=0, value=1, key=f"tall_{sede}")
            with c5:
                gps = st.number_input(f"GPS ({sede})", min_value=0, value=0, key=f"gps_{sede}")
            
            fleet_data.append({
                "date": str(report_date),
                "week": report_week,
                "sede": sede,
                "tot_unidades": tot,
                "und_ruta": ruta,
                "und_sede": sede_u,
                "und_taller": taller,
                "fallas_gps": gps,
                "analista": analista_seleccionado
            })
            st.markdown("---")
            
        submitted_fleet = st.form_submit_button("Guardar Estatus de Flota")
        if submitted_fleet:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("DELETE FROM fleet_status WHERE date = ? AND week = ?", (str(report_date), report_week))
            for item in fleet_data:
                c.execute('''
                    INSERT INTO fleet_status (date, week, sede, tot_unidades, und_ruta, und_sede, und_taller, fallas_gps, analista)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (item["date"], item["week"], item["sede"], item["tot_unidades"], item["und_ruta"], item["und_sede"], item["und_taller"], item["fallas_gps"], item["analista"]))
            conn.commit()
            conn.close()
            st.success("¡Estatus de flota y analistas guardados exitosamente!")

    st.markdown("### 2. Unidades Viajeras y Novedades")
    with st.form("travel_novedades_form"):
        st.markdown("#### Registrar Unidad Viajera")
        t_unidad = st.text_input("Código de Unidad (Ej. Unid 001)")
        t_conductor = st.text_input("Conductor")
        c_i, c_f = st.columns(2)
        with c_i:
            t_desde = st.text_input("Desde")
        with c_f:
            t_hasta = st.text_input("Hasta")
        t_sede_resp = st.selectbox("Sede Responsable", SEDES_DEFAULT)
        
        add_travel = st.form_submit_button("Añadir Unidad Viajera")
        if add_travel and t_unidad:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('''
                INSERT INTO travel_units (date, week, unidad, conductor, desde, hasta, sede_resp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(report_date), report_week, t_unidad, t_conductor, t_desde, t_hasta, t_sede_resp))
            conn.commit()
            conn.close()
            st.success(f"Unidad {t_unidad} agregada.")

    with st.form("novedad_form"):
        st.markdown("#### Registrar Novedad / Alerta")
        nov_text = st.text_area("Descripción de la Novedad o Incidencia")
        add_nov = st.form_submit_button("Registrar Novedad")
        if add_nov and nov_text:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('''
                INSERT INTO novedades (date, week, novedad)
                VALUES (?, ?, ?)
            ''', (str(report_date), report_week, nov_text))
            conn.commit()
            conn.close()
            st.success("Novedad registrada.")

elif menu == "📊 Dashboard en Vivo":
    conn = sqlite3.connect(DB_FILE)
    weeks_df = pd.read_sql("SELECT DISTINCT week FROM fleet_status", conn)
    
    if weeks_df.empty:
        st.warning("No hay datos registrados aún. Por favor, ve a la sección 'Registro de Datos' para ingresar información.")
    else:
        selected_week = st.selectbox("Seleccionar Semana", weeks_df["week"].tolist())
        
        df_fleet = pd.read_sql("SELECT * FROM fleet_status WHERE week = ?", conn, params=(selected_week,))
        df_travel = pd.read_sql("SELECT * FROM travel_units WHERE week = ?", conn, params=(selected_week,))
        df_nov = pd.read_sql("SELECT * FROM novedades WHERE week = ?", conn, params=(selected_week,))
        
        tot_u = df_fleet["tot_unidades"].sum()
        tot_r = df_fleet["und_ruta"].sum()
        tot_s = df_fleet["und_sede"].sum()
        tot_t = df_fleet["und_taller"].sum()
        tot_gps = df_fleet["fallas_gps"].sum()
        
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            pct_r = int((tot_r / tot_u * 100) if tot_u > 0 else 0)
            st.metric("UNIDADES EN RUTA", f"{tot_r} / {tot_u}", f"{pct_r}%")
        with k2:
            pct_s = int((tot_s / tot_u * 100) if tot_u > 0 else 0)
            st.metric("UNIDADES EN SEDE", f"{tot_s} / {tot_u}", f"{pct_s}%")
        with k3:
            pct_t = int((tot_t / tot_u * 100) if tot_u > 0 else 0)
            st.metric("UNIDADES EN TALLER", f"{tot_t} / {tot_u}", f"{pct_t}%")
        with k4:
            pct_gps = int((tot_gps / tot_u * 100) if tot_u > 0 else 0)
            st.metric("FALLAS GPS (Alerta)", f"{tot_gps} / {tot_u}", f"{pct_gps}%")
            
        st.markdown("---")
        
        st.subheader("📋 Status de Flota y Responsables por Sede")
        display_df = df_fleet[["sede", "tot_unidades", "und_ruta", "und_sede", "und_taller", "fallas_gps", "analista"]].copy()
        display_df.columns = ["Sede", "Tot. Unidades", "Und. Ruta", "Und. Sede", "Und. Taller", "Fallos GPS", "Analista Responsable"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        c_left, c_right = st.columns(2)
        with c_left:
            st.subheader("🚚 Unidades Viajeras")
            if not df_travel.empty:
                st.dataframe(df_travel[["unidad", "conductor", "desde", "hasta", "sede_resp"]], use_container_width=True, hide_index=True)
            else:
                st.info("No hay unidades viajeras registradas.")
                
        with c_right:
            st.subheader("⚠️ Novedades - Bitácora")
            if not df_nov.empty:
                for idx, row in df_nov.iterrows():
                    st.markdown(f"🟢 • {row['novedad']}")
            else:
                st.info("Sin novedades registradas.")

    conn.close()

elif menu == "📈 Estadísticas Históricas":
    st.subheader("📈 Análisis y Estadísticas de Flota")
    conn = sqlite3.connect(DB_FILE)
    df_all = pd.read_sql("SELECT * FROM fleet_status", conn)
    conn.close()
    
    if df_all.empty:
        st.info("No hay suficiente información histórica.")
    else:
        df_grouped = df_all.groupby("week")[["tot_unidades", "und_ruta", "und_sede", "und_taller", "fallas_gps"]].sum().reset_index()
        st.markdown("### Tendencia General por Semana")
        st.line_chart(df_grouped.set_index("week"))
