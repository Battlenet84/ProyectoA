from odds_api import GoogleSheetsOddsLoader
import logging

# Configurar logging para ver todos los detalles
logging.basicConfig(level=logging.DEBUG)

# Mapeo de props para referencia
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
    'Puntos más Asistencias más Rebotes': 'PTS_AST_REB'
}

def normalize_prop_name(prop_name: str) -> str:
    """Normaliza el nombre de una prop para facilitar la comparación."""
    return prop_name.lower().replace(' + ', '_').replace('+', '_').replace(' ', '_')

def test_sheets():
    # ID del Google Sheet
    SPREADSHEET_ID = "1VTn80vGKu9MbAHZoV9UoVKYyPeVkh-6_N6DMNQInKQk"
    
    print("\nIniciando prueba de lectura de Google Sheets...")
    
    # Crear el loader
    loader = GoogleSheetsOddsLoader(SPREADSHEET_ID)
    
    try:
        # Intentar cargar las odds
        print("\nCargando odds...")
        odds = loader.load_odds()
        
        # Imprimir resultados
        print("\nResultados:")
        if not odds:
            print("No se encontraron odds")
        else:
            print(f"Se encontraron odds para {len(odds)} jugadores:")
            
            # Contadores para estadísticas
            total_props = 0
            props_mapeadas = 0
            props_no_mapeadas = set()
            
            for jugador, props in odds.items():
                print(f"\n{jugador}:")
                for prop in props:
                    total_props += 1
                    prop_name = prop['prop_name']
                    print(f"\n  Analizando prop: {prop_name}")
                    
                    # Intentar diferentes formas de mapeo
                    mapped = False
                    
                    # 1. Intento directo
                    if prop_name in prop_mapping:
                        print(f"  ✅ Mapeo directo: {prop_name} -> {prop_mapping[prop_name]}")
                        props_mapeadas += 1
                        mapped = True
                    else:
                        print(f"  ❌ No se encontró mapeo directo")
                        
                        # 2. Intento con normalización
                        prop_norm = normalize_prop_name(prop_name)
                        for key, value in prop_mapping.items():
                            if normalize_prop_name(key) == prop_norm:
                                print(f"  ✅ Mapeo normalizado: {prop_name} -> {value} (a través de {key})")
                                props_mapeadas += 1
                                mapped = True
                                break
                        
                        if not mapped:
                            print(f"  ❌ No se encontró mapeo normalizado")
                            props_no_mapeadas.add(prop_name)
                    
                    # Mostrar valores de la prop
                    if prop['over_line'] is not None:
                        print(f"    Over {prop['over_line']} @ {prop['over_odds']}")
                    if prop['under_line'] is not None:
                        print(f"    Under {prop['under_line']} @ {prop['under_odds']}")
            
            # Mostrar resumen
            print("\n=== RESUMEN ===")
            print(f"Total de props encontradas: {total_props}")
            print(f"Props mapeadas correctamente: {props_mapeadas}")
            print(f"Props sin mapear: {len(props_no_mapeadas)}")
            if props_no_mapeadas:
                print("\nProps que necesitan mapeo:")
                for prop in sorted(props_no_mapeadas):
                    print(f"  - {prop}")

    except Exception as e:
        print(f"\nError durante la prueba: {str(e)}")
        import traceback
        print("\nTraceback completo:")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_sheets() 