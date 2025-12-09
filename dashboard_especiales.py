# -*- coding: utf-8 -*-
# dashboard_especiales.py
# Dashboard completo con CSS pastel animado, consultas SQL y gráficas transparentes.
# Reemplaza "(contraseña)" o el PWD vacío con tu contraseña real antes de ejecutar.

import urllib
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime

import dash
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# --------------------------------------------------
# CONEXIÓN SQL
# --------------------------------------------------
def obtener_conexion():
    import os

    DB_PWD = os.environ.get("DB_PWD", "")  # Render, GitHub Actions o tu PC pondrán la contraseña

    params = urllib.parse.quote_plus(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=10.1.1.214;"
        "DATABASE=Neotel;"
        "UID=MIS_CesarGR;"
        f"PWD={DB_PWD};"
    )

    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    return engine


# --------------------------------------------------
# CONSULTAS Y FUNCIONES
# --------------------------------------------------
def obtener_trafico():
    query = """
    ;WITH BASE AS (
        SELECT *,
            CASE 
                WHEN DNIS = '5550059224' THEN 'HERDEZ FOOD IVR'
                WHEN DNIS = '5550059285' THEN 'HERDEZ CORPORATIVO'
                WHEN DNIS = '5550059213' THEN 'HERDEZ CONFIANZA'
                WHEN DNIS = '5547372149' THEN 'CRUZ AZUL'
                WHEN DNIS = '5550059273' THEN 'CONFIANZA LIBERTAD'
                WHEN DNIS = '5550059281' THEN 'HOY COBRO'
                WHEN DNIS = '524427463582' THEN 'LIBERTAD REVOLVENTE 360'
                WHEN DNIS = '5542112905' THEN 'EGLOBAL'
                WHEN DNIS = '524429198123' THEN 'LIBERTAD'
                WHEN DNIS = '4429198246' THEN 'LIBERTAD ATC'
                WHEN DNIS = '524427463439' THEN 'LIBERTAD INVERSION'
                ELSE 'SIN CAMPAÑA'
            END AS CAMPANA_ASIGNADA,
            CASE WHEN DIRECCION = 'ENTRANTE' THEN 1 ELSE 0 END AS RECIBIDAS,
            CASE WHEN DIRECCION = 'ENTRANTE' AND LLAMADA_ABANDONADA = 'NO' THEN 1 ELSE 0 END AS CONTESTADAS,
            CASE WHEN DIRECCION = 'ENTRANTE' AND LLAMADA_ABANDONADA = 'SI' THEN 1 ELSE 0 END AS ABANDONADAS,
            (ISNULL(TIEMPO_EN_COLA,0) + ISNULL(TIEMPO_DE_TIMBRADO,0)) AS ASA_BRUTO,
            (ISNULL(TIEMPO_DE_CONVERSACION,0) + ISNULL(TIEMPO_DE_TIPIFICACIÓN,0)) AS AHT_BRUTO
        FROM LLAMADAS_ESPECIALES_ECD
        WHERE CAST(FECHA AS DATE) BETWEEN '2025-12-01' AND '2025-12-08'
            AND DIRECCION = 'ENTRANTE'
            AND FUERA_DE_HORARIO = 'Inside'
            AND (SUB_CATEGORIA NOT LIKE '%Llamada de Prueba%' OR SUB_CATEGORIA IS NULL)
            AND CAMPAÑA NOT IN ('LIBERTAD', 'EGLOBAL', 'ASSISTANCE')
            AND ISNULL(TIEMPO_EN_IVR,0) <> 0
            AND DNIS <> '5542112905'  -- filtro en SQL para omitir EGLOBAL
    )
    SELECT INTERVALO,
           SUM(RECIBIDAS) AS RECIBIDAS,
           SUM(CONTESTADAS) AS CONTESTADAS,
           SUM(ABANDONADAS) AS ABANDONADAS,
           CASE WHEN SUM(CONTESTADAS) > 0 THEN SUM(CASE WHEN CONTESTADAS = 1 THEN ASA_BRUTO ELSE 0 END) * 1.0 / SUM(CONTESTADAS) END AS ASA,
           CASE WHEN SUM(CONTESTADAS) > 0 THEN SUM(AHT_BRUTO) * 1.0 / SUM(CONTESTADAS) END AS AHT,
           SUM(CASE WHEN CONTESTADAS = 1 AND ASA_BRUTO <= 20 THEN 1 ELSE 0 END) AS ATENDIDAS_20S,
           CASE WHEN SUM(RECIBIDAS) > 0 THEN SUM(ABANDONADAS) * 1.0 / SUM(RECIBIDAS) END AS PORC_ABA,
           CASE WHEN SUM(CONTESTADAS) > 0 THEN SUM(CASE WHEN ASA_BRUTO <= 20 THEN 1 ELSE 0 END) * 1.0 / SUM(CONTESTADAS) END AS PORC_SLA
    FROM BASE
    GROUP BY INTERVALO
    ORDER BY INTERVALO;
    """
    try:
        engine = obtener_conexion()
        df = pd.read_sql(query, engine)

        # Refuerzo en Python: si por alguna razón no filtró en SQL, eliminar DNIS = '5542112905'
        if "DNIS" in df.columns:
            df = df[df["DNIS"].astype(str) != "5542112905"]
        # también eliminar cualquier fila cuyo CAMPANA_ASIGNADA sea 'EGLOBAL' por seguridad
        if "CAMPANA_ASIGNADA" in df.columns:
            df = df[~df["CAMPANA_ASIGNADA"].astype(str).str.upper().str.contains("EGLOBAL", na=False)]

        return df
    except Exception as e:
        print("Error obtener_trafico():", e)
        cols = ["INTERVALO","RECIBIDAS","CONTESTADAS","ABANDONADAS","ASA","AHT","ATENDIDAS_20S","PORC_ABA","PORC_SLA"]
        return pd.DataFrame(columns=cols)

