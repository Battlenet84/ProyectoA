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

# Inicializar el objeto de stats con manejo de errores
try:
    st.write("Inicializando conexión con NBA Stats...")
    nba = NBAStats()
    st.success("✅ Conexión establecida correctamente")
except Exception as e:
    st.error(f"❌ Error al inicializar NBA Stats: {str(e)}")
    st.stop()

# Sidebar para selección
with st.sidebar:
    st.header("⚙️ Configuración")
    
    try:
        # Selector de temporada
        st.write("Seleccionar temporada y tipo:")
        temporada_sel = st.selectbox(
            "📅 Temporada", 
            nba.obtener_lista_temporadas(),
            index=0  # Por defecto la más reciente
        )
        
        tipo_temporada_sel = st.selectbox(
            "🏆 Tipo de Temporada",
            nba.obtener_tipos_temporada(),
            index=0  # Por defecto temporada regular
        )
        
        # Selector de equipo
        st.write("Obteniendo lista de equipos...")
        equipos = nba.obtener_lista_equipos()
        equipo_sel = st.selectbox("📋 Seleccionar Equipo", equipos)
        
        # Selector de equipo rival
        equipos_rivales = ["Todos los equipos"] + [equipo for equipo in equipos if equipo != equipo_sel]
        rival_sel = st.selectbox("🆚 Seleccionar Rival", equipos_rivales)
        
        # Información de debug
        with st.expander("🔍 Información de Debug", expanded=False):
            st.write("Temporada seleccionada:", temporada_sel)
            st.write("Tipo de temporada:", tipo_temporada_sel)
            st.write("Equipo seleccionado:", equipo_sel)
            st.write("Rival seleccionado:", rival_sel)
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
        st.caption(f"Temporada: {temporada_sel} ({tipo_temporada_sel})")
        
        with st.spinner("Cargando estadísticas..."):
            # Obtener datos
            df_jugadores = nba.obtener_estadisticas_jugadores_equipo(
                equipo=equipo_sel, 
                rivales=rival_param,
                temporada=temporada_sel,
                tipo_temporada=tipo_temporada_sel
            )
        
        if df_jugadores.empty:
            st.error("❌ No se encontraron datos para mostrar")
            st.write("Intente refrescar la página o seleccionar otro equipo/temporada")
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
                if 'PLAYER_NAME' in df_jugadores.columns:
                    jugadores = sorted(df_jugadores['PLAYER_NAME'].unique().tolist())
                    
                    # Layout de 2 columnas para los inputs
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🎯 Configuración")
                        jugador_sel = st.selectbox("Seleccionar Jugador", jugadores)
                        tipo_prop = st.selectbox(
                            "Tipo de Prop", 
                            [
                                "Puntos",
                                "Asistencias", 
                                "Rebotes",
                                "Triples",
                                "Robos",
                                "Tapones",
                                "Pérdidas",
                                "Puntos + Asistencias",
                                "Puntos + Rebotes",
                                "Asistencias + Rebotes",
                                "Puntos + Asistencias + Rebotes",
                                "Tapones + Robos"
                            ]
                        )
                        
                        # Selector de local/visitante
                        localidad = st.selectbox(
                            "Filtrar por Localía",
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
                            "Pérdidas": 2,
                            "Puntos + Asistencias": 25,
                            "Puntos + Rebotes": 25,
                            "Asistencias + Rebotes": 15,
                            "Puntos + Asistencias + Rebotes": 35,
                            "Tapones + Robos": 3
                        }.get(tipo_prop, 1)
                        
                        col_umbral1, col_umbral2 = st.columns(2)
                        with col_umbral1:
                            umbral = st.number_input(
                                f"Línea de {tipo_prop}", 
                                min_value=0.5, 
                                value=float(valor_defecto),
                                step=0.5
                            )
                        with col_umbral2:
                            tipo_apuesta = st.selectbox(
                                "Tipo de Apuesta",
                                ["Más de", "Menos de"],
                                help="'Más de' significa que superará el umbral, 'Menos de' que quedará por debajo"
                            )
                    
                    with col2:
                        st.subheader("📊 Cuota")
                        cuota = st.number_input("Cuota Ofrecida", min_value=1.01, value=1.90, step=0.05)

                    # Botón de análisis
                    if st.button("📊 Analizar Apuesta"):
                        with st.spinner("Analizando apuesta..."):
                            try:
                                resultado = evaluar_prop_bet(
                                    stats=nba,
                                    equipo=equipo_sel,
                                    jugador=jugador_sel,
                                    prop=tipo_prop,
                                    umbral=umbral,
                                    cuota=cuota,
                                    temporada=temporada_sel,
                                    tipo_temporada=tipo_temporada_sel,
                                    es_over=tipo_apuesta == "Más de",
                                    filtro_local=localidad
                                )
                                st.markdown("### 📊 Resultado del Análisis")
                                st.code(resultado, language="markdown")
                            except Exception as e:
                                st.error(f"❌ Error al analizar la apuesta: {str(e)}")
                                st.write("Detalles del error:", str(e))
                else:
                    st.error("❌ No se encontró la columna PLAYER_NAME en los datos")
            else:
                st.error("❌ No se pudieron encontrar las columnas necesarias")
    except Exception as e:
        st.error(f"❌ Error al obtener datos: {str(e)}")
        st.write("Detalles técnicos:", str(e))
        st.write("Intente refrescar la página o contacte al soporte técnico")


