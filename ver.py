import base64
import datetime
import io
import re
import sqlite3
import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

DB_FILE = "fospuca_operativoxox.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute("""
        CREATE TABLE IF NOT EXISTS fleet_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            week TEXT,
            turno TEXT,
            sede TEXT,
            tot_unidades INTEGER,
            und_ruta INTEGER,
            und_sede INTEGER,
            und_taller INTEGER,
            fallas_gps INTEGER,
            analista TEXT,
            timestamp TEXT
        )
    """)
  c.execute("""
        CREATE TABLE IF NOT EXISTS travel_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            week TEXT,
            turno TEXT,
            unidad TEXT,
            conductor TEXT,
            desde TEXT,
            hasta TEXT,
            sede_resp TEXT,
            timestamp TEXT
        )
    """)
  c.execute("""
        CREATE TABLE IF NOT EXISTS novedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            week TEXT,
            turno TEXT,
            novedad TEXT,
            timestamp TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()

st.set_page_config(
    page_title="Reporte Operativo",
    layout="wide",
    page_icon="🟢",
)
st.markdown("### REPORTE OPERATIVO MONITOREO & GPS")
st.markdown("---")

st.sidebar.header("⚙️ Panel de Control")
menu = st.sidebar.selectbox(
    "Seleccione Vista",
    [
        "📊 Dashboard en Vivo",
        "📝 Registro de Datos",
        "⚡ Carga de Data Inteligente",
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

UNIDADES_TOTALES_SEDE = {
    "Baruta": 58,
    "Chacao": 24,
    "Girardot": 33,
    "Hatillo": 24,
    "Iribarren": 52,
    "Maneiro": 17,
    "Maracaibo": 67,
    "San Diego": 23,
}

LISTA_ANALISTAS = [
    "ANGLY VILLALOBOS",
    "ANGEL PEÑA",
    "CARLOS GONZALEZ",
    "CRISTIAN SUAREZ",
    "CRISTOFER LUGO",
    "DANAE FIGUEROA",
    "ENRIQUE VILORIA",
    "GABRIELA AZUAJE",
    "HUGO AREVALO",
    "JAVIER MOLINA",
    "JOHNATAN OCHOA",
    "JOSE RAMIREZ",
    "JOSE SANDOVAL",
    "JOSE MANUEL SALAZAR",
    "JOSETH CARDOZA",
    "JULIO DOMINGUEZ",
    "KARELIS BERMUDEZ",
    "OSCAR IBARRA",
    "PETER BARRIOS",
    "RICARDO MORAO",
]

now = datetime.datetime.now()
today = now.date()
current_time_str = now.strftime("%H:%M:%S")
current_timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
iso_year, iso_week, _ = today.isocalendar()
default_week_str = f"Semana {iso_week} - {iso_year}"

if menu == "📝 Registro de Datos":
  st.subheader("📝 Cargar o Modificar Reporte Operativo")

  conn_check = sqlite3.connect(DB_FILE)
  df_todos_registros = pd.read_sql(
      "SELECT DISTINCT date, turno, timestamp FROM fleet_status ORDER BY date"
      " DESC",
      conn_check,
  )
  conn_check.close()

  modo_operacion = "Nuevo Registro"

  if not df_todos_registros.empty:
    opciones_modo = ["Registrar Nuevo Turno", "Modificar Registro Existente"]
    elegido = st.radio(
        "Seleccione qué desea hacer:", opciones_modo, horizontal=True
    )

    if elegido == "Modificar Registro Existente":
      modo_operacion = "Modificar"
      df_todos_registros["label"] = (
          df_todos_registros["date"]
          + " - Turno: "
          + df_todos_registros["turno"]
          + " (Guardado: "
          + df_todos_registros["timestamp"]
          + ")"
      )
      reg_elegido_label = st.selectbox(
          "Seleccione el registro a modificar:",
          df_todos_registros["label"].tolist(),
      )
      if reg_elegido_label:
        row_match = df_todos_registros[
            df_todos_registros["label"] == reg_elegido_label
        ].iloc[0]
        report_date = datetime.datetime.strptime(
            row_match["date"], "%Y-%m-%d"
        ).date()
        turno_automatico = row_match["turno"]
        conn_w = sqlite3.connect(DB_FILE)
        res_w = pd.read_sql(
            "SELECT week FROM fleet_status WHERE date = ? AND turno = ? LIMIT 1",
            conn_w,
            params=(str(report_date), turno_automatico),
        )
        conn_w.close()
        report_week = (
            res_w["week"].iloc[0] if not res_w.empty else default_week_str
        )
        report_time = (
            "12:01:00" if turno_automatico == "Nocturno" else "08:00:00"
        )
    else:
      col1, col2, col3 = st.columns(3)
      with col1:
        report_date = st.date_input("Fecha del Reporte", today)
      with col2:
        report_week = st.text_input("Semana", default_week_str)
      with col3:
        report_time = st.text_input("Hora Actual (HH:MM:SS)", current_time_str)

      turno_automatico = "Diurno"
      try:
        t_parsed = datetime.datetime.strptime(report_time, "%H:%M:%S").time()
        if t_parsed > datetime.time(12, 0, 0):
          turno_automatico = "Nocturno"
      except ValueError:
        pass
  else:
    col1, col2, col3 = st.columns(3)
    with col1:
      report_date = st.date_input("Fecha del Reporte", today)
    with col2:
      report_week = st.text_input("Semana", default_week_str)
    with col3:
      report_time = st.text_input("Hora Actual (HH:MM:SS)", current_time_str)

    turno_automatico = "Diurno"
    try:
      t_parsed = datetime.datetime.strptime(report_time, "%H:%M:%S").time()
      if t_parsed > datetime.time(12, 0, 0):
        turno_automatico = "Nocturno"
    except ValueError:
      pass

  if modo_operacion == "Modificar":
    st.info(
        f"🛠️ Modificando registro para la fecha: **{report_date}** | Turno:"
        f" **{turno_automatico}**"
    )
  else:
    st.info(
        f"🕒 Hora ingresada detectada: **{report_time}** ➔ Turno asignado"
        f" automáticamente: **{turno_automatico}**"
    )

  conn_val = sqlite3.connect(DB_FILE)
  df_existente = pd.read_sql(
      "SELECT * FROM fleet_status WHERE date = ? AND turno = ?",
      conn_val,
      params=(str(report_date), turno_automatico),
  )
  conn_val.close()

  bloqueado = False
  tiempo_transcurrido_str = ""

  if not df_existente.empty and "timestamp" in df_existente.columns:
    ultimo_ts_str = df_existente["timestamp"].dropna().max()
    if ultimo_ts_str:
      try:
        ultimo_dt = datetime.datetime.strptime(
            ultimo_ts_str, "%Y-%m-%d %H:%M:%S"
        )
        ahora_dt = datetime.datetime.now()
        diferencia = ahora_dt - ultimo_dt
        horas_transcurridas = diferencia.total_seconds() / 3600

        if horas_transcurridas >= 5:
          bloqueado = True
          h_t = int(horas_transcurridas)
          m_t = int((horas_transcurridas - h_t) * 60)
          tiempo_transcurrido_str = f"{h_t} horas y {m_t} minutos"
      except Exception:
        pass

  if bloqueado:
    st.error(
        f"🔒 **Modificación Bloqueada:** Ya han transcurrido"
        f" **{tiempo_transcurrido_str}** (más de las 5 horas permitidas) desde"
        f" que se guardó este registro. Ya no es posible realizar cambios."
    )
  else:
    if not df_existente.empty:
      st.warning(
          "⚠️ **Ventana de Modificación Activa:** Este registro fue guardado"
          f" hace menos de 5 horas ({tiempo_transcurrido_str} aprox.). Puede"
          " modificar los datos y guardar los cambios."
      )
    else:
      st.success(
          "✨ No hay registros previos para este turno. Puede proceder a"
          " ingresar los datos."
      )

    st.markdown("### 1. Estatus de Flota y Asignación de Analistas por Sede")

    valores_previos = {}
    if not df_existente.empty:
      for _, row in df_existente.iterrows():
        valores_previos[row["sede"]] = {
            "tot": row["tot_unidades"],
            "ruta": row["und_ruta"],
            "sede": row["und_sede"],
            "taller": row["und_taller"],
            "gps": row["fallas_gps"],
            "analista": row["analista"],
        }

    with st.form("fleet_form"):
      fleet_data = []
      for sede in SEDES_DEFAULT:
        tot_predefinido = UNIDADES_TOTALES_SEDE.get(sede, 10)
        p_data = valores_previos.get(sede, {})

        def_analista = p_data.get("analista", LISTA_ANALISTAS[0])
        def_tot = p_data.get("tot", tot_predefinido)
        def_ruta = p_data.get("ruta", 7)
        def_sede = p_data.get("sede", 2)
        def_taller = p_data.get("taller", 1)
        def_gps = p_data.get("gps", 0)

        try:
          idx_analista = LISTA_ANALISTAS.index(def_analista)
        except ValueError:
          idx_analista = 0

        c_analista, c_tot, c1, c2, c3, c4 = st.columns([2, 1, 1, 1, 1, 1])
        with c_analista:
          analista_seleccionado = st.selectbox(
              f"Analista ({sede})",
              LISTA_ANALISTAS,
              index=idx_analista,
              key=f"an_{sede}",
          )
        with c_tot:
          st.markdown(f"**Tot ({sede})**")
          tot = st.number_input(
              f"Tot ({sede})",
              min_value=0,
              value=def_tot,
              key=f"tot_{sede}",
              label_visibility="collapsed",
          )
        with c1:
          ruta = st.number_input(
              f"En Ruta ({sede})",
              min_value=0,
              value=def_ruta,
              key=f"ruta_{sede}",
          )
        with c2:
          sede_u = st.number_input(
              f"En Sede ({sede})",
              min_value=0,
              value=def_sede,
              key=f"sed_{sede}",
          )
        with c3:
          taller = st.number_input(
              f"En Taller ({sede})",
              min_value=0,
              value=def_taller,
              key=f"tall_{sede}",
          )
        with c4:
          gps = st.number_input(
              f"Falla GPS ({sede})",
              min_value=0,
              value=def_gps,
              key=f"gps_{sede}",
          )

        fleet_data.append({
            "date": str(report_date),
            "week": report_week,
            "turno": turno_automatico,
            "sede": sede,
            "tot_unidades": tot,
            "und_ruta": ruta,
            "und_sede": sede_u,
            "und_taller": taller,
            "fallas_gps": gps,
            "analista": analista_seleccionado,
            "timestamp": current_timestamp_str,
        })

      submitted_fleet = st.form_submit_button("Guardar / Actualizar Estatus")
      if submitted_fleet:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            "DELETE FROM fleet_status WHERE date = ? AND turno = ?",
            (str(report_date), turno_automatico),
        )
        for item in fleet_data:
          c.execute(
              """
                      INSERT INTO fleet_status (date, week, turno, sede, tot_unidades, und_ruta, und_sede, und_taller, fallas_gps, analista, timestamp)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                  """,
              (
                  item["date"],
                  item["week"],
                  item["turno"],
                  item["sede"],
                  item["tot_unidades"],
                  item["und_ruta"],
                  item["und_sede"],
                  item["und_taller"],
                  item["fallas_gps"],
                  item["analista"],
                  item["timestamp"],
              ),
          )
        conn.commit()
        conn.close()

        st.session_state["active_week"] = report_week
        st.session_state["active_turno"] = turno_automatico

        st.success(
            f"¡Datos guardados/actualizados exitosamente para el turno"
            f" {turno_automatico}!"
        )
        st.rerun()

    st.markdown("### 2. Unidades Viajeras y Novedades")
    col_t, col_n = st.columns(2)
    with col_t:
      with st.form("travel_form"):
        st.markdown(f"#### Registrar Unidad Viajera ({turno_automatico})")
        t_unidad = st.text_input("Código de Unidad")
        t_conductor = st.text_input("Conductor")
        t_desde = st.text_input("Desde")
        t_hasta = st.text_input("Hasta")
        t_sede_resp = st.selectbox(
            "Sede Responsable", SEDES_DEFAULT, key="trav_sede"
        )
        add_travel = st.form_submit_button("Añadir Viajera")
        if add_travel and t_unidad:
          conn = sqlite3.connect(DB_FILE)
          c = conn.cursor()
          c.execute(
              """
                      INSERT INTO travel_units (date, week, turno, unidad, conductor, desde, hasta, sede_resp, timestamp)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                  """,
              (
                  str(report_date),
                  report_week,
                  turno_automatico,
                  t_unidad,
                  t_conductor,
                  t_desde,
                  t_hasta,
                  t_sede_resp,
                  current_timestamp_str,
              ),
          )
          conn.commit()
          conn.close()

          st.session_state["active_week"] = report_week
          st.session_state["active_turno"] = turno_automatico

          st.success(
              f"Unidad {t_unidad} agregada para el turno {turno_automatico}."
          )
          st.rerun()
    with col_n:
      with st.form("novedad_form"):
        st.markdown(f"#### Registrar Novedad ({turno_automatico})")
        nov_text = st.text_area("Descripción de la Novedad o Incidencia")
        add_nov = st.form_submit_button("Registrar Novedad")
        if add_nov and nov_text:
          conn = sqlite3.connect(DB_FILE)
          c = conn.cursor()
          c.execute(
              """
                      INSERT INTO novedades (date, week, turno, novedad, timestamp)
                      VALUES (?, ?, ?, ?, ?)
                  """,
              (
                  str(report_date),
                  report_week,
                  turno_automatico,
                  nov_text,
                  current_timestamp_str,
              ),
          )
          conn.commit()
          conn.close()

          st.session_state["active_week"] = report_week
          st.session_state["active_turno"] = turno_automatico

          st.success(
              f"Novedad registrada para el turno {turno_automatico}."
          )
          st.rerun()

elif menu == "⚡ Carga de Data Inteligente":
  st.subheader("⚡ Carga de Data Inteligente mediante Texto")
  st.markdown(
      "Pegue el reporte de texto estructurado en el siguiente campo y haga clic"
      " en **Cargar y Procesar** para extraer automáticamente los campos"
      " correspondientes."
  )

  texto_ingresado = st.text_area(
      "Pegue el reporte operativo aquí:", height=250, placeholder="..."
  )

  if st.button("Cargar y Procesar"):
    if not texto_ingresado.strip():
      st.warning("Por favor, ingrese un texto válido para procesar.")
    else:

      def extraer_patron(patron, texto, grupo=1, default=""):
        match = re.search(patron, texto)
        if match:
          return match.group(grupo).strip()
        return default

      sede_extraida = extraer_patron(
          r"REPORTE OPERATIVO DE LA FLOTA\s*–\s*([^\n\r]+)", texto_ingresado
      )
      fecha_str = extraer_patron(r"Fecha:\s*([^\n\r]+)", texto_ingresado)
      turno_extraido = extraer_patron(
          r"Turno reportado:\s*([^\n\r]+)", texto_ingresado
      )
      analista_extraido = extraer_patron(
          r"Analista:\s*([^\n\r]+)", texto_ingresado
      )
      tot_unidades_str = extraer_patron(
          r"🔵\s*TOTAL UNIDADES DE LA FLOTA:\s*\(?(\d+)\]?", texto_ingresado, 1, "0"
      )
      en_ruta_str = extraer_patron(
          r"🟢\s*EN RUTA:\s*\(?(\d+)\]?", texto_ingresado, 1, "0"
      )
      en_sede_str = extraer_patron(
          r"🟡\s*EN SEDE:\s*\(?(\d+)\]?", texto_ingresado, 1, "0"
      )
      en_taller_str = extraer_patron(
          r"🔧\s*EN TALLER:\s*\[?(\d+)\]?", texto_ingresado, 1, "0"
      )
      falla_gps_str = extraer_patron(
          r"🔴\s*FALLA DE GPS:\s*\[?(\d+)\]?", texto_ingresado, 1, "0"
      )

      st.success("¡Data extraída exitosamente!")

      col_res1, col_res2 = st.columns(2)
      with col_res1:
        st.markdown(f"**Sede:** {sede_extraida}")
        st.markdown(f"**Fecha:** {fecha_str}")
        st.markdown(f"**Turno:** {turno_extraido}")
        st.markdown(f"**Analista:** {analista_extraido}")
        st.markdown(f"**Total Unidades:** {tot_unidades_str}")
      with col_res2:
        st.markdown(f"**En Ruta:** {en_ruta_str}")
        st.markdown(f"**En Sede:** {en_sede_str}")
        st.markdown(f"**En Taller:** {en_taller_str}")
        st.markdown(f"**Falla GPS:** {falla_gps_str}")

      st.session_state["parsed_data"] = {
          "sede": sede_extraida,
          "fecha": fecha_str,
          "turno": turno_extraido,
          "analista": analista_extraido,
          "tot": tot_unidades_str,
          "ruta": en_ruta_str,
          "sede_val": en_sede_str,
          "taller": en_taller_str,
          "gps": falla_gps_str,
      }

  if "parsed_data" in st.session_state:
    st.markdown("---")
    if st.button("Guardar"):
      data = st.session_state["parsed_data"]
      try:
        from datetime import datetime as dt

        parsed_date = dt.strptime(data["fecha"].strip(), "%d/%m/%y").date()
      except Exception:
        parsed_date = today

      turno_db = "Nocturno" if "NOCTURNO" in data["turno"].upper() else "Diurno"
      iso_y, iso_w, _ = parsed_date.isocalendar()
      w_str = f"Semana {iso_w} - {iso_y}"

      sede_db = (
          data["sede"].capitalize()
          if data["sede"].capitalize() in SEDES_DEFAULT
          else "Maneiro"
      )

      conn = sqlite3.connect(DB_FILE)
      c = conn.cursor()
      c.execute(
          "SELECT id FROM fleet_status WHERE date = ? AND turno = ? AND sede ="
          " ?",
          (str(parsed_date), turno_db, sede_db),
      )
      existe = c.fetchone()

      if existe:
        c.execute(
            """
                UPDATE fleet_status 
                SET tot_unidades = ?, und_ruta = ?, und_sede = ?, und_taller = ?, fallas_gps = ?, analista = ?, timestamp = ?
                WHERE date = ? AND turno = ? AND sede = ?
            """,
            (
                int(data["tot"]),
                int(data["ruta"]),
                int(data["sede_val"]),
                int(data["taller"]),
                int(data["gps"]),
                data["analista"],
                current_timestamp_str,
                str(parsed_date),
                turno_db,
                sede_db,
            ),
        )
      else:
        c.execute(
            """
                INSERT INTO fleet_status (date, week, turno, sede, tot_unidades, und_ruta, und_sede, und_taller, fallas_gps, analista, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(parsed_date),
                w_str,
                turno_db,
                sede_db,
                int(data["tot"]),
                int(data["ruta"]),
                int(data["sede_val"]),
                int(data["taller"]),
                int(data["gps"]),
                data["analista"],
                current_timestamp_str,
            ),
        )

      conn.commit()
      conn.close()

      st.session_state["active_week"] = w_str
      st.session_state["active_turno"] = turno_db
      del st.session_state["parsed_data"]

      st.success(
          f"¡Los datos de la sede **{sede_db}** fueron actualizados y guardados"
          " correctamente!"
      )
      st.rerun()

elif menu == "📊 Dashboard en Vivo":
  conn = sqlite3.connect(DB_FILE)
  weeks_df = pd.read_sql("SELECT DISTINCT week FROM fleet_status", conn)

  if weeks_df.empty:
    st.warning(
        "No hay datos registrados aún. Por favor, ve a la sección 'Registro de"
        " Datos' para ingresar información."
    )
  else:
    lista_semanas = weeks_df["week"].tolist()
    idx_semana = 0
    if (
        "active_week" in st.session_state
        and st.session_state["active_week"] in lista_semanas
    ):
      idx_semana = lista_semanas.index(st.session_state["active_week"])

    selected_week = st.selectbox(
        "Seleccionar Semana", lista_semanas, index=idx_semana
    )

    turnos_disponibles_live = pd.read_sql(
        "SELECT DISTINCT turno FROM fleet_status WHERE week = ?",
        conn,
        params=(selected_week,),
    )["turno"].tolist()

    if not turnos_disponibles_live:
      turnos_disponibles_live = ["Diurno", "Nocturno"]

    idx_turno = 0
    if (
        "active_turno" in st.session_state
        and st.session_state["active_turno"] in turnos_disponibles_live
    ):
      idx_turno = turnos_disponibles_live.index(
          st.session_state["active_turno"]
      )

    selected_turno_live = st.selectbox(
        "Seleccionar Turno", turnos_disponibles_live, index=idx_turno
    )

    df_fleet = pd.read_sql(
        "SELECT * FROM fleet_status WHERE week = ? AND turno = ?",
        conn,
        params=(selected_week, selected_turno_live),
    )
    df_travel = pd.read_sql(
        "SELECT * FROM travel_units WHERE week = ? AND turno = ?",
        conn,
        params=(selected_week, selected_turno_live),
    )
    df_nov = pd.read_sql(
        "SELECT * FROM novedades WHERE week = ? AND turno = ?",
        conn,
        params=(selected_week, selected_turno_live),
    )

    if df_fleet.empty:
      st.warning(
          f"No hay registros para la semana {selected_week} en el turno"
          f" {selected_turno_live}."
      )
    else:
      tot_u = df_fleet["tot_unidades"].sum()
      tot_r = df_fleet["und_ruta"].sum()
      tot_s = df_fleet["und_sede"].sum()
      tot_t = df_fleet["und_taller"].sum()
      tot_gps = df_fleet["fallas_gps"].sum()

      st.markdown(
          f"### 📊 Indicadores Generales de Flota (Turno:"
          f" {selected_turno_live})"
      )
      k1, k2, k3, k4 = st.columns(4)

      def make_donut(value, total, title, color_hex):
        source = pd.DataFrame({
            "Category": [title, "Resto"],
            "Value": [value, max(0, total - value)],
        })
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
            .properties(width=40, height=100)
        )
        return chart

      with k1:
        pct_r = int((tot_r / tot_u * 100) if tot_u > 0 else 0)
        c_m, c_c = st.columns([1, 1])
        with c_m:
          st.metric("UNIDADES RUTA", f"{tot_r} / {tot_u}", f"{pct_r}%")
        with c_c:
          st.altair_chart(make_donut(tot_r, tot_u, "Ruta", "#2e7d32"))

      with k2:
        pct_s = int((tot_s / tot_u * 100) if tot_u > 0 else 0)
        c_m, c_c = st.columns([1, 1])
        with c_m:
          st.metric("UNIDADES SEDE", f"{tot_s} / {tot_u}", f"{pct_s}%")
        with c_c:
          st.altair_chart(make_donut(tot_s, tot_u, "Sede", "#1976d2"))

      with k3:
        pct_t = int((tot_t / tot_u * 100) if tot_u > 0 else 0)
        c_m, c_c = st.columns([1, 1])
        with c_m:
          st.metric("UNIDADES TALLER", f"{tot_t} / {tot_u}", f"{pct_t}%")
        with c_c:
          st.altair_chart(make_donut(tot_t, tot_u, "Taller", "#f57c00"))

      with k4:
        pct_gps = int((tot_gps / tot_u * 100) if tot_u > 0 else 0)
        c_m, c_c = st.columns([1, 1])
        with c_m:
          st.metric("FALLAS GPS", f"{tot_gps} / {tot_u}", f"{pct_gps}%")
        with c_c:
          st.altair_chart(make_donut(tot_gps, tot_u, "GPS", "#d32f2f"))

      st.markdown("---")

      col_table1, col_table2 = st.columns([3, 2])

      with col_table1:
        st.subheader("📋 Status Flota")
        display_fleet = df_fleet[
            [
                "sede",
                "tot_unidades",
                "und_ruta",
                "und_sede",
                "und_taller",
                "fallas_gps",
            ]
        ].copy()
        display_fleet.columns = [
            "Sede",
            "Tot. U.",
            "Ruta",
            "En Sede",
            "Taller",
            "Falla GPS",
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
              .footer-signature {{ text-align: right; margin-top: 30px; font-size: 10pt; line-height: 1.4; border-top: 1px solid #b2dfdb; padding-top: 10px; }}
          </style>
          </head>
          <body>
              <div class="header-container">
                  <h1>REPORTE OPERATIVO MONITOREO Y GPS</h1>
                  <div class="meta-info">Semana: {selected_week} &nbsp;&nbsp;|&nbsp;&nbsp;|&nbsp;&nbsp; Fecha: {today} &nbsp;&nbsp;|&nbsp;&nbsp</div>
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
                      <th>Falla GPS</th>
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
              <div class="footer-signature">
                  <strong>Monitoreo & GPS</strong> - <em>Vigilancia Activa, Riesgo Cero.</em>
              </div>
          </body>
          </html>
          """

      b64 = base64.b64encode(html_report.encode()).decode()
      href = f'<a href="data:text/html;base64,{b64}" download="Reporte_Gerencial_Fospuca_{selected_turno_live}.html" style="background-color: #1b4d3e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 10px;">📥 Descargar Reporte Gerencial con Gráficos (HTML/PDF)</a>'
      st.markdown(href, unsafe_allow_html=True)

  conn.close()

elif menu == "📈 Estadísticas Históricas":
  st.subheader("📈 Análisis, Estadísticas y Consulta Histórica de Tablero")
  conn = sqlite3.connect(DB_FILE)
  df_all = pd.read_sql("SELECT * FROM fleet_status", conn)

  if df_all.empty:
    st.info("No hay suficiente información histórica.")
  else:
    st.markdown(
        "### 🔍 Consultar Histórico por Fecha Específica y Selector de Turno"
    )
    fechas_disponibles = sorted(df_all["date"].unique(), reverse=True)

    c_f1, c_f2 = st.columns(2)
    with c_f1:
      selected_date = st.selectbox(
          "Seleccione la fecha del tablero histórico", fechas_disponibles
      )

    turnos_por_fecha = pd.read_sql(
        "SELECT DISTINCT turno FROM fleet_status WHERE date = ?",
        conn,
        params=(selected_date,),
    )["turno"].tolist()

    with c_f2:
      selected_turno_hist = st.selectbox(
          "Seleccione el Turno a Consultar",
          turnos_por_fecha if turnos_por_fecha else ["Diurno", "Nocturno"],
      )

    df_fleet = pd.read_sql(
        "SELECT * FROM fleet_status WHERE date = ? AND turno = ?",
        conn,
        params=(selected_date, selected_turno_hist),
    )
    df_travel = pd.read_sql(
        "SELECT * FROM travel_units WHERE date = ? AND turno = ?",
        conn,
        params=(selected_date, selected_turno_hist),
    )
    df_nov = pd.read_sql(
        "SELECT * FROM novedades WHERE date = ? AND turno = ?",
        conn,
        params=(selected_date, selected_turno_hist),
    )

    if not df_fleet.empty:
      selected_week = df_fleet["week"].iloc[0]
      st.success(
          f"Mostrando el tablero correspondiente al día **{selected_date}** |"
          f" Turno: **{selected_turno_hist}** (Semana: **{selected_week}**)"
      )

      tot_u = df_fleet["tot_unidades"].sum()
      tot_r = df_fleet["und_ruta"].sum()
      tot_s = df_fleet["und_sede"].sum()
      tot_t = df_fleet["und_taller"].sum()
      tot_gps = df_fleet["fallas_gps"].sum()

      st.markdown("### 📊 Indicadores Generales de Flota (Histórico)")
      k1, k2, k3, k4 = st.columns(4)

      def make_donut(value, total, title, color_hex):
        source = pd.DataFrame({
            "Category": [title, "Resto"],
            "Value": [value, max(0, total - value)],
        })
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
            .properties(width=40, height=100)
        )
        return chart

      with k1:
        pct_r = int((tot_r / tot_u * 100) if tot_u > 0 else 0)
        c_m, c_c = st.columns([1, 1])
        with c_m:
          st.metric("UNIDADES RUTA", f"{tot_r} / {tot_u}", f"{pct_r}%")
        with c_c:
          st.altair_chart(make_donut(tot_r, tot_u, "Ruta", "#2e7d32"))

      with k2:
        pct_s = int((tot_s / tot_u * 100) if tot_s > 0 else 0)
        c_m, c_c = st.columns([1, 1])
        with c_m:
          st.metric("UNIDADES SEDE", f"{tot_s} / {tot_u}", f"{pct_s}%")
        with c_c:
          st.altair_chart(make_donut(tot_s, tot_u, "Sede", "#1976d2"))

      with k3:
        pct_t = int((tot_t / tot_u * 100) if tot_u > 0 else 0)
        c_m, c_c = st.columns([1, 1])
        with c_m:
          st.metric("UNIDADES TALLER", f"{tot_t} / {tot_u}", f"{pct_t}%")
        with c_c:
          st.altair_chart(make_donut(tot_t, tot_u, "Taller", "#f57c00"))

      with k4:
        pct_gps = int((tot_gps / tot_u * 100) if tot_u > 0 else 0)
        c_m, c_c = st.columns([1, 1])
        with c_m:
          st.metric("FALLAS GPS", f"{tot_gps} / {tot_u}", f"{pct_gps}%")
        with c_c:
          st.altair_chart(make_donut(tot_gps, tot_u, "GPS", "#d32f2f"))

      st.markdown("---")

      col_table1, col_table2 = st.columns([3, 2])
      with col_table1:
        st.subheader("📋 Status Flota")
        display_fleet = df_fleet[
            [
                "sede",
                "tot_unidades",
                "und_ruta",
                "und_sede",
                "und_taller",
                "fallas_gps",
            ]
        ].copy()
        display_fleet.columns = [
            "Sede",
            "Tot. U.",
            "Ruta",
            "En Sede",
            "Taller",
            "Falla GPS",
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
          st.info(
              f"Sin unidades viajeras en esta fecha para el turno"
              f" {selected_turno_hist}."
          )

      with col_bot2:
        st.subheader("⚠️ Novedades Resaltantes")
        if not df_nov.empty:
          for idx, row in df_nov.iterrows():
            st.markdown(f"• {row['novedad']}")
        else:
          st.info(
              f"Sin novedades registradas en esta fecha para el turno"
              f" {selected_turno_hist}."
          )
    else:
      st.warning(
          f"No se encontraron registros para la fecha {selected_date} en el"
          f" turno {selected_turno_hist}."
      )

    st.markdown("---")
    st.markdown("### Tendencia General por Semana")
    df_grouped = (
        df_all.groupby("week")[
            ["tot_unidades", "und_ruta", "und_sede", "und_taller", "fallas_gps"]
        ]
        .sum()
        .reset_index()
    )
    st.line_chart(df_grouped.set_index("week"))

  conn.close()