def obtener_resumen_campanas():
    query = """
    SELECT 
        CASE 
            WHEN DNIS = '5550059224' THEN 'HERDEZ FOOD IVR'
            WHEN DNIS = '5550059285' THEN 'HERDEZ CORPORATIVO'
            WHEN DNIS = '5550059213' THEN 'HERDEZ CONFIANZA'
            WHEN DNIS = '5547372149' THEN 'CRUZ AZUL'
            WHEN DNIS = '5550059273' THEN 'CONFIANZA LIBERTAD'
            WHEN DNIS = '5550059281' THEN 'HOY COBRO'
            WHEN DNIS = '524427463582' THEN 'LIBERTAD REVOLVENTE 360'
            WHEN DNIS = '5542112905' THEN 'EGLOBAL'
            WHEN DNIS = '524429198123' THEN 'LIBERTAD'
            WHEN DNIS = '4429198246' THEN 'LIBERTAD ATC'
            WHEN DNIS = '524427463439' THEN 'LIBERTAD INVERSION'
            ELSE 'SIN CAMPAÑA'
        END AS CAMPANA,
        COUNT(*) AS INTERACCIONES
    FROM LLAMADAS_ESPECIALES_ECD
   WHERE CAST(FECHA AS DATE) BETWEEN '2025-12-01' AND '2025-12-08'
      AND DIRECCION = 'ENTRANTE'
      AND ISNULL(TIEMPO_EN_IVR,0) <> 0
      AND DNIS <> '5542112905'  -- filtro en SQL para omitir EGLOBAL
    GROUP BY DNIS
    ORDER BY INTERACCIONES ASC;
    """
    try:
        engine = obtener_conexion()
        df = pd.read_sql(query, engine)

        # seguridad extra en Python
        if "CAMPANA" in df.columns:
            df = df[~df["CAMPANA"].astype(str).str.upper().str.contains("EGLOBAL", na=False)]

        return df
    except Exception as e:
        print("Error obtener_resumen_campanas():", e)
        return pd.DataFrame(columns=["CAMPANA","INTERACCIONES"])

