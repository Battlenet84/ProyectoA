import streamlit as st
from nba_stats import NBAStats
from bet_calculator import evaluar_prop_bet
from bet_scraper import BetScraper
from odds_api import ExcelOddsLoader
import pandas as pd
import re  # Agregar importación del módulo re para expresiones regulares

# Mapeo de nombres de props a columnas
prop_mapping = {
    # Estadísticas básicas
    'Puntos': 'PTS',
    'Asistencias': 'AST',
    'Rebotes': 'REB',
    'Triples': 'FG3M',
    'Robos': 'STL',
    'Tapones': 'BLK',
    'Bloqueos': 'BLK',
    'Pérdidas': 'TOV',
    'Pérdidas de balón': 'TOV',
    
    # Props combinadas - versión española
    'Puntos + Asistencias': 'PTS_AST',
    'Puntos y Asistencias': 'PTS_AST',
    'Puntos más Asistencias': 'PTS_AST',
    
    'Puntos + Rebotes': 'PTS_REB',
    'Puntos y Rebotes': 'PTS_REB',
    'Puntos más Rebotes': 'PTS_REB',
    
    'Asistencias + Rebotes': 'AST_REB',
    'Asistencias y Rebotes': 'AST_REB',
    'Asistencias más Rebotes': 'AST_REB',
    
    'Puntos + Asistencias + Rebotes': 'PTS_AST_REB',
    'Puntos, Asistencias y Rebotes': 'PTS_AST_REB',
    'Puntos más Asistencias más Rebotes': 'PTS_AST_REB',
    
    'Tapones + Robos': 'STL_BLK',
    'Tapones y Robos': 'STL_BLK',
    'Tapones más Robos': 'STL_BLK',
    'Bloqueos + Robos': 'STL_BLK',
    'Bloqueos y Robos': 'STL_BLK',
    'Bloqueos más Robos': 'STL_BLK',
    
    # Props combinadas - versión inglesa
    'Points': 'PTS',
    'Assists': 'AST',
    'Rebounds': 'REB',
    'Threes': 'FG3M',
    'Steals': 'STL',
    'Blocks': 'BLK',
    'Turnovers': 'TOV',
    
    'Points + Assists': 'PTS_AST',
    'Points and Assists': 'PTS_AST',
    'Points & Assists': 'PTS_AST',
    
    'Points + Rebounds': 'PTS_REB',
    'Points and Rebounds': 'PTS_REB',
    'Points & Rebounds': 'PTS_REB',
    
    'Assists + Rebounds': 'AST_REB',
    'Assists and Rebounds': 'AST_REB',
    'Assists & Rebounds': 'AST_REB',
    
    'Points + Assists + Rebounds': 'PTS_AST_REB',
    'Points, Assists and Rebounds': 'PTS_AST_REB',
    'Points, Assists & Rebounds': 'PTS_AST_REB',
    
    'Blocks + Steals': 'STL_BLK',
    'Blocks and Steals': 'STL_BLK',
    'Blocks & Steals': 'STL_BLK',
    
    # Versiones cortas
    'PTS': 'PTS',
    'AST': 'AST',
    'REB': 'REB',
    'FG3M': 'FG3M',
    'STL': 'STL',
    'BLK': 'BLK',
    'TOV': 'TOV',
    'PTS+AST': 'PTS_AST',
    'PTS_AST': 'PTS_AST',
    'PTS+REB': 'PTS_REB',
    'PTS_REB': 'PTS_REB',
    'AST+REB': 'AST_REB',
    'AST_REB': 'AST_REB',
    'PTS+AST+REB': 'PTS_AST_REB',
    'PTS_AST_REB': 'PTS_AST_REB',
    'STL+BLK': 'STL_BLK',
    'STL_BLK': 'STL_BLK'
}

# Inicializar el historial de apuestas en la sesión si no existe
if 'historial_apuestas' not in st.session_state:
    st.session_state.historial_apuestas = []

