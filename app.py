import base64
import datetime
import io
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

DB_FILE = "fospuca_operativo.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute("""
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
    """)
  c.execute("""
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
    """)
  c.execute("""
        CREATE TABLE IF NOT EXISTS novedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            week TEXT,
            novedad TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()

st.set_page_config(
    page_title="Dashboard Operativo - FOSPUCA 360",
    layout="wide",
    page_icon="🟢",
)

st.markdown(
    """
    <style>
    .main { background-color: #f4f9f4; }
    h1, h2, h3 { color: #1b4d3e; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #c8e6c9; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🟢 REPORTE OPERATIVO MONITOREO Y GPS - FOSPUCA 360")
st.markdown("---")

st.sidebar.header("⚙️ Panel de Control")
menu = st.sidebar.selectbox(
    "Seleccione Vista",
    [
        "📊 Dashboard en Vivo",
        "📝 Registro de Datos",
        "📈 Estadísticas Históricas",
    ],
)

SEDES_DEFAULT = [
    "Baruta",
    "Chacao",
    "Girardot",
    "Hatillo",
    "Iribarren",
    "Maneiro",
    "Maracaibo",
    "San Diego",
]

LISTA_ANALISTAS = [
"ANGLY JOSE VILLALOBOS SALAS",
"ANGEL EDUARDO PEÑA GUERRA",
"CARLOS JOSE GONZALEZ",
"CRISTIAN ALEJANDRO SUAREZ ALDANA",
"CRISTOFER ONEAL LUGO ALVAREZ",
"DANAE DEL VALLE FIGUEROA",
"ENRIQUE RAFAEL VILORIA MARTELO",
"GABRIELA ALEGRIA AZUAJE VILCANES",
"HUGO RAINER AREVALO DIAZ",
"JAVIER ALFONZO MOLINA GARCIAS",
"JOHNATAN DAVID OCHOA PIÑERO",
"JOSE ALEJANDRO RAMIREZ JAIME",
"JOSE GREGORIO SANDOVAL SANCHEZ",
"JOSE MANUEL ANTONIO SALAZAR VILLALBA",
"JOSETH JAVIMAR CARDOZA SILVA",
"JULIO CESAR DOMINGUEZ MARCAREÑO",
"KARELIS BELLA BERMUDEZ GARCIA",
"OSCAR RODOLFO IBARRA",
"PETER MOUSOLINE BARRIOS PADILLA",
"RICARDO MANUEL MORAO",
]

if menu == "📝 Registro de Datos":
  st.subheader("📝 Cargar o Actualizar Reporte Operativo")

  col1, col2 = st.columns(2)
  with col1:
    report_date = st.date_input("Fecha del Reporte", datetime.date.today())
  with col2:
    report_week = st.text_input("Semana", "Semana 05 - 2026")

  st.markdown("### 1. Estatus de Flota y Asignación de Analistas por Sede")
  st.info(
      "Configura los valores de unidades y selecciona el analista"
      " correspondiente a cada sede."
  )

  with st.form("fleet_form"):
    fleet_data = []
    for sede in SEDES_DEFAULT:
      c_analista, c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1, 1])
      with c_analista:
        analista_seleccionado = st.selectbox(
            f"Analista ({sede})", LISTA_ANALISTAS, key=f"an_{sede}"
        )
      with c1:
        tot = st.number_input(
            f"Tot ({sede})", min_value=0, value=10, key=f"tot_{sede}"
        )
      with c2:
        ruta = st.number_input(
            f"Ruta ({sede})", min_value=0, value=7, key=f"ruta_{sede}"
        )
      with c3:
        sede_u = st.number_input(
            f"Sede ({sede})", min_value=0, value=2, key=f"sed_{sede}"
        )
      with c4:
        taller = st.number_input(
            f"Taller ({sede})", min_value=0, value=1, key=f"tall_{sede}"
        )
      with c5:
        gps = st.number_input(
            f"GPS ({sede})", min_value=0, value=0, key=f"gps_{sede}"
        )

      fleet_data.append({
          "date": str(report_date),
          "week": report_week,
          "sede": sede,
          "tot_unidades": tot,
          "und_ruta": ruta,
          "und_sede": sede_u,
          "und_taller": taller,
          "fallas_gps": gps,
          "analista": analista_seleccionado,
      })

    submitted_fleet = st.form_submit_button("Guardar Estatus de Flota")
    if submitted_fleet:
      conn = sqlite3.connect(DB_FILE)
      c = conn.cursor()
      c.execute(
          "DELETE FROM fleet_status WHERE date = ? AND week = ?",
          (str(report_date), report_week),
      )
      for item in fleet_data:
        c.execute(
            """
                    INSERT INTO fleet_status (date, week, sede, tot_unidades, und_ruta, und_sede, und_taller, fallas_gps, analista)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
                item["date"],
                item["week"],
                item["sede"],
                item["tot_unidades"],
                item["und_ruta"],
                item["und_sede"],
                item["und_taller"],
                item["fallas_gps"],
                item["analista"],
            ),
        )
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
        c.execute(
            """
                    INSERT INTO travel_units (date, week, unidad, conductor, desde, hasta, sede_resp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
            (
                str(report_date),
                report_week,
                t_unidad,
                t_conductor,
                t_desde,
                t_hasta,
                t_sede_resp,
            ),
        )
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
        c.execute(
            """
                    INSERT INTO novedades (date, week, novedad)
                    VALUES (?, ?, ?)
                """,
            (str(report_date), report_week, nov_text),
        )
        conn.commit()
        conn.close()
        st.success("Novedad registrada.")

elif menu == "📊 Dashboard en Vivo":
  conn = sqlite3.connect(DB_FILE)
  weeks_df = pd.read_sql("SELECT DISTINCT week FROM fleet_status", conn)

  if weeks_df.empty:
    st.warning(
        "No hay datos registrados aún. Por favor, ve a la sección 'Registro de"
        " Datos' para ingresar información."
    )
  else:
    selected_week = st.selectbox(
        "Seleccionar Semana", weeks_df["week"].tolist()
    )

    df_fleet = pd.read_sql(
        "SELECT * FROM fleet_status WHERE week = ?",
        conn,
        params=(selected_week,),
    )
    df_travel = pd.read_sql(
        "SELECT * FROM travel_units WHERE week = ?",
        conn,
        params=(selected_week,),
    )
    df_nov = pd.read_sql(
        "SELECT * FROM novedades WHERE week = ?", conn, params=(selected_week,)
    )

    tot_u = df_fleet["tot_unidades"].sum()
    tot_r = df_fleet["und_ruta"].sum()
    tot_s = df_fleet["und_sede"].sum()
    tot_t = df_fleet["und_taller"].sum()
    tot_gps = df_fleet["fallas_gps"].sum()

    st.markdown("### 📊 Indicadores Generales de Flota")
    k1, k2, k3, k4 = st.columns(4)

    import altair as alt

    def make_donut(value, total, title, color_hex):
      source = pd.DataFrame(
          {"Category": [title, "Resto"], "Value": [value, max(0, total - value)]}
      )
      chart = (
          alt.Chart(source)
          .mark_arc(innerRadius=25, outerRadius=40)
          .encode(
              theta=alt.Theta(field="Value", type="quantitative"),
              color=alt.Color(
                  field="Category",
                  type="nominal",
                  scale=alt.Scale(range=[color_hex, "#e0e0e0"]),
                  legend=None,
              ),
          )
          .properties(width=80, height=80)
      )
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

    col_table1, col_table2 = st.columns([3, 2])

    with col_table1:
      st.subheader("📋 Status Flota")
      display_fleet = df_fleet[
          ["sede", "tot_unidades", "und_ruta", "und_sede", "und_taller", "fallas_gps"]
      ].copy()
      display_fleet.columns = [
          "Sede",
          "Tot. U.",
          "Ruta",
          "En Sede",
          "Taller",
          "GPS",
      ]
      st.dataframe(display_fleet, use_container_width=True, hide_index=True)

    with col_table2:
      st.subheader("👤 Analistas Responsables")
      display_analyst = df_fleet[["sede", "analista"]].copy()
      display_analyst.columns = ["Sede", "Analista Responsable"]
      st.dataframe(display_analyst, use_container_width=True, hide_index=True)

    col_bot1, col_bot2 = st.columns(2)
    with col_bot1:
      st.subheader("🚚 Unidades Viajeras")
      if not df_travel.empty:
        st.dataframe(
            df_travel[
                ["unidad", "conductor", "desde", "hasta", "sede_resp"]
            ],
            use_container_width=True,
            hide_index=True,
        )
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


    def generate_chart_base64(val, total, title, color):
      fig, ax = plt.subplots(figsize=(1.8, 1.8))
      rest = max(0, total - val)
      wedges, texts = ax.pie(
          [val, rest],
          colors=[color, "#e0e0e0"],
          startangle=90,
          wedgeprops=dict(width=0.4, edgecolor="w"),
      )
      ax.text(
          0,
          0,
          f"{int((val/total*100) if total > 0 else 0)}%",
          ha="center",
          va="center",
          fontsize=10,
          fontweight="bold",
          color="#1b4d3e",
      )
      plt.tight_layout()
      buf = io.BytesIO()
      plt.savefig(
          buf,
          format="png",
          bbox_inches="tight",
          transparent=True,
          dpi=150,
      )
      buf.seek(0)
      img_b64 = base64.b64encode(buf.read()).decode("utf-8")
      plt.close(fig)
      return img_b64


    img_ruta = generate_chart_base64(tot_r, tot_u, "Ruta", "#2e7d32")
    img_sede = generate_chart_base64(tot_s, tot_u, "Sede", "#1976d2")
    img_taller = generate_chart_base64(tot_t, tot_u, "Taller", "#f57c00")
    img_gps = generate_chart_base64(tot_gps, tot_u, "GPS", "#d32f2f")

    rows_html = ""
    for idx, row in df_fleet.iterrows():
      # Se añadieron clases CSS text-center para forzar el centrado en el reporte HTML generado
      rows_html += (
          "<tr>"
          f"<td><strong>{row['sede']}</strong></td>"
          f'<td class="text-center">{row["tot_unidades"]}</td>'
          f'<td class="text-center">{row["und_ruta"]}</td>'
          f'<td class="text-center">{row["und_sede"]}</td>'
          f'<td class="text-center">{row["und_taller"]}</td>'
          f'<td class="text-center">{row["fallas_gps"]}</td>'
          f'<td class="text-center">{row["analista"]}</td>'
          "</tr>"
      )

    travel_html = ""
    if not df_travel.empty:
      for idx, row in df_travel.iterrows():
        travel_html += (
            f"<tr><td>{row['unidad']}</td><td>{row['conductor']}</td><td>{row['desde']}</td><td>{row['hasta']}</td><td>{row['sede_resp']}</td></tr>"
        )
    else:
      travel_html = (
          "<tr><td colspan='5' style='text-align:center;"
          " color:#777;'>Sin unidades viajeras registradas.</td></tr>"
      )

    nov_html = ""
    if not df_nov.empty:
      for idx, row in df_nov.iterrows():
        nov_html += f"<li>{row['novedad']}</li>"
    else:
      nov_html = (
          "<li style='color:#777; list-style:none;'>Sin novedades registradas"
          " para este periodo.</li>"
      )

    html_report = f"""<!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <title>Reporte Operativo - FOSPUCA 360</title>
        <style>
            body {{ font-family: Arial, sans-serif; color: #1b4d3e; padding: 25px; background-color: #ffffff; }}
            .header-container {{ border-bottom: 3px solid #1b4d3e; padding-bottom: 10px; margin-bottom: 20px; }}
            h1 {{ color: #1b4d3e; font-size: 18pt; margin: 0; }}
            .meta-info {{ font-size: 10pt; color: #555; font-weight: bold; margin-top: 5px; }}
            .indicators-grid {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 25px; }}
            .card {{ flex: 1; border: 1px solid #c8e6c9; background-color: #f4f9f4; border-radius: 6px; padding: 8px; text-align: center; }}
            .card-title {{ font-size: 8pt; color: #1b4d3e; font-weight: bold; margin-bottom: 3px; }}
            .card-value {{ font-size: 11pt; font-weight: bold; color: #2e7d32; margin-top: 3px; }}
            .chart-img {{ width: 55px; height: 55px; display: block; margin: 0 auto; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #b2dfdb; padding: 6px 8px; text-align: left; font-size: 9.5pt; }}
            th {{ background-color: #1b4d3e; color: white; text-transform: uppercase; font-size: 8.5pt; text-align: center; }}
            .text-center {{ text-align: center !important; }}
            tr:nth-child(even) {{ background-color: #f9fbf9; }}
            h3 {{ color: #1b4d3e; font-size: 11pt; border-bottom: 2px solid #1b4d3e; padding-bottom: 3px; margin-top: 15px; margin-bottom: 8px; }}
            .row-split {{ display: flex; gap: 15px; }}
            .col-split {{ flex: 1; }}
            ul {{ margin: 0; padding-left: 18px; font-size: 9.5pt; }}
            li {{ margin-bottom: 4px; }}
        </style>
        </head>
        <body>
            <div class="header-container">
                <h1>REPORTE OPERATIVO MONITOREO Y GPS</h1>
                <div class="meta-info">Semana: {selected_week} &nbsp;&nbsp;|&nbsp;&nbsp; Fecha: {datetime.date.today()}</div>
            </div>
            
            <h3>Indicadores Generales de Flota</h3>
            <div class="indicators-grid">
                <div class="card">
                    <div class="card-title">UNIDADES RUTA</div>
                    <img src="data:image/png;base64,{img_ruta}" class="chart-img">
                    <div class="card-value">{tot_r} / {tot_u} <span style="font-size:9pt;">({pct_r}%)</span></div>
                </div>
                <div class="card">
                    <div class="card-title">UNIDADES SEDE</div>
                    <img src="data:image/png;base64,{img_sede}" class="chart-img">
                    <div class="card-value">{tot_s} / {tot_u} <span style="font-size:9pt;">({pct_s}%)</span></div>
                </div>
                <div class="card">
                    <div class="card-title">UNIDADES TALLER</div>
                    <img src="data:image/png;base64,{img_taller}" class="chart-img">
                    <div class="card-value">{tot_t} / {tot_u} <span style="font-size:9pt;">({pct_t}%)</span></div>
                </div>
                <div class="card">
                    <div class="card-title">FALLAS GPS</div>
                    <img src="data:image/png;base64,{img_gps}" class="chart-img">
                    <div class="card-value" style="color: #d32f2f;">{tot_gps} / {tot_u} <span style="font-size:9pt;">({pct_gps}%)</span></div>
                </div>
            </div>
            
            <h3>Status de Flota y Analistas Responsables</h3>
            <table>
                <tr>
                    <th>Sede</th>
                    <th>Tot. Unid.</th>
                    <th>Ruta</th>
                    <th>Sede</th>
                    <th>Taller</th>
                    <th>GPS</th>
                    <th>Analista Responsable</th>
                </tr>
                {rows_html}
            </table>
            
            <div class="row-split">
                <div class="col-split">
                    <h3>Unidades Viajeras</h3>
                    <table>
                        <tr><th>Unidad</th><th>Conductor</th><th>Desde</th><th>Hasta</th><th>Resp.</th></tr>
                        {travel_html}
                    </table>
                </div>
                <div class="col-split">
                    <h3>Novedades Resaltantes</h3>
                    <div style="border: 1px solid #b2dfdb; background-color: #f9fbf9; border-radius: 6px; padding: 10px; min-height: 70px;">
                        <ul>
                            {nov_html}
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    b64 = base64.b64encode(html_report.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="Reporte_Gerencial_Fospuca.html" style="background-color: #1b4d3e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 10px;">📥 Descargar Reporte Gerencial con Gráficos (HTML/PDF)</a>'
    st.markdown(href, unsafe_allow_html=True)

  conn.close()

elif menu == "📈 Estadísticas Históricas":
  st.subheader("📈 Análisis y Estadísticas de Flota")
  conn = sqlite3.connect(DB_FILE)
  df_all = pd.read_sql("SELECT * FROM fleet_status", conn)
  conn.close()

  if df_all.empty:
    st.info("No hay suficiente información histórica.")
  else:
    df_grouped = (
        df_all.groupby("week")[
            ["tot_unidades", "und_ruta", "und_sede", "und_taller", "fallas_gps"]
        ]
        .sum()
        .reset_index()
    )
    st.markdown("### Tendencia General por Semana")
    st.line_chart(df_grouped.set_index("week"))