def obtener_datos_agentes():
    query = """
    SELECT ULTIMO_AGENTE, COUNT(*) AS INTERACCIONES
    FROM LLAMADAS_ESPECIALES_ECD
   WHERE CAST(FECHA AS DATE) BETWEEN '2025-12-01' AND '2025-12-08'
      AND DIRECCION = 'ENTRANTE'
      AND LLAMADA_ABANDONADA = 'NO'
      AND ISNULL(TIEMPO_EN_IVR,0) <> 0
      AND DNIS <> '5542112905'  -- filtro en SQL para omitir EGLOBAL
    GROUP BY ULTIMO_AGENTE
    ORDER BY INTERACCIONES DESC;
    """
    try:
        engine = obtener_conexion()
        df = pd.read_sql(query, engine)

        df["ULTIMO_AGENTE"] = df["ULTIMO_AGENTE"].astype(str)

        catalogo_agentes = pd.DataFrame({
            "ID_CONEXION": [4245,6873,10009,11757,11810,11914,12584,12620,14264,14494,15339,16834,16939,17852,50604,80102,90088],
            "NOMBRE": [
                "DOMINGUEZ GONZALEZ AMELLALY ANDREA",
                "MARIN PEÑARANDA KELLY YUREINNY",
                "ALCALA BARRERA ELIZABETH",
                "FUENTES OSNAYA MAGALY JOCELINE",
                "MIRANDA SANTIAGO NORMA ANGELICA",
                "GALICIA GARCIA KARLA CLAUDIA",
                "CARRASCO JUAN ALEYDA MONSERRAT",
                "CASTILLO GARCIA LIZBETH",
                "AVILES MARTINEZ LETICIA",
                "CADENA RUIZ ESPARZA MARIA DE LOURDES",
                "LOPEZ MALAGON MITZI AMARILLIS",
                "TRUJILLO LUNA OSCAR",
                "RUIZ ZAVALA JESSICA MARGARITA",
                "BERDEJO FLORES PATRICIA",
                "MENDEZ DE LA LUZ MARIA FERNANDA",
                "AGUIRRE NAVA KENIA ANGELICA",
                "TROVAMALA VILLAVICENCIO ISABEL"
            ]
        })
        catalogo_agentes["ID_CONEXION"] = catalogo_agentes["ID_CONEXION"].astype(str)

        df = df.merge(catalogo_agentes, left_on="ULTIMO_AGENTE", right_on="ID_CONEXION", how="left")
        df["NOMBRE"].fillna(df["ULTIMO_AGENTE"], inplace=True)

        return df[["NOMBRE", "INTERACCIONES"]]
    except Exception as e:
        print("Error obtener_datos_agentes():", e)
        return pd.DataFrame(columns=["NOMBRE","INTERACCIONES"])