# Configuración de la página
st.set_page_config(
    page_title="NBA Stats Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
    .stButton>button:hover {
        background-color: #135c8d;
    }
    .stats-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
    }
    .st-emotion-cache-16txtl3 {
        padding: 2rem;
        border-radius: 0.5rem;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1, h2, h3 {
        color: #1f77b4;
    }
    .stSelectbox label {
        color: #1f77b4;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("🏀 NBA Stats Dashboard")

# Inicializar el objeto de stats con manejo de errores
try:
    nba = NBAStats()
except Exception as e:
    st.error(f"❌ Error al inicializar NBA Stats: {str(e)}")
    st.stop()

# Sidebar para selección
with st.sidebar:
    st.header("⚙️ Configuración")
    
    try:
        # Selector de temporada
        temporada_sel = st.selectbox(
            "📅 Temporada", 
            nba.obtener_lista_temporadas(),
            index=0  # Por defecto la más reciente
        )
        
        # Selector de tipos de temporada (múltiple)
        tipos_temporada_sel = st.multiselect(
            "🏆 Tipos de Temporada",
            nba.obtener_tipos_temporada(),
            default=["Regular Season"],  # Por defecto solo temporada regular
            help="Selecciona uno o más tipos de temporada para incluir en el análisis"
        )
        
        if not tipos_temporada_sel:
            st.warning("⚠️ Debes seleccionar al menos un tipo de temporada")
            st.stop()
        
        # Selector de equipo
        equipos = nba.obtener_lista_equipos()
        equipo_sel = st.selectbox("📋 Seleccionar Equipo", equipos)
        
        # Selector de equipo rival
        equipos_rivales = ["Todos los equipos"] + [equipo for equipo in equipos if equipo != equipo_sel]
        rival_sel = st.selectbox("🆚 Seleccionar Rival", equipos_rivales)
        
    except Exception as e:
        st.error(f"❌ Error en la configuración: {str(e)}")
        st.stop()

# Convertir "Todos los equipos" a None para la función
rival_param = None if rival_sel == "Todos los equipos" else [rival_sel]

# Contenido principal
if equipo_sel:
    try:
        # Título de la sección
        st.header(f"📊 Estadísticas de {equipo_sel}" + (f" vs {rival_sel}" if rival_sel != "Todos los equipos" else ""))
        st.caption(f"Temporada: {temporada_sel} ({', '.join(tipos_temporada_sel)})")
        
        with st.spinner("Cargando estadísticas..."):
            # Inicializar DataFrame vacío para acumular datos
            df_jugadores = pd.DataFrame()
            
            # Obtener datos para cada tipo de temporada seleccionado
            for tipo_temporada in tipos_temporada_sel:
                df_temp = nba.obtener_estadisticas_jugadores_equipo(
                    equipo=equipo_sel, 
                    rivales=rival_param,
                    temporada=temporada_sel,
                    tipo_temporada=tipo_temporada
                )
                
                if not df_temp.empty:
                    # Agregar columna para identificar el tipo de temporada
                    df_temp['TIPO_TEMPORADA'] = tipo_temporada
                    # Concatenar con el DataFrame principal
                    df_jugadores = pd.concat([df_jugadores, df_temp], ignore_index=True)
            
            if df_jugadores.empty:
                st.error("❌ No se encontraron datos para mostrar")
                st.write("Intente refrescar la página o seleccionar otro equipo/temporada")
                st.stop()
            
            # Agrupar por jugador y calcular promedios
            if 'PLAYER_NAME' in df_jugadores.columns:
                columnas_numericas = ['MIN', 'PTS', 'AST', 'REB', 'STL', 'BLK', 'TOV', 'FG_PCT', 'FG3_PCT', 'FT_PCT']
                columnas_numericas = [col for col in columnas_numericas if col in df_jugadores.columns]
                
                df_jugadores = df_jugadores.groupby('PLAYER_NAME')[columnas_numericas].mean().reset_index()
                
                # Crear columnas compuestas después de agrupar
                if all(col in df_jugadores.columns for col in ['PTS', 'AST']):
                    df_jugadores['PTS_AST'] = df_jugadores['PTS'] + df_jugadores['AST']
                
                if all(col in df_jugadores.columns for col in ['PTS', 'REB']):
                    df_jugadores['PTS_REB'] = df_jugadores['PTS'] + df_jugadores['REB']
                
                if all(col in df_jugadores.columns for col in ['AST', 'REB']):
                    df_jugadores['AST_REB'] = df_jugadores['AST'] + df_jugadores['REB']
                
                if all(col in df_jugadores.columns for col in ['PTS', 'AST', 'REB']):
                    df_jugadores['PTS_AST_REB'] = df_jugadores['PTS'] + df_jugadores['AST'] + df_jugadores['REB']
                
                if all(col in df_jugadores.columns for col in ['STL', 'BLK']):
                    df_jugadores['STL_BLK'] = df_jugadores['STL'] + df_jugadores['BLK']
            
            # Mostrar las columnas disponibles para debug
            st.write("Columnas disponibles:", df_jugadores.columns.tolist())
        
        if df_jugadores.empty:
            st.error("❌ No se encontraron datos para mostrar")
            st.write("Intente refrescar la página o seleccionar otro equipo/temporada")
            st.stop()
        elif 'PLAYER_NAME' not in df_jugadores.columns:
            st.error("❌ No se encontró la columna PLAYER_NAME en los datos")
            st.stop()
        
        # Crear DataFrame para mostrar estadísticas
        columnas_mostrar = {
            'PLAYER_NAME': 'Jugador',
            'GP': 'PJ',
            'MIN': 'MIN',
            'PTS': 'PTS',
            'AST': 'AST',
            'REB': 'REB',
            'STL': 'ROB',
            'BLK': 'TAP',
            'TOV': 'PER',
            'FG_PCT': 'FG%',
            'FG3_PCT': '3P%',
            'FT_PCT': 'TL%',
            'PTS_AST': 'PTS+AST',
            'PTS_REB': 'PTS+REB',
            'AST_REB': 'AST+REB',
            'PTS_AST_REB': 'PTS+AST+REB',
            'STL_BLK': 'ROB+TAP'
        }
        
        # Verificar qué columnas están disponibles
        columnas_disponibles = []
        nuevos_nombres = []
        for col_original, col_nuevo in columnas_mostrar.items():
            if col_original in df_jugadores.columns:
                columnas_disponibles.append(col_original)
                nuevos_nombres.append(col_nuevo)
        
        if not columnas_disponibles:
            st.error("❌ No se encontraron columnas válidas para mostrar")
            st.stop()
        
        # Crear DataFrame con las columnas disponibles
        df_mostrar = df_jugadores[columnas_disponibles].copy()
        df_mostrar.columns = nuevos_nombres
        
        # Formatear porcentajes y números
        for col in ['FG%', '3P%', 'TL%']:
            if col in df_mostrar.columns:
                df_mostrar[col] = df_mostrar[col].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "-")
        
        for col in ['MIN', 'PTS', 'AST', 'REB', 'ROB', 'TAP', 'PER']:
            if col in df_mostrar.columns:
                df_mostrar[col] = df_mostrar[col].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "-")
        
        # Ordenar por puntos si está disponible
        if 'PTS' in df_mostrar.columns:
            df_mostrar = df_mostrar.sort_values('PTS', ascending=False)
        
        # Mostrar tabla de estadísticas
        st.subheader("📈 Estadísticas del Equipo")
        st.dataframe(
            df_mostrar,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Jugador": st.column_config.TextColumn(
                    "Jugador",
                    width="medium",
                    help="Apellido, Nombre"
                ),
                "PJ": st.column_config.NumberColumn(
                    "PJ",
                    help="Partidos Jugados"
                ),
                "MIN": st.column_config.TextColumn(
                    "MIN",
                    help="Minutos por partido"
                ),
                "PTS": st.column_config.TextColumn(
                    "PTS",
                    help="Puntos por partido"
                ),
                "AST": st.column_config.TextColumn(
                    "AST",
                    help="Asistencias por partido"
                ),
                "REB": st.column_config.TextColumn(
                    "REB",
                    help="Rebotes por partido"
                ),
                "ROB": st.column_config.TextColumn(
                    "ROB",
                    help="Robos por partido"
                ),
                "TAP": st.column_config.TextColumn(
                    "TAP",
                    help="Tapones por partido"
                ),
                "PER": st.column_config.TextColumn(
                    "PER",
                    help="Pérdidas por partido"
                ),
                "FG%": st.column_config.TextColumn(
                    "FG%",
                    help="Porcentaje de tiros de campo"
                ),
                "3P%": st.column_config.TextColumn(
                    "3P%",
                    help="Porcentaje de triples"
                ),
                "TL%": st.column_config.TextColumn(
                    "TL%",
                    help="Porcentaje de tiros libres"
                )
            }
        )
        
        # Sección de Apuestas
        st.markdown("---")
        st.header("💰 Análisis de Apuestas")
        
        try:
            # Tabs para diferentes fuentes de cuotas
            tab1, tab2, tab3 = st.tabs(["📊 Análisis Individual", "📈 Cargar Excel", "🔍 Apuestas Cargadas"])
            
            with tab1:
                st.subheader("🎯 Análisis Individual")
                
                # Obtener lista de jugadores
                if 'PLAYER_NAME' not in df_jugadores.columns:
                    st.error("❌ No se encontró la lista de jugadores")
                    st.stop()
                
                # Mantener los nombres en su orden natural
                jugadores = sorted(df_jugadores['PLAYER_NAME'].unique().tolist())
                
                # Layout de 2 columnas para los inputs
                col1, col2 = st.columns(2)
                
                with col1:
                    jugador_sel = st.selectbox(
                        "👤 Seleccionar Jugador",
                        jugadores,
                        key='jugador_sel_manual'
                    )
                    
                    tipo_prop = st.selectbox(
                        "📊 Tipo de Prop", 
                        [
                            "Puntos",
                            "Asistencias", 
                            "Rebotes",
                            "Triples",
                            "Robos",
                            "Tapones",
                            "Bloqueos",
                            "Pérdidas",
                            "Pérdidas de balón",
                            "Puntos + Asistencias",
                            "Puntos + Rebotes",
                            "Asistencias + Rebotes",
                            "Puntos + Asistencias + Rebotes",
                            "Tapones + Robos",
                            "Bloqueos + Robos"
                        ]
                    )
                    
                    # Selector de local/visitante
                    localidad = st.selectbox(
                        "🏠 Filtrar por Localía",
                        ["Todos los partidos", "Solo Local", "Solo Visitante"],
                        help="Analizar solo partidos de local, visitante o ambos"
                    )
                    
                    # Ajustar el valor por defecto según el tipo de prop
                    valor_defecto = {
                        "Puntos": 20,
                        "Asistencias": 5,
                        "Rebotes": 5,
                        "Triples": 2,
                        "Robos": 1,
                        "Tapones": 1,
                        "Bloqueos": 1,
                        "Pérdidas": 2,
                        "Pérdidas de balón": 2,
                        "Puntos + Asistencias": 25,
                        "Puntos y Asistencias": 25,
                        "Puntos más Asistencias": 25,
                        "Puntos + Rebotes": 25,
                        "Puntos y Rebotes": 25,
                        "Puntos más Rebotes": 25,
                        "Asistencias + Rebotes": 15,
                        "Asistencias y Rebotes": 15,
                        "Asistencias más Rebotes": 15,
                        "Puntos + Asistencias + Rebotes": 35,
                        "Puntos, Asistencias y Rebotes": 35,
                        "Puntos más Asistencias más Rebotes": 35,
                        "Tapones + Robos": 3,
                        "Tapones y Robos": 3,
                        "Tapones más Robos": 3,
                        "Bloqueos + Robos": 3,
                        "Bloqueos y Robos": 3,
                        "Bloqueos más Robos": 3
                    }.get(tipo_prop, 1)
                
                with col2:
                    col_umbral1, col_umbral2 = st.columns(2)
                    with col_umbral1:
                        umbral = st.number_input(
                            f"📏 Línea",
                            min_value=0.5,
                            value=float(valor_defecto),
                            step=0.5,
                            key='umbral_manual'
                        )
                    with col_umbral2:
                        tipo_apuesta = st.selectbox(
                            "📈 Tipo de Apuesta",
                            ["Más de", "Menos de"],
                            help="'Más de' significa que superará el umbral, 'Menos de' que quedará por debajo"
                        )
                    
                    cuota = st.number_input(
                        "💰 Cuota Ofrecida",
                        min_value=1.01,
                        value=1.90,
                        step=0.05,
                        key='cuota_manual'
                    )
                
                # Botón de análisis centrado
                col1, col2, col3 = st.columns([1,2,1])
                with col2:
                    if st.button("📊 Analizar Apuesta", key='analizar_manual', use_container_width=True):
                        with st.spinner("Analizando apuesta..."):
                            try:
                                # Verificar que la columna existe en el DataFrame
                                columna_prop = prop_mapping[tipo_prop]
                                if columna_prop not in df_jugadores.columns:
                                    st.error(f"❌ No se encontró la columna {columna_prop} para la prop {tipo_prop}")
                                    st.write("Columnas disponibles:", df_jugadores.columns.tolist())
                                    st.stop()
                                
                                resultado = evaluar_prop_bet(
                                    stats=nba,
                                    equipo=equipo_sel,
                                    jugador=jugador_sel,
                                    prop=tipo_prop,
                                    umbral=umbral,
                                    cuota=cuota,
                                    temporada=temporada_sel,
                                    tipo_temporada=tipos_temporada_sel,
                                    es_over=tipo_apuesta == "Más de",
                                    filtro_local=localidad
                                )
                                
                                # Crear contenedor para el resultado
                                result_container = st.container()
                                with result_container:
                                    st.markdown("### 📊 Resultado del Análisis")
                                    st.code(resultado, language="markdown")
                                    
                                    # Extraer el valor esperado y la probabilidad del resultado
                                    import re
                                    valor_esperado = None
                                    probabilidad = None
                                    for linea in resultado.split('\n'):
                                        if 'Valor esperado por unidad apostada:' in linea:
                                            valor_esperado = float(re.search(r'[-+]?\d*\.\d+', linea).group())
                                        elif 'Probabilidad histórica:' in linea:
                                            prob_str = re.search(r'(\d+\.?\d*)%', linea)
                                            if prob_str:
                                                probabilidad = float(prob_str.group(1)) / 100
                                    
                                    # Agregar al historial
                                    nueva_apuesta = {
                                        'jugador': jugador_sel,
                                        'tipo': tipo_prop,
                                        'linea': f"{'>' if tipo_apuesta == 'Más de' else '<'}{umbral}",
                                        'cuota': cuota,
                                        'probabilidad': probabilidad,
                                        'valor_esperado': valor_esperado,
                                        'recomendacion': '✅' if valor_esperado > 0 else '❌'
                                    }
                                    st.session_state.historial_apuestas.append(nueva_apuesta)
                                    
                            except Exception as e:
                                st.error(f"❌ Error al analizar la apuesta: {str(e)}")
                                st.write("Detalles del error:", str(e))
            
        except Exception as e:
            st.error(f"❌ Error al cargar la sección de apuestas: {str(e)}")
            st.stop()

        with tab2:
            st.subheader("📑 Cargar Cuotas desde Excel")
            
            try:
                # Layout de dos columnas
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Selector de jugador
                    if 'PLAYER_NAME' not in df_jugadores.columns:
                        st.error("❌ No se encontró la lista de jugadores")
                        st.stop()
                    
                    jugadores = sorted(df_jugadores['PLAYER_NAME'].unique().tolist())
                    jugador_cuotas = st.selectbox(
                        "👤 Seleccionar Jugador",
                        jugadores,
                        key='jugador_sel_excel'
                    )
                    
                    # Opción para especificar si tiene encabezados
                    tiene_encabezado = st.radio(
                        "📋 Formato del Excel",
                        options=["Sin encabezados", "Con encabezados"],
                        index=0,  # Por defecto asumimos sin encabezados
                        help="Selecciona 'Sin encabezados' si la primera fila ya contiene una prop"
                    )
                    
                    # File uploader
                    uploaded_file = st.file_uploader(
                        "📄 Seleccionar archivo Excel",
                        type=['xlsx', 'xls'],
                        help="Selecciona un archivo Excel con el formato especificado"
                    )
                
                with col2:
                    # Mostrar ejemplo de formato en un expander más compacto
                    with st.expander("ℹ️ Ver formato"):
                        st.caption("""
                        **Estructura del Excel sin encabezados:**
                        ```
                        Puntos|25.5 |25.5
                              |1.85 |1.95
                        ```
                        
                        **Estructura del Excel con encabezados:**
                        ```
                        Prop  |Más  |Menos
                        Puntos|25.5 |25.5
                              |1.85 |1.95
                        ```
                        """)
                
                # Botón explícito para cargar y procesar
                if uploaded_file is not None:
                    if st.button("📥 Cargar Excel", key='cargar_excel', use_container_width=True):
                        with st.spinner("Procesando cuotas..."):
                            try:
                                # Guardar el archivo temporalmente
                                with open("temp_odds.xlsx", "wb") as f:
                                    f.write(uploaded_file.getvalue())
                                
                                # Cargar las cuotas
                                loader = ExcelOddsLoader("temp_odds.xlsx")
                                # Pasar el parámetro de encabezados al loader
                                props_por_jugador = loader.load_odds(tiene_encabezados=(tiene_encabezado == "Con encabezados"))
                                
                                if props_por_jugador:
                                    # Guardar en session state
                                    st.session_state.odds_data = props_por_jugador
                                    
                                    # Crear DataFrame para mostrar todas las cuotas
                                    odds_data = []
                                    for jugador, props in props_por_jugador.items():
                                        for prop in props:
                                            # Agregar over si existe
                                            if prop['over_line'] is not None and prop['over_odds'] is not None:
                                                odds_data.append({
                                                    'Jugador': jugador,
                                                    'Prop': prop['prop_name'],
                                                    'Línea': prop['over_line'],
                                                    'Tipo': 'Más de',
                                                    'Cuota': prop['over_odds']
                                                })
                                            # Agregar under si existe
                                            if prop['under_line'] is not None and prop['under_odds'] is not None:
                                                odds_data.append({
                                                    'Jugador': jugador,
                                                    'Prop': prop['prop_name'],
                                                    'Línea': prop['under_line'],
                                                    'Tipo': 'Menos de',
                                                    'Cuota': prop['under_odds']
                                                })
                                    
                                    if odds_data:
                                        # Guardar en session state
                                        st.session_state.odds_data_df = pd.DataFrame(odds_data)
                                        
                                        # Mostrar éxito y tabla de cuotas
                                        st.success("✅ Cuotas cargadas correctamente")
                                        
                                        st.markdown("### 📊 Cuotas Disponibles")
                                        st.data_editor(
                                            st.session_state.odds_data_df,
                                            use_container_width=True,
                                            hide_index=True,
                                            column_config={
                                                "Jugador": st.column_config.TextColumn(
                                                    "Jugador",
                                                    width="medium",
                                                    help="Nombre del jugador (nombre de la hoja)"
                                                ),
                                                "Prop": st.column_config.TextColumn(
                                                    "Prop",
                                                    width="medium",
                                                    help="Tipo de prop"
                                                ),
                                                "Línea": st.column_config.NumberColumn(
                                                    "Línea",
                                                    format="%.1f",
                                                    help="Valor de la línea"
                                                ),
                                                "Tipo": st.column_config.TextColumn(
                                                    "Tipo",
                                                    width="small",
                                                    help="Más de/Menos de"
                                                ),
                                                "Cuota": st.column_config.NumberColumn(
                                                    "Cuota",
                                                    format="%.2f",
                                                    help="Cuota ofrecida"
                                                )
                                            }
                                        )
                                        
                                        # Mensaje para dirigir al usuario
                                        st.info("👉 Ve a la pestaña 'Apuestas Cargadas' para analizar las props")
                                    else:
                                        st.warning("⚠️ No se encontraron cuotas válidas en el archivo")
                                else:
                                    st.error("❌ No se pudieron procesar las cuotas del archivo")
                            except Exception as e:
                                st.error(f"❌ Error al procesar el archivo: {str(e)}")
                else:
                    # Mensaje de ayuda inicial
                    st.info("👆 Sube un archivo Excel para comenzar. Cada hoja debe tener el nombre del jugador.")
                    
            except Exception as e:
                st.error(f"❌ Error en la pestaña de carga: {str(e)}")
                st.stop()

        with tab3:
            st.subheader("🔍 Análisis de Apuestas Cargadas")
            
            try:
                # Verificar si hay datos cargados
                if 'odds_data' not in st.session_state:
                    st.info("👆 Primero carga un archivo Excel con cuotas en la pestaña 'Cargar Excel'")
                    st.stop()
                
                # Mostrar datos cargados
                if 'odds_data_df' in st.session_state:
                    st.write("### 📊 Cuotas Disponibles")
                    st.data_editor(
                        st.session_state.odds_data_df,
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Botón para analizar
                if st.button("🔍 Analizar Todas las Props", key='analizar_props', use_container_width=True):
                    with st.spinner("Analizando props..."):
                        try:
                            # Limpiar el historial actual
                            st.session_state.historial_apuestas = []
                            
                            # Contenedor para los análisis detallados
                            with st.expander("📈 Análisis Detallados", expanded=True):
                                # Iterar sobre cada jugador y sus props
                                for jugador, props in st.session_state.odds_data.items():
                                    st.markdown(f"## 👤 {jugador}")
                                    
                                    for prop in props:
                                        st.write(f"\nAnalizando {prop['prop_name']}...")
                                        
                                        # Analizar Over si existe
                                        if prop['over_line'] is not None and prop['over_odds'] is not None:
                                            try:
                                                st.write(f"Analizando Over {prop['over_line']}...")
                                                resultado_over = evaluar_prop_bet(
                                                    stats=nba,
                                                    equipo=equipo_sel,
                                                    jugador=jugador,
                                                    prop=prop['prop_name'],
                                                    umbral=prop['over_line'],
                                                    cuota=prop['over_odds'],
                                                    temporada=temporada_sel,
                                                    tipo_temporada=tipos_temporada_sel,
                                                    es_over=True,
                                                    filtro_local="Todos los partidos"
                                                )
                                                st.markdown(f"### 📊 {prop['prop_name']} Más de {prop['over_line']}")
                                                st.code(resultado_over, language="markdown")
                                                
                                                # Extraer el valor esperado y la probabilidad
                                                valor_esperado = None
                                                probabilidad = None
                                                for linea in resultado_over.split('\n'):
                                                    if 'Valor esperado por unidad apostada:' in linea:
                                                        valor_esperado = float(re.search(r'[-+]?\d*\.\d+', linea).group())
                                                    elif 'Probabilidad histórica:' in linea:
                                                        prob_str = re.search(r'(\d+\.?\d*)%', linea)
                                                        if prob_str:
                                                            probabilidad = float(prob_str.group(1)) / 100
                                                
                                                # Agregar al historial
                                                st.session_state.historial_apuestas.append({
                                                    'jugador': jugador,
                                                    'tipo': prop['prop_name'],
                                                    'linea': f">{prop['over_line']}",
                                                    'cuota': prop['over_odds'],
                                                    'probabilidad': probabilidad,
                                                    'valor_esperado': valor_esperado,
                                                    'recomendacion': '✅' if valor_esperado > 0 else '❌'
                                                })
                                                
                                            except Exception as e:
                                                st.error(f"Error al analizar {prop['prop_name']} Más de {prop['over_line']}: {str(e)}")
                                        
                                        # Analizar Under si existe
                                        if prop['under_line'] is not None and prop['under_odds'] is not None:
                                            try:
                                                st.write(f"Analizando Under {prop['under_line']}...")
                                                resultado_under = evaluar_prop_bet(
                                                    stats=nba,
                                                    equipo=equipo_sel,
                                                    jugador=jugador,
                                                    prop=prop['prop_name'],
                                                    umbral=prop['under_line'],
                                                    cuota=prop['under_odds'],
                                                    temporada=temporada_sel,
                                                    tipo_temporada=tipos_temporada_sel,
                                                    es_over=False,
                                                    filtro_local="Todos los partidos"
                                                )
                                                st.markdown(f"### 📊 {prop['prop_name']} Menos de {prop['under_line']}")
                                                st.code(resultado_under, language="markdown")
                                                
                                                # Extraer el valor esperado y la probabilidad
                                                valor_esperado = None
                                                probabilidad = None
                                                for linea in resultado_under.split('\n'):
                                                    if 'Valor esperado por unidad apostada:' in linea:
                                                        valor_esperado = float(re.search(r'[-+]?\d*\.\d+', linea).group())
                                                    elif 'Probabilidad histórica:' in linea:
                                                        prob_str = re.search(r'(\d+\.?\d*)%', linea)
                                                        if prob_str:
                                                            probabilidad = float(prob_str.group(1)) / 100
                                                
                                                # Agregar al historial
                                                st.session_state.historial_apuestas.append({
                                                    'jugador': jugador,
                                                    'tipo': prop['prop_name'],
                                                    'linea': f"<{prop['under_line']}",
                                                    'cuota': prop['under_odds'],
                                                    'probabilidad': probabilidad,
                                                    'valor_esperado': valor_esperado,
                                                    'recomendacion': '✅' if valor_esperado > 0 else '❌'
                                                })
                                                
                                            except Exception as e:
                                                st.error(f"Error al analizar {prop['prop_name']} Menos de {prop['under_line']}: {str(e)}")
                            
                            # Mostrar resumen en el historial
                            if st.session_state.historial_apuestas:
                                st.markdown("---")
                                st.header("📚 Resumen de Props Analizadas")
                                
                                # Crear DataFrame del historial
                                df_historial = pd.DataFrame(st.session_state.historial_apuestas)
                                
                                # Ordenar por valor esperado (mejor a peor)
                                df_historial = df_historial.sort_values('valor_esperado', ascending=False)
                                
                                # Formatear el valor esperado y la probabilidad
                                df_historial['valor_esperado'] = df_historial['valor_esperado'].apply(
                                    lambda x: f"{x:+.2f}" if x is not None else "N/A"
                                )
                                df_historial['probabilidad'] = df_historial['probabilidad'].apply(
                                    lambda x: f"{x*100:.1f}%" if x is not None else "N/A"
                                )
                                
                                # Mostrar tabla con estilo
                                st.data_editor(
                                    df_historial,
                                    column_config={
                                        "jugador": st.column_config.TextColumn(
                                            "Jugador",
                                            width="medium",
                                            help="Nombre del jugador"
                                        ),
                                        "tipo": st.column_config.TextColumn(
                                            "Tipo",
                                            width="medium",
                                            help="Tipo de prop"
                                        ),
                                        "linea": st.column_config.TextColumn(
                                            "Línea",
                                            width="small",
                                            help="Valor de la línea"
                                        ),
                                        "cuota": st.column_config.NumberColumn(
                                            "Cuota",
                                            format="%.2f",
                                            help="Cuota ofrecida"
                                        ),
                                        "probabilidad": st.column_config.TextColumn(
                                            "Prob. Hist.",
                                            width="small",
                                            help="Probabilidad histórica"
                                        ),
                                        "valor_esperado": st.column_config.TextColumn(
                                            "Valor Esp.",
                                            width="small",
                                            help="Valor esperado por unidad apostada"
                                        ),
                                        "recomendacion": st.column_config.TextColumn(
                                            "Rec.",
                                            width="small",
                                            help="Recomendación de apuesta"
                                        )
                                    },
                                    hide_index=True,
                                    use_container_width=True
                                )
                                
                                # Botón para limpiar historial
                                if st.button("🗑️ Limpiar Historial", key='limpiar_historial'):
                                    st.session_state.historial_apuestas = []
                                    st.rerun()
                                    
                        except Exception as e:
                            st.error(f"Error general durante el análisis: {str(e)}")
                            
            except Exception as e:
                st.error(f"❌ Error en la pestaña de análisis: {str(e)}")
                st.stop()
    except Exception as e:
        st.error(f"❌ Error al obtener datos: {str(e)}")
        st.write("Intente refrescar la página o contacte al soporte técnico")


