import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
from weasyprint import HTML

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

st.set_page_config(page_title="Dashboard Operativo - FOSPUCA 360", layout="wide", page_icon="🟢")

st.markdown('''
    <style>
    .main { background-color: #f4f9f4; }
    h1, h2, h3 { color: #1b4d3e; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #c8e6c9; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    </style>
''', unsafe_allow_html=True)

st.title("🟢 REPORTE OPERATIVO MONITOREO Y GPS - FOSPUCA 360")
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
    col_t, col_n = st.columns(2)
    with col_t:
        with st.form("travel_form"):
            st.markdown("#### Registrar Unidad Viajera")
            t_unidad = st.text_input("Código de Unidad")
            t_conductor = st.text_input("Conductor")
            t_desde = st.text_input("Desde")
            t_hasta = st.text_input("Hasta")
            t_sede_resp = st.selectbox("Sede Responsable", SEDES_DEFAULT, key="trav_sede")
            add_travel = st.form_submit_button("Añadir Viajera")
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
    with col_n:
        with st.form("novedad_form"):
            st.markdown("#### Registrar Novedad")
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
        
        # Top section: Metrics & Mini Charts matching the sketch
        st.markdown("### 📊 Indicadores Generales de Flota")
        k1, k2, k3, k4 = st.columns(4)
        
        import altair as alt
        
        def make_donut(value, total, title, color_hex):
            source = pd.DataFrame({
                "Category": [title, "Resto"],
                "Value": [value, max(0, total - value)]
            })
            chart = alt.Chart(source).mark_arc(innerRadius=25, outerRadius=40).encode(
                theta=alt.Theta(field="Value", type="quantitative"),
                color=alt.Color(field="Category", type="nominal", scale=alt.Scale(range=[color_hex, "#e0e0e0"]), legend=None)
            ).properties(width=80, height=80)
            return chart

        with k1:
            pct_r = int((tot_r / tot_u * 100) if tot_u > 0 else 0)
            c_m, c_c = st.columns([2, 1])
            with c_m:
                st.metric("UNIDADES RUTA", f"{tot_r} / {tot_u}", f"{pct_r}%")
            with c_c:
                st.altair_chart(make_donut(tot_r, tot_u, "Ruta", "#2e7d32"))
        with k2:
            pct_s = int((tot_s / tot_u * 100) if tot_u > 0 else 0)
            c_m, c_c = st.columns([2, 1])
            with c_m:
                st.metric("UNIDADES SEDE", f"{tot_s} / {tot_u}", f"{pct_s}%")
            with c_c:
                st.altair_chart(make_donut(tot_s, tot_u, "Sede", "#1976d2"))
        with k3:
            pct_t = int((tot_t / tot_u * 100) if tot_u > 0 else 0)
            c_m, c_c = st.columns([2, 1])
            with c_m:
                st.metric("UNIDADES TALLER", f"{tot_t} / {tot_u}", f"{pct_t}%")
            with c_c:
                st.altair_chart(make_donut(tot_t, tot_u, "Taller", "#f57c00"))
        with k4:
            pct_gps = int((tot_gps / tot_u * 100) if tot_u > 0 else 0)
            c_m, c_c = st.columns([2, 1])
            with c_m:
                st.metric("FALLAS GPS", f"{tot_gps} / {tot_u}", f"{pct_gps}%")
            with c_c:
                st.altair_chart(make_donut(tot_gps, tot_u, "GPS", "#d32f2f"))
            
        st.markdown("---")
        
        # Middle section: Status de Flota Table + Analista Responsable Table side by side (matching sketch)
        col_table1, col_table2 = st.columns([3, 2])
        
        with col_table1:
            st.subheader("📋 Status Flota")
            display_fleet = df_fleet[["sede", "tot_unidades", "und_ruta", "und_sede", "und_taller", "fallas_gps"]].copy()
            display_fleet.columns = ["Sede", "Tot. U.", "Ruta", "Sede", "Taller", "GPS"]
            st.dataframe(display_fleet, use_container_width=True, hide_index=True)
            
        with col_table2:
            st.subheader("👤 Analistas Responsables")
            display_analyst = df_fleet[["sede", "analista"]].copy()
            display_analyst.columns = ["Sede", "Analista Responsable"]
            st.dataframe(display_analyst, use_container_width=True, hide_index=True)
            
        # Bottom section: Unidades Viajeras & Novedades (matching sketch)
        col_bot1, col_bot2 = st.columns(2)
        with col_bot1:
            st.subheader("🚚 Unidades Viajeras")
            if not df_travel.empty:
                st.dataframe(df_travel[["unidad", "conductor", "desde", "hasta", "sede_resp"]], use_container_width=True, hide_index=True)
            else:
                st.info("Sin unidades viajeras.")
                
        with col_bot2:
            st.subheader("⚠️ Novedades Resaltantes")
            if not df_nov.empty:
                for idx, row in df_nov.iterrows():
                    st.markdown(f"• {row['novedad']}")
            else:
                st.info("Sin novedades.")

        st.markdown("---")
        
        # PDF Generation Button
        if st.button("📄 Generar Reporte PDF Ejecutivo", type="primary"):
            html_content = f"""<!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4 portrait; margin: 12mm; background-color: #fafdfa; }}
                body {{ font-family: Helvetica, Arial, sans-serif; color: #1b4d3e; margin: 0; padding: 0; font-size: 10pt; }}
                h1 {{ font-size: 16pt; text-align: center; margin-bottom: 5px; color: #1b4d3e; }}
                .subtitle {{ text-align: center; font-size: 10pt; color: #555; margin-bottom: 20px; }}
                .kpi-container {{ width: 100%; margin-bottom: 15px; }}
                .kpi-box {{ display: inline-block; width: 23%; background: #ffffff; border: 1px solid #c8e6c9; border-radius: 6px; padding: 8px; text-align: center; box-sizing: border-box; }}
                .kpi-title {{ font-size: 8pt; font-weight: bold; color: #333; }}
                .kpi-val {{ font-size: 12pt; font-weight: bold; color: #1b4d3e; margin-top: 4px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 9pt; }}
                th {{ background-color: #1b4d3e; color: #ffffff; text-align: left; padding: 6px; }}
                td {{ border: 1px solid #c8e6c9; padding: 6px; }}
                tr:nth-child(even) {{ background-color: #f1f8f1; }}
                .section-title {{ font-size: 12pt; font-weight: bold; margin-top: 15px; margin-bottom: 8px; border-bottom: 2px solid #1b4d3e; padding-bottom: 3px; }}
            </style>
            </head>
            <body>
                <h1>REPORTE OPERATIVO MONITOREO Y GPS</h1>
                <div class="subtitle">Semana: {selected_week} &nbsp;|&nbsp; Fecha: {datetime.date.today()}</div>
                
                <div class="section-title">1. Indicadores Generales de Flota</div>
                <div class="kpi-container">
                    <div class="kpi-box"><div class="kpi-title">Ruta</div><div class="kpi-val">{tot_r} / {tot_u} ({pct_r}%)</div></div>
                    <div class="kpi-box"><div class="kpi-title">Sede</div><div class="kpi-val">{tot_s} / {tot_u} ({pct_s}%)</div></div>
                    <div class="kpi-box"><div class="kpi-title">Taller</div><div class="kpi-val">{tot_t} / {tot_u} ({pct_t}%)</div></div>
                    <div class="kpi-box"><div class="kpi-title">Fallas GPS</div><div class="kpi-val">{tot_gps} / {tot_u} ({pct_gps}%)</div></div>
                </div>
                
                <div class="section-title">2. Status de Flota y Responsables por Sede</div>
                <table>
                    <thead>
                        <tr>
                            <th>Sede</th>
                            <th>Tot. Unid.</th>
                            <th>Und. Ruta</th>
                            <th>Und. Sede</th>
                            <th>Und. Taller</th>
                            <th>Fallas GPS</th>
                            <th>Analista Responsable</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for idx, row in df_fleet.iterrows():
                html_content += f"""
                        <tr>
                            <td>{row['sede']}</td>
                            <td>{row['tot_unidades']}</td>
                            <td>{row['und_ruta']}</td>
                            <td>{row['und_sede']}</td>
                            <td>{row['und_taller']}</td>
                            <td>{row['fallas_gps']}</td>
                            <td>{row['analista']}</td>
                        </tr>
                """
            html_content += """
                    </tbody>
                </table>
                
                <div class="section-title">3. Unidades Viajeras</div>
                <table>
                    <thead>
                        <tr>
                            <th>Unidad</th>
                            <th>Conductor</th>
                            <th>Desde</th>
                            <th>Hasta</th>
                            <th>Sede Resp.</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            if not df_travel.empty:
                for idx, row in df_travel.iterrows():
                    html_content += f"""
                        <tr>
                            <td>{row['unidad']}</td>
                            <td>{row['conductor']}</td>
                            <td>{row['desde']}</td>
                            <td>{row['hasta']}</td>
                            <td>{row['sede_resp']}</td>
                        </tr>
                    """
            else:
                html_content += "<tr><td colspan='5' style='text-align: center;'>Sin unidades viajeras registradas.</td></tr>"
            
            html_content += """
                    </tbody>
                </table>
                
                <div class="section-title">4. Novedades Resaltantes</div>
                <ul>
            """
            if not df_nov.empty:
                for idx, row in df_nov.iterrows():
                    html_content += f"<li>{row['novedad']}</li>"
            else:
                html_content += "<li>Sin novedades registradas.</li>"
                
            html_content += """
                </ul>
            </body>
            </html>
            """
            
            pdf_path = "reporte_operativo_fospuca.pdf"
            HTML(string=html_content).write_pdf(pdf_path)
            st.success("¡Reporte PDF generado exitosamente!")
            
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="📥 Descargar PDF Generado",
                    data=pdf_file,
                    file_name="Reporte_Operativo_Fospuca.pdf",
                    mime="application/pdf"
                )

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
