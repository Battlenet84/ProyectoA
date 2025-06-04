import streamlit as st
from nba_stats import NBAStats
from bet_calculator import evaluar_prop_bet
from bet_scraper import BetScraper
import pandas as pd

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
        
        tipo_temporada_sel = st.selectbox(
            "🏆 Tipo de Temporada",
            nba.obtener_tipos_temporada(),
            index=0  # Por defecto temporada regular
        )
        
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
        elif 'PLAYER_NAME' not in df_jugadores.columns:
            st.error("❌ No se encontró la columna PLAYER_NAME en los datos")
        else:
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
                'FT_PCT': 'TL%'
            }
            
            # Verificar qué columnas están disponibles
            columnas_disponibles = []
            nuevos_nombres = []
            for col_original, col_nuevo in columnas_mostrar.items():
                if col_original in df_jugadores.columns:
                    columnas_disponibles.append(col_original)
                    nuevos_nombres.append(col_nuevo)
            
            if columnas_disponibles:
                # Crear DataFrame con las columnas disponibles
                df_mostrar = df_jugadores[columnas_disponibles].copy()
                df_mostrar.columns = nuevos_nombres
                
                # Si tenemos la columna de jugador, mantener el formato original
                if 'Jugador' in df_mostrar.columns:
                    # Ordenar por nombre completo
                    df_mostrar = df_mostrar.sort_values('Jugador')
                
                # Formatear porcentajes
                for col in ['FG%', '3P%', 'TL%']:
                    if col in df_mostrar.columns:
                        df_mostrar[col] = df_mostrar[col].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "-")
                
                # Formatear números decimales
                for col in ['MIN', 'PTS', 'AST', 'REB', 'ROB', 'TAP', 'PER']:
                    if col in df_mostrar.columns:
                        df_mostrar[col] = df_mostrar[col].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "-")
                
                # Ordenar por puntos (si está disponible)
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
            
            # Obtener lista de jugadores
            if 'PLAYER_NAME' in df_jugadores.columns:
                # Mantener los nombres en su orden natural
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
            else:
                st.error("❌ No se encontró la columna PLAYER_NAME en los datos")
    except Exception as e:
        st.error(f"❌ Error al obtener datos: {str(e)}")
        st.write("Intente refrescar la página o contacte al soporte técnico")


