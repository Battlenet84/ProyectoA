import streamlit as st
from nba_stats import NBAStats
from bet_calculator import evaluar_prop_bet

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
    }
    .stats-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("🏀 NBA Stats Dashboard")

# Inicializar el objeto de stats
nba = NBAStats()

# Sidebar para selección
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Selector de equipo
    equipos = nba.obtener_lista_equipos()
    equipo_sel = st.selectbox("📋 Seleccionar Equipo", equipos)
    
    # Selector de equipo rival
    equipos_rivales = ["Todos los equipos"] + [equipo for equipo in equipos if equipo != equipo_sel]
    rival_sel = st.selectbox("🆚 Seleccionar Rival", equipos_rivales)
    
    # Información de debug oculta
    with st.expander("🔍 Información de Debug", expanded=False):
        st.write("Equipo seleccionado:", equipo_sel)
        st.write("Rival seleccionado:", rival_sel)

# Convertir "Todos los equipos" a None para la función
rival_param = None if rival_sel == "Todos los equipos" else [rival_sel]

# Contenido principal
if equipo_sel:
    # Título de la sección
    st.header(f"📊 Estadísticas de {equipo_sel}" + (f" vs {rival_sel}" if rival_sel != "Todos los equipos" else ""))
    
    # Obtener datos
    df_jugadores = nba.obtener_estadisticas_jugadores_equipo(equipo_sel, rival_param)
    
    if df_jugadores.empty:
        st.error("❌ No se encontraron datos para mostrar")
    else:
        # Mapeo de columnas (oculto en expander)
        with st.expander("🔧 Detalles Técnicos", expanded=False):
            st.write("Dimensiones:", df_jugadores.shape)
            st.write("Columnas disponibles:", df_jugadores.columns.tolist())
        
        # Mapeo flexible de columnas
        column_mapping = {}
        for col in df_jugadores.columns:
            if 'PLAYER' in col or 'NAME' in col:
                column_mapping['PLAYER_NAME'] = col
            elif col == 'GP':
                column_mapping['GP'] = col
            elif col == 'MIN':
                column_mapping['MIN'] = col
            elif col == 'PTS':
                column_mapping['PTS'] = col
            elif col == 'AST':
                column_mapping['AST'] = col
            elif col == 'REB':
                column_mapping['REB'] = col
            elif col == 'STL':
                column_mapping['STL'] = col
            elif col == 'BLK':
                column_mapping['BLK'] = col
            elif col == 'TOV':
                column_mapping['TOV'] = col
            elif col == 'PF':
                column_mapping['PF'] = col
            elif 'FG_PCT' in col:
                column_mapping['FG_PCT'] = col
            elif 'FG3_PCT' in col:
                column_mapping['FG3_PCT'] = col
            elif 'FT_PCT' in col:
                column_mapping['FT_PCT'] = col

        # Nombres en español para mostrar
        column_display_names = {
            'PLAYER_NAME': 'Jugador',
            'GP': 'Partidos',
            'MIN': 'Minutos',
            'PTS': 'Puntos',
            'AST': 'Asistencias',
            'REB': 'Rebotes',
            'STL': 'Robos',
            'BLK': 'Tapones',
            'TOV': 'Pérdidas',
            'PF': 'Faltas',
            'FG_PCT': '% Tiros de Campo',
            'FG3_PCT': '% Triples',
            'FT_PCT': '% Tiros Libres'
        }

        # Crear DataFrame para mostrar
        columns_to_show = []
        new_column_names = []
        
        for std_name, display_name in column_display_names.items():
            if std_name in column_mapping:
                columns_to_show.append(column_mapping[std_name])
                new_column_names.append(display_name)

        if columns_to_show:
            df_mostrar = df_jugadores[columns_to_show].copy()
            df_mostrar.columns = new_column_names
            
            # Mostrar tabla de estadísticas
            st.subheader("📈 Estadísticas de Jugadores")
            st.dataframe(
                df_mostrar,
                use_container_width=True,
                hide_index=True
            )

            # Sección de Apuestas
            st.markdown("---")
            st.header("💰 Análisis de Apuestas")
            
            # Obtener lista de jugadores
            player_name_col = column_mapping.get('PLAYER_NAME')
            if player_name_col:
                jugadores = df_jugadores[player_name_col].unique().tolist()
                
                # Layout de 2 columnas para los inputs
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🎯 Configuración")
                    jugador_sel = st.selectbox("Seleccionar Jugador", jugadores)
                    umbral = st.number_input("Umbral de Puntos", min_value=1, value=20)
                
                with col2:
                    st.subheader("📊 Cuota")
                    cuota = st.number_input("Cuota Ofrecida", min_value=1.01, value=1.90, step=0.05)

                # Botón de análisis
                if st.button("📊 Analizar Apuesta"):
                    with st.spinner("Analizando apuesta..."):
                        resultado = evaluar_prop_bet(
                            stats=nba,
                            equipo=equipo_sel,
                            jugador=jugador_sel,
                            prop="PTS",
                            umbral=umbral,
                            cuota=cuota
                        )
                        
                        # Mostrar resultado en un contenedor estilizado
                        st.markdown("### 📊 Resultado del Análisis")
                        st.code(resultado, language="markdown")
            else:
                st.error("❌ No se pudo acceder a la lista de jugadores")
        else:
            st.error("❌ No se pudieron encontrar las columnas necesarias")