def grafica_pie_agentes():
    df_ag = obtener_datos_agentes()
    if df_ag.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin datos de agentes", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig

    fig = go.Figure(go.Pie(
        labels=df_ag["NOMBRE"],
        values=df_ag["INTERACCIONES"],
        hoverinfo="label+percent+value",
        textinfo="label+percent",
        textposition="inside"
    ))
    fig.update_layout(
        title="Distribución de Interacciones Contestadas por Agente",
        showlegend=True,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --------------------------------------------------
# DASH APP
# --------------------------------------------------
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# CSS pastel animado y tarjetas; gráficas transparentes
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Dashboard de Tráfico Especiales ATC</title>
        {%favicon%}
        {%css%}
        <style>
            /* Fondo pastel animado */
            body {
                margin: 0;
                padding: 0;
                background: linear-gradient(45deg, #f7f3ff, #fdf7f0, #f0f9ff, #f7f0fb);
                background-size: 600% 600%;
                animation: gradientMove 18s ease infinite;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            @keyframes gradientMove {
                0% { background-position: 0% 50%; }
                25% { background-position: 50% 50%; }
                50% { background-position: 100% 50%; }
                75% { background-position: 50% 50%; }
                100% { background-position: 0% 50%; }
            }

            /* Contenedor principal */
            #main-container {
                padding: 18px;
                max-width: 1200px;
                margin: 0 auto;
            }

            /* KPI cards (suaves y pastel) */
            .kpi-card {
                background: rgba(255,255,255,0.85);
                border-radius: 14px;
                padding: 12px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(16,24,40,0.04);
                transition: transform .12s ease;
            }
            .kpi-card:hover { transform: translateY(-4px); }
            .kpi-title { font-size: 0.85rem; color:#334155; font-weight:700; }
            .kpi-value { font-size:1.4rem; color:#0f172a; font-weight:800; }

            /* Tabla */
            .dash-table-container .dash-spreadsheet-container {
                background: rgba(255,255,255,0.92);
                border-radius: 10px;
                padding: 6px;
                box-shadow: 0 6px 18px rgba(2,6,23,0.04);
            }

            .dash-table-container th {
                background: rgba(246,241,255,0.9) !important;
                color: #0f172a !important;
                font-weight: 700 !important;
            }

            .dash-table-container td {
                background: rgba(255,255,255,0.96) !important;
                color:#0f172a !important;
            }

            /* Gráficas: contenedor transparente para que solo se vea el gradiente de fondo */
            .js-plotly-plot {
                background: transparent !important;
                border-radius: 12px !important;
                padding: 6px !important;
                box-shadow: none !important;
            }

            footer { display:none; }
        </style>
    </head>
    <body>
        {%app_entry%}
        {%config%}
        {%scripts%}
        {%renderer%}
    </body>
</html>
"""

# estilos inline para layout de Dash
bg = {"backgroundColor": "transparent", "padding": "6px", "minHeight": "100vh"}
kpi_style = {
    "padding":"12px",
    "borderRadius":"12px",
    "textAlign":"center",
    "background":"white",
    "boxShadow":"0 1px 6px rgba(2,6,23,0.04)",
    "transition": "all 0.2s ease",
    "minWidth": "120px"
}

# helpers colores (pasteles)
def color_sla(p):
    try:
        p = float(p)
    except:
        p = 0
    if p >= 80: return "#d1fae5"  # pastel green
    elif p >= 70: return "#fff7ed"  # pastel yellow
    else: return "#fee2e2"  # pastel red

def color_abandono(p):
    try:
        p = float(p)
    except:
        p = 0
    if p <= 5: return "#d1fae5"
    elif p <= 9.9: return "#fff7ed"
    else: return "#fee2e2"

def color_atencion(p):
    try:
        p = float(p)
    except:
        p = 0
    if p >= 90: return "#d1fae5"
    elif p >= 80: return "#fff7ed"
    else: return "#fee2e2"

# --------------------------------------------------
# LAYOUT
# --------------------------------------------------
app.layout = html.Div(id="main-container", style=bg, children=[

    html.H1("Dashboard de Tráfico Mensual Especiales ATC", style={"textAlign":"center","color":"#4b3fbd","marginBottom":"6px"}),
    html.Div(id="ultima_actualizacion", style={"textAlign":"center","fontStyle":"italic","marginBottom":"12px","color":"#475569"}),

    # KPIs
    dbc.Row(id="kpi_cards", className="mb-3", justify="around"),

    # tabla + pastel pie
    dbc.Row([
        dbc.Col(
            html.Div(
                dash_table.DataTable(
                    id="tabla_intervalos", columns=[], data=[], page_size=10,
                    style_table={"overflowX":"auto"},
                    style_cell={"textAlign":"center","padding":"6px"}
                ), className="dash-table-container"
            ), width=8),

        dbc.Col(dcc.Graph(id="grafico_agentes", style={"height":"380px"}), width=4)
    ], className="mb-3"),

    # graficas principales
    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_intervalos", style={"height":"420px"}), width=6),
        dbc.Col(dcc.Graph(id="grafico_campanas", style={"height":"420px"}), width=6)
    ], className="mb-3"),

    dcc.Interval(id="intervalo_refresco", interval=60*1000, n_intervals=0)
])

# --------------------------------------------------
# CALLBACK (completo y funcional)
# --------------------------------------------------
@app.callback(
    [
        Output("kpi_cards", "children"),
        Output("tabla_intervalos", "columns"),
        Output("tabla_intervalos", "data"),
        Output("grafico_agentes", "figure"),
        Output("grafico_intervalos", "figure"),
        Output("grafico_campanas", "figure"),
        Output("ultima_actualizacion", "children")
    ],
    [Input("intervalo_refresco", "n_intervals")]
)
def actualizar_dashboard(n):
    # obtener datos
    df = obtener_trafico()
    df_camp = obtener_resumen_campanas()
    fig_agentes = grafica_pie_agentes()

    # si no hay datos, devolvemos placeholders
    if df is None or df.empty:
        empty_cols = []
        empty_data = []
        empty_fig = go.Figure()
        empty_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        kpis = [
            dbc.Col(html.Div([html.Div("Recibidas", className="kpi-title"), html.Div("0", className="kpi-value")], style=kpi_style, className="kpi-card"), width="auto"),
            dbc.Col(html.Div([html.Div("Contestadas", className="kpi-title"), html.Div("0", className="kpi-value")], style=kpi_style, className="kpi-card"), width="auto"),
            dbc.Col(html.Div([html.Div("Abandonadas", className="kpi-title"), html.Div("0", className="kpi-value")], style={**kpi_style, "background": color_abandono(0)}, className="kpi-card"), width="auto"),
            dbc.Col(html.Div([html.Div("% Abandono", className="kpi-title"), html.Div("0.00%", className="kpi-value")], style={**kpi_style, "background": color_abandono(0)}, className="kpi-card"), width="auto"),
            dbc.Col(html.Div([html.Div("% Atención", className="kpi-title"), html.Div("0.00%", className="kpi-value")], style={**kpi_style, "background": color_atencion(0)}, className="kpi-card"), width="auto"),
            dbc.Col(html.Div([html.Div("% SLA", className="kpi-title"), html.Div("0.00%", className="kpi-value")], style={**kpi_style, "background": color_sla(0)}, className="kpi-card"), width="auto"),
            dbc.Col(html.Div([html.Div("ASA (s)", className="kpi-title"), html.Div("0", className="kpi-value")], style=kpi_style, className="kpi-card"), width="auto"),
            dbc.Col(html.Div([html.Div("AHT (s)", className="kpi-title"), html.Div("0", className="kpi-value")], style=kpi_style, className="kpi-card"), width="auto"),
        ]
        return kpis, empty_cols, empty_data, empty_fig, empty_fig, empty_fig, f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # Normaliza columnas numéricas
    for col in ["RECIBIDAS","CONTESTADAS","ABANDONADAS","ATENDIDAS_20S","ASA","AHT","PORC_ABA","PORC_SLA"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0

    df["ASA"] = df["ASA"].round(0)
    df["AHT"] = df["AHT"].round(0)

    total_rec = int(df["RECIBIDAS"].sum())
    total_con = int(df["CONTESTADAS"].sum())
    total_aba = int(df["ABANDONADAS"].sum())
    total_20 = int(df["ATENDIDAS_20S"].sum())

    porc_aba = (total_aba / total_rec) * 100 if total_rec > 0 else 0
    porc_atencion = (total_con / total_rec) * 100 if total_rec > 0 else 0
    porc_sla = (total_20 / total_con) * 100 if total_con > 0 else 0

    try:
        if df["CONTESTADAS"].sum() > 0:
            asa_prom = (df["ASA"] * df["CONTESTADAS"]).sum() / df["CONTESTADAS"].sum()
            aht_prom = (df["AHT"] * df["CONTESTADAS"]).sum() / df["CONTESTADAS"].sum()
        else:
            asa_prom = 0
            aht_prom = 0
    except Exception:
        asa_prom = 0
        aht_prom = 0

    asa_prom = round(asa_prom, 0)
    aht_prom = round(aht_prom, 0)

    # KPI cards
    kpis = [
        dbc.Col(html.Div([html.Div("Recibidas", className="kpi-title"), html.Div(f"{total_rec:,}", className="kpi-value")], style=kpi_style, className="kpi-card"), width="auto"),
        dbc.Col(html.Div([html.Div("Contestadas", className="kpi-title"), html.Div(f"{total_con:,}", className="kpi-value")], style=kpi_style, className="kpi-card"), width="auto"),
        dbc.Col(html.Div([html.Div("Abandonadas", className="kpi-title"), html.Div(f"{total_aba:,}", className="kpi-value")], style={**kpi_style, "background": color_abandono(porc_aba)}, className="kpi-card"), width="auto"),
        dbc.Col(html.Div([html.Div("% Abandono", className="kpi-title"), html.Div(f"{porc_aba:.2f}%", className="kpi-value")], style={**kpi_style, "background": color_abandono(porc_aba)}, className="kpi-card"), width="auto"),
        dbc.Col(html.Div([html.Div("% Atención", className="kpi-title"), html.Div(f"{porc_atencion:.2f}%", className="kpi-value")], style={**kpi_style, "background": color_atencion(porc_atencion)}, className="kpi-card"), width="auto"),
        dbc.Col(html.Div([html.Div("% SLA", className="kpi-title"), html.Div(f"{porc_sla:.2f}%", className="kpi-value")], style={**kpi_style, "background": color_sla(porc_sla)}, className="kpi-card"), width="auto"),
        dbc.Col(html.Div([html.Div("ASA (s)", className="kpi-title"), html.Div(f"{int(asa_prom):,}", className="kpi-value")], style=kpi_style, className="kpi-card"), width="auto"),
        dbc.Col(html.Div([html.Div("AHT (s)", className="kpi-title"), html.Div(f"{int(aht_prom):,}", className="kpi-value")], style=kpi_style, className="kpi-card"), width="auto"),
    ]

    # tabla
    df_tabla = df.copy()
    if "ASA" in df_tabla.columns:
        df_tabla["ASA"] = df_tabla["ASA"].astype(int)
    if "AHT" in df_tabla.columns:
        df_tabla["AHT"] = df_tabla["AHT"].astype(int)

    columnas_int = [{"name": c, "id": c} for c in df_tabla.columns]
    datos_int = df_tabla.to_dict("records")

    # parseo seguro para porcentajes (0..1)
    def parse_pct_value(x):
        try:
            if x is None:
                return 0.0
            if isinstance(x, (int, float)):
                return float(x)
            s = str(x).strip()
            if s.endswith("%"):
                s = s.replace("%","")
                return float(s)/100.0
            return float(s)
        except Exception:
            return 0.0

    porc_aba_list = [parse_pct_value(x) for x in df.get("PORC_ABA", [0]*len(df))]
    porc_sla_list = [parse_pct_value(x) for x in df.get("PORC_SLA", [0]*len(df))]

    # gráficos intervalos (transparentes)
    x_inter = df["INTERVALO"] if "INTERVALO" in df.columns else list(range(len(df)))
    y_cont = df["CONTESTADAS"] if "CONTESTADAS" in df.columns else [0]*len(x_inter)
    y_aban = df["ABANDONADAS"] if "ABANDONADAS" in df.columns else [0]*len(x_inter)

    fig_int = go.Figure()
    fig_int.add_trace(go.Bar(
        x=x_inter, y=y_cont,
        name="Contestadas",
        text=y_cont, textposition="auto",
        marker_color="#6B46C1"
    ))
    fig_int.add_trace(go.Bar(
        x=x_inter, y=y_aban,
        name="Abandonadas",
        text=y_aban, textposition="auto",
        marker_color="#FB7185"
    ))
    fig_int.add_trace(go.Scatter(
        x=x_inter, y=porc_aba_list,
        name="% Abandono",
        mode="lines+markers+text",
        text=[f"{v*100:.1f}%" for v in porc_aba_list],
        textposition="top center",
        marker=dict(size=7),
        yaxis="y2"
    ))
    fig_int.add_trace(go.Scatter(
        x=x_inter, y=porc_sla_list,
        name="% SLA",
        mode="lines+markers+text",
        text=[f"{v*100:.1f}%" for v in porc_sla_list],
        textposition="top center",
        marker=dict(size=7),
        yaxis="y2"
    ))

    fig_int.update_layout(
        title="Tráfico y KPIs por Intervalo",
        barmode="stack",
        yaxis_title="Cantidad de llamadas",
        yaxis2=dict(title="Porcentaje", overlaying="y", side="right", tickformat=".0%"),
        legend=dict(x=0.01, y=0.99),
        plot_bgcolor="rgba(0,0,0,0)",   # transparente
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=60)
    )

    # gráfica campañas (transparent)
    if not df_camp.empty:
        df_camp_sorted = df_camp.sort_values("INTERACCIONES", ascending=True)
        fig_camp = go.Figure(go.Bar(
            x=df_camp_sorted["INTERACCIONES"],
            y=df_camp_sorted["CAMPANA"],
            orientation="h",
            text=df_camp_sorted["INTERACCIONES"],
            textposition="outside",
            marker_color="#A78BFA"
        ))
        fig_camp.update_layout(
            title="Interacción por Campaña (Ascendente)", yaxis={'automargin': True},
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=60)
        )
    else:
        fig_camp = go.Figure()
        fig_camp.update_layout(title="Sin datos de campaña", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")

    actualizacion = f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return kpis, columnas_int, datos_int, fig_agentes, fig_int, fig_camp, actualizacion

# --------------------------------------------------
# EJECUTAR
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8051)