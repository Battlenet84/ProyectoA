import streamlit as st
from nba_stats import NBAStats
from bet_calculator import evaluar_prop_bet, calcular_probabilidad_historica
from bet_scraper import BetScraper
from odds_api import GoogleSheetsOddsLoader
import pandas as pd
import re  # Agregar importación del módulo re para expresiones regulares
from googleapiclient.discovery import build

def normalize_player_name(name: str) -> str:
    """Normaliza el nombre de un jugador para facilitar la búsqueda."""
    # Convertir a minúsculas y eliminar puntos y comas
    name = name.lower().replace('.', '').replace(',', '').strip()
    
    # Si el nombre tiene formato "Apellido, Nombre", invertirlo
    if ',' in name:
        parts = name.split(',')
        if len(parts) == 2:
            name = f"{parts[1].strip()} {parts[0].strip()}"
    
    # Eliminar caracteres especiales y espacios múltiples
    name = re.sub(r'[^a-z\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def find_player_in_team(df: pd.DataFrame, player_name: str) -> pd.DataFrame:
    """Busca un jugador en un DataFrame de equipo usando diferentes métodos."""
    # Normalizar el nombre buscado
    nombre_norm = normalize_player_name(player_name)
    
    # Normalizar nombres en el DataFrame
    df['PLAYER_NAME_NORM'] = df['PLAYER_NAME'].apply(normalize_player_name)
    
    # 1. Coincidencia exacta
    match_df = df[df['PLAYER_NAME_NORM'] == nombre_norm]
    if not match_df.empty:
        return match_df
    
    # 2. Coincidencia por apellido
    apellido = nombre_norm.split()[-1]
    match_df = df[df['PLAYER_NAME_NORM'].str.endswith(apellido)]
    if not match_df.empty:
        return match_df
    
    # 3. Coincidencia parcial
    match_df = df[df['PLAYER_NAME_NORM'].str.contains(nombre_norm, na=False)]
    if not match_df.empty:
        return match_df
    
    # 4. Coincidencia por partes del nombre
    for part in nombre_norm.split():
        if len(part) > 2:  # Evitar partes muy cortas
            match_df = df[df['PLAYER_NAME_NORM'].str.contains(part, na=False)]
            if not match_df.empty:
                return match_df
    
    return pd.DataFrame()

def create_combined_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Crea columnas de estadísticas combinadas si no existen."""
    # Lista de combinaciones posibles
    combined_stats = {
        'PTS_AST': ['PTS', 'AST'],
        'PTS_REB': ['PTS', 'REB'],
        'AST_REB': ['AST', 'REB'],
        'PTS_AST_REB': ['PTS', 'AST', 'REB'],
        'STL_BLK': ['STL', 'BLK']
    }
    
    # Crear cada combinación si las columnas base existen
    for combined_name, base_stats in combined_stats.items():
        if combined_name not in df.columns:
            if all(stat in df.columns for stat in base_stats):
                df[combined_name] = df[base_stats].sum(axis=1)
    
    return df

# Cargar apuestas desde Google Sheets
SPREADSHEET_ID = "1VTn80vGKu9MbAHZoV9UoVKYyPeVkh-6_N6DMNQInKQk"

# Inicializar el cargador de cuotas desde Google Sheets si no existe en la sesión
if 'sheets_loader' not in st.session_state:
    st.session_state.sheets_loader = GoogleSheetsOddsLoader(SPREADSHEET_ID)

# Cargar las cuotas si no están en la sesión
if 'odds_data' not in st.session_state:
    try:
        st.session_state.odds_data = st.session_state.sheets_loader.load_odds()
        # Crear DataFrame para mostrar todas las cuotas
        odds_data = []
        for jugador, props in st.session_state.odds_data.items():
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
            st.session_state.odds_data_df = pd.DataFrame(odds_data)
    except Exception as e:
        print(f"Error al cargar cuotas de Google Sheets: {str(e)}")

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
                                loader = GoogleSheetsOddsLoader("temp_odds.xlsx")
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
                # Botón para probar conexión
                if st.button("🔌 Probar Conexión", key="test_connection"):
                    with st.spinner("Probando conexión con Google Sheets..."):
                        try:
                            # Intentar obtener solo los metadatos del documento
                            creds = st.session_state.sheets_loader._get_credentials()
                            service = build('sheets', 'v4', credentials=creds)
                            sheet_metadata = service.spreadsheets().get(
                                spreadsheetId=st.session_state.sheets_loader.spreadsheet_id
                            ).execute()
                            
                            # Mostrar información del documento
                            st.success("✅ Conexión exitosa con Google Sheets")
                            st.write("Información del documento:")
                            st.json({
                                "title": sheet_metadata.get('properties', {}).get('title', 'N/A'),
                                "locale": sheet_metadata.get('properties', {}).get('locale', 'N/A'),
                                "sheets": [sheet['properties']['title'] for sheet in sheet_metadata.get('sheets', [])]
                            })
                        except Exception as e:
                            st.error(f"❌ Error de conexión: {str(e)}")
                            if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
                                st.write("Estado de las credenciales:")
                                creds_info = {k: "✓" for k in st.secrets.gcp_service_account.keys()}
                                st.json(creds_info)
                            else:
                                st.warning("No se encontraron credenciales en Streamlit Secrets")
                
                # Botón para recargar y analizar todas las props
                if st.button("🔄 Recargar y Analizar Props", key="reload_analyze_odds"):
                    with st.spinner("Cargando y analizando props..."):
                        try:
                            # Cargar datos de Google Sheets
                            st.info("Cargando datos desde Google Sheets...")
                            st.session_state.odds_data = st.session_state.sheets_loader.load_odds()
                            
                            if not st.session_state.odds_data:
                                st.error("No se encontraron datos en Google Sheets")
                                st.write("Debug: odds_data está vacío")
                                st.stop()
                            
                            # Mostrar información detallada de las props cargadas
                            st.write("Debug: Datos cargados de Google Sheets:")
                            total_props = 0
                            for jugador, props in st.session_state.odds_data.items():
                                st.write(f"\nJugador: {jugador}")
                                for prop in props:
                                    total_props += 1
                                    st.write(f"  Prop: {prop['prop_name']}")
                                    if prop['over_line'] is not None:
                                        st.write(f"    Over {prop['over_line']} @ {prop['over_odds']}")
                                    if prop['under_line'] is not None:
                                        st.write(f"    Under {prop['under_line']} @ {prop['under_odds']}")
                            
                            st.success(f"✅ Datos cargados: {len(st.session_state.odds_data)} jugadores y {total_props} props encontradas")
                            
                            # Lista para almacenar todos los análisis
                            analisis_props = []
                            
                            # Barra de progreso
                            total_props = sum(
                                len(props) * 2 for props in st.session_state.odds_data.values()
                            )  # *2 porque cada prop tiene over y under
                            
                            progress_bar = st.progress(0)
                            progress_text = st.empty()
                            status_text = st.empty()
                            props_analizadas = 0
                            
                            # Diccionario para evitar duplicados
                            props_procesadas = set()

                            # Primero obtener la lista de todos los equipos y sus jugadores
                            status_text.text("Cargando datos de equipos...")
                            equipos_data = {}
                            for equipo in nba.obtener_lista_equipos():
                                try:
                                    df_temp = nba.obtener_estadisticas_jugadores_equipo(
                                        equipo=equipo,
                                        temporada=temporada_sel,
                                        tipo_temporada=tipos_temporada_sel
                                    )
                                    if not df_temp.empty:
                                        equipos_data[equipo] = df_temp
                                        st.write(f"Debug: Cargados {len(df_temp)} jugadores del equipo {equipo}")
                                except Exception as e:
                                    st.write(f"Debug: Error al cargar datos del equipo {equipo}: {str(e)}")
                            
                            st.write(f"Debug: Datos cargados para {len(equipos_data)} equipos")
                            
                            # Diccionario para cachear datos de jugadores
                            cache_datos_jugador = {}
                            
                            # Procesar cada prop
                            for jugador, props in st.session_state.odds_data.items():
                                # Extraer nombre del jugador (antes de la coma si existe)
                                nombre_jugador = jugador.split(',')[0] if ',' in jugador else jugador
                                status_text.text(f"Procesando jugador: {nombre_jugador}")
                                st.write(f"\nDebug: Procesando jugador: {nombre_jugador}")
                                
                                # Obtener datos del jugador una sola vez y cachearlos
                                if nombre_jugador not in cache_datos_jugador:
                                    try:
                                        status_text.text(f"Buscando estadísticas de {nombre_jugador}...")
                                        
                                        # Buscar jugador en todos los equipos
                                        equipo_encontrado = None
                                        df_jugador = None
                                        
                                        for equipo, df_equipo in equipos_data.items():
                                            df_match = find_player_in_team(df_equipo.copy(), nombre_jugador)
                                            if not df_match.empty:
                                                equipo_encontrado = equipo
                                                df_jugador = df_match
                                                st.write(f"Debug: ✅ Jugador encontrado en el equipo {equipo}")
                                                st.write(f"Debug: Nombre en estadísticas: {df_jugador['PLAYER_NAME'].iloc[0]}")
                                                break
                                        
                                        if equipo_encontrado is None:
                                            st.warning(f"No se encontró el equipo actual de {nombre_jugador}")
                                            st.write("Debug: No se encontró el equipo del jugador")
                                            continue
                                        
                                        # Obtener el ID del jugador
                                        player_id = str(df_jugador['PLAYER_ID'].iloc[0])
                                        status_text.text(f"Obteniendo datos partido a partido de {nombre_jugador}...")
                                        st.write(f"Debug: ID del jugador: {player_id}")
                                        
                                        # Obtener datos partido a partido
                                        datos_partidos = nba.get_player_game_logs(
                                            player_id=player_id,
                                            season=temporada_sel,
                                            season_type=tipos_temporada_sel
                                        )
                                        
                                        if datos_partidos.empty:
                                            st.warning(f"No se encontraron datos partido a partido para {nombre_jugador}")
                                            st.write("Debug: DataFrame de partidos está vacío")
                                            continue
                                        
                                        # Crear columnas combinadas
                                        datos_partidos = create_combined_stats(datos_partidos)
                                        st.write("Debug: Columnas después de crear combinaciones:", datos_partidos.columns.tolist())
                                                
                                        cache_datos_jugador[nombre_jugador] = datos_partidos
                                        status_text.success(f"✅ Datos obtenidos para {nombre_jugador}")
                                        
                                    except Exception as e:
                                        st.error(f"Error al obtener datos de {nombre_jugador}: {str(e)}")
                                        st.write(f"Debug: Error completo:", str(e))
                                        import traceback
                                        st.write("Debug: Traceback:", traceback.format_exc())
                                        continue
                                
                                # Usar los datos cacheados para analizar las props
                                datos_partidos = cache_datos_jugador.get(nombre_jugador)
                                if datos_partidos is not None and not datos_partidos.empty:
                                    for prop in props:
                                        # Actualizar progreso
                                        progress_text.text(f"Analizando {nombre_jugador} - {prop['prop_name']}")
                                        st.write(f"\nDebug: Analizando prop {prop['prop_name']} para {nombre_jugador}")
                                        
                                        # Mapear nombres de props a columnas de estadísticas
                                        stat_mapping = {
                                            # Estadísticas básicas - español
                                            'Puntos': 'PTS',
                                            'Asistencias': 'AST',
                                            'Rebotes': 'REB',
                                            'Triples': 'FG3M',
                                            'Robos': 'STL',
                                            'Tapones': 'BLK',
                                            'Bloqueos': 'BLK',
                                            'Pérdidas': 'TOV',
                                            'Pérdidas de balón': 'TOV',
                                            
                                            # Props combinadas - español
                                            'Puntos + Asistencias': 'PTS_AST',
                                            'Puntos y Asistencias': 'PTS_AST',
                                            'Puntos más Asistencias': 'PTS_AST',
                                            'Puntos+Asistencias': 'PTS_AST',
                                            
                                            'Puntos + Rebotes': 'PTS_REB',
                                            'Puntos y Rebotes': 'PTS_REB',
                                            'Puntos más Rebotes': 'PTS_REB',
                                            'Puntos+Rebotes': 'PTS_REB',
                                            
                                            'Asistencias + Rebotes': 'AST_REB',
                                            'Asistencias y Rebotes': 'AST_REB',
                                            'Asistencias más Rebotes': 'AST_REB',
                                            'Asistencias+Rebotes': 'AST_REB',
                                            
                                            'Puntos + Asistencias + Rebotes': 'PTS_AST_REB',
                                            'Puntos, Asistencias y Rebotes': 'PTS_AST_REB',
                                            'Puntos más Asistencias más Rebotes': 'PTS_AST_REB',
                                            'Puntos+Asistencias+Rebotes': 'PTS_AST_REB',
                                            
                                            'Tapones + Robos': 'STL_BLK',
                                            'Tapones y Robos': 'STL_BLK',
                                            'Tapones más Robos': 'STL_BLK',
                                            'Bloqueos + Robos': 'STL_BLK',
                                            'Bloqueos y Robos': 'STL_BLK',
                                            'Bloqueos más Robos': 'STL_BLK',
                                            'Tapones+Robos': 'STL_BLK',
                                            'Bloqueos+Robos': 'STL_BLK',
                                            
                                            # Estadísticas básicas - inglés
                                            'Points': 'PTS',
                                            'Assists': 'AST',
                                            'Rebounds': 'REB',
                                            'Threes': 'FG3M',
                                            'Steals': 'STL',
                                            'Blocks': 'BLK',
                                            'Turnovers': 'TOV',
                                            
                                            # Props combinadas - inglés
                                            'Points + Assists': 'PTS_AST',
                                            'Points and Assists': 'PTS_AST',
                                            'Points & Assists': 'PTS_AST',
                                            'Points+Assists': 'PTS_AST',
                                            
                                            'Points + Rebounds': 'PTS_REB',
                                            'Points and Rebounds': 'PTS_REB',
                                            'Points & Rebounds': 'PTS_REB',
                                            'Points+Rebounds': 'PTS_REB',
                                            
                                            'Assists + Rebounds': 'AST_REB',
                                            'Assists and Rebounds': 'AST_REB',
                                            'Assists & Rebounds': 'AST_REB',
                                            'Assists+Rebounds': 'AST_REB',
                                            
                                            'Points + Assists + Rebounds': 'PTS_AST_REB',
                                            'Points, Assists and Rebounds': 'PTS_AST_REB',
                                            'Points, Assists & Rebounds': 'PTS_AST_REB',
                                            'Points+Assists+Rebounds': 'PTS_AST_REB',
                                            
                                            'Blocks + Steals': 'STL_BLK',
                                            'Blocks and Steals': 'STL_BLK',
                                            'Blocks & Steals': 'STL_BLK',
                                            'Blocks+Steals': 'STL_BLK',
                                            
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
                                        
                                        # Obtener el nombre de la columna correcto
                                        prop_name = prop['prop_name'].strip()
                                        stat_name = stat_mapping.get(prop_name)
                                        
                                        if not stat_name:
                                            # Si no encontramos coincidencia exacta, intentar normalizar
                                            prop_name_norm = prop_name.lower().replace(' ', '').replace('+', '_')
                                            for key, value in stat_mapping.items():
                                                key_norm = key.lower().replace(' ', '').replace('+', '_')
                                                if key_norm == prop_name_norm:
                                                    stat_name = value
                                                    break
                                        
                                        if not stat_name:
                                            st.warning(f"No se pudo mapear la prop {prop_name} a una estadística")
                                            st.write(f"Debug: Prop {prop_name} no encontrada en el mapeo")
                                            continue
                                        
                                        st.write(f"Debug: Prop {prop_name} mapeada a {stat_name}")
                                        
                                        # Verificar si la columna existe o necesita ser creada
                                        if stat_name not in datos_partidos.columns:
                                            if '_' in stat_name:
                                                stats_base = stat_name.split('_')
                                                if all(stat in datos_partidos.columns for stat in stats_base):
                                                    st.write(f"Debug: Creando columna combinada {stat_name}")
                                                    datos_partidos[stat_name] = datos_partidos[stats_base].sum(axis=1)
                                                    st.write(f"Debug: Columna {stat_name} creada exitosamente")
                                                else:
                                                    missing_stats = [stat for stat in stats_base if stat not in datos_partidos.columns]
                                                    st.warning(f"No se encontraron todas las estadísticas necesarias para {prop_name}")
                                                    st.write(f"Debug: Faltan las columnas: {missing_stats}")
                                                    continue
                                            else:
                                                st.warning(f"No se encontró la estadística {stat_name} para {nombre_jugador}")
                                                st.write(f"Debug: Columna {stat_name} no encontrada")
                                                continue
                                        
                                        # Analizar over si existe
                                        if prop['over_line'] is not None and prop['over_odds'] is not None:
                                            try:
                                                # Crear una clave única para esta prop
                                                prop_key = f"{nombre_jugador}_{prop['prop_name']}_over_{prop['over_line']}"
                                                
                                                if prop_key not in props_procesadas:
                                                    props_procesadas.add(prop_key)
                                                    
                                                    # Asegurarnos de que los valores sean numéricos
                                                    over_line = float(prop['over_line'])
                                                    over_odds = float(prop['over_odds'])
                                                    
                                                    st.write(f"Debug: Analizando Over {over_line} @ {over_odds}")
                                                    
                                                    prob, cumplidos, total = calcular_probabilidad_historica(
                                                        datos_partidos,
                                                        stat_name,
                                                        over_line,
                                                        es_over=True
                                                    )
                                                    
                                                    st.write(f"Debug: Probabilidad calculada: {prob:.2%} ({cumplidos}/{total} partidos)")
                                                    
                                                    if prob > 0 and total > 0:
                                                        # Calcular valor esperado
                                                        valor_esperado = (prob * (over_odds - 1)) - ((1 - prob) * 1)
                                                        
                                                        analisis_props.append({
                                                            'jugador': jugador,
                                                            'tipo': prop['prop_name'],
                                                            'linea': f">{over_line}",
                                                            'cuota': over_odds,
                                                            'probabilidad': prob,
                                                            'valor_esperado': valor_esperado,
                                                            'recomendacion': '✅' if valor_esperado > 0 else '❌',
                                                            'partidos': total
                                                        })
                                                        st.write(f"Debug: Análisis Over agregado con valor esperado: {valor_esperado:.3f}")
                                            except Exception as e:
                                                st.error(f"Error al analizar {jugador} - {prop['prop_name']} Over: {str(e)}")
                                        
                                        props_analizadas += 1
                                        progress_bar.progress(props_analizadas / total_props)
                                        
                                        # Analizar under si existe
                                        if prop['under_line'] is not None and prop['under_odds'] is not None:
                                            try:
                                                # Crear una clave única para esta prop
                                                prop_key = f"{nombre_jugador}_{prop['prop_name']}_under_{prop['under_line']}"
                                                
                                                if prop_key not in props_procesadas:
                                                    props_procesadas.add(prop_key)
                                                    
                                                    # Asegurarnos de que los valores sean numéricos
                                                    under_line = float(prop['under_line'])
                                                    under_odds = float(prop['under_odds'])
                                                    
                                                    # Verificar si tenemos la estadística
                                                    if stat_name in datos_partidos.columns:
                                                        prob, cumplidos, total = calcular_probabilidad_historica(
                                                            datos_partidos,
                                                            stat_name,
                                                            under_line,
                                                            es_over=False
                                                        )
                                                        
                                                        if prob > 0 and total > 0:
                                                            # Calcular valor esperado
                                                            valor_esperado = (prob * (under_odds - 1)) - ((1 - prob) * 1)
                                                            
                                                            analisis_props.append({
                                                                'jugador': jugador,
                                                                'tipo': prop['prop_name'],
                                                                'linea': f"<{under_line}",
                                                                'cuota': under_odds,
                                                                'probabilidad': prob,
                                                                'valor_esperado': valor_esperado,
                                                                'recomendacion': '✅' if valor_esperado > 0 else '❌',
                                                                'partidos': total
                                                            })
                                            except Exception as e:
                                                st.error(f"Error al analizar {jugador} - {prop['prop_name']} Under: {str(e)}")
                                        
                                        props_analizadas += 1
                                        progress_bar.progress(props_analizadas / total_props)
                                
                            # Limpiar elementos de progreso
                            progress_bar.empty()
                            progress_text.empty()
                            status_text.empty()
                            
                            # Convertir a DataFrame y eliminar duplicados basados en todas las columnas excepto 'recomendacion'
                            if analisis_props:
                                df_analisis = pd.DataFrame(analisis_props)
                                df_analisis = df_analisis.drop_duplicates(
                                    subset=['jugador', 'tipo', 'linea', 'cuota', 'probabilidad', 'valor_esperado', 'partidos']
                                )
                                analisis_props = df_analisis.to_dict('records')
                            
                            # Guardar análisis en session state
                            st.session_state.historial_apuestas = analisis_props
                            
                            # Mostrar resumen
                            if analisis_props:
                                st.success(f"✅ {len(analisis_props)} props analizadas correctamente")
                            else:
                                st.warning("⚠️ No se encontraron props para analizar")
                            
                        except Exception as e:
                            st.error(f"Error al cargar/analizar datos: {str(e)}")
                    
                    # Mostrar historial de análisis
                    if 'historial_apuestas' in st.session_state and st.session_state.historial_apuestas:
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
                        st.dataframe(
                            df_historial,
                            use_container_width=True,
                            hide_index=True,
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
                                ),
                                "partidos": st.column_config.NumberColumn(
                                    "Partidos",
                                    help="Número de partidos analizados"
                                )
                            }
                        )
                        
                        # Botón para limpiar historial
                        if st.button("🗑️ Limpiar Historial", key='limpiar_historial'):
                            st.session_state.historial_apuestas = []
                            st.rerun()
                    else:
                        st.info("No hay props analizadas. Usa el botón 'Recargar y Analizar Props' para comenzar.")
            
            except Exception as e:
                st.error(f"Error en la pestaña de apuestas cargadas: {str(e)}")
                st.stop()
    except Exception as e:
        st.error(f"❌ Error al obtener datos: {str(e)}")
        st.write("Intente refrescar la página o contacte al soporte técnico")


