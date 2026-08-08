import json
import time
from playwright.sync_api import sync_playwright

# ==========================================
# CONFIGURACIÓN
# ==========================================
URL_BASE = "https://www.gfviolet.com.br/db"
ARCHIVO_SALIDA = "db_monsters_gfviolet.json"
TAMANO_LOTE = 50   

# --- FUNCIONES DEL ALGORITMO DE DETECCIÓN ---

def chequear_existencia(page, ids):
    """Envía un lote de IDs a la API y devuelve un diccionario de {id: True/False} si existen o no."""
    ids_js = str(ids)
    js_code = f"""async () => {{
        const ids = {ids_js};
        const requests = ids.map(async (id) => {{
            try {{
                const res = await fetch(`https://www.gfviolet.com.br/api/dbviolet/monsters/${{id}}/`);
                if (!res.ok) return [id, false];
                const json = await res.json();
                
                let isValid = false;
                if (json.data) {{
                    isValid = Array.isArray(json.data) ? json.data.length > 0 : Object.keys(json.data).length > 0;
                }} else {{
                    isValid = Array.isArray(json) ? json.length > 0 : Object.keys(json).length > 0;
                }}
                return [id, isValid];
            }} catch (e) {{
                return [id, false];
            }}
        }});
        const results = await Promise.all(requests);
        return Object.fromEntries(results);
    }}"""
    return page.evaluate(js_code)

def chequear_existencia_unico(page, id_num):
    resultados = chequear_existencia(page, [id_num])
    return resultados.get(str(id_num), False)

def detectar_limites(page):
    print("\n[*] 2. Ejecutando Algoritmo de Detección de Límites (Jump + Binary Search)...")
    STEP = 100
    MAX_SEARCH = 120000 # Escaneamos hasta 120k por si las moscas
    
    puntos_prueba = list(range(1, MAX_SEARCH + 1, STEP))
    
    print(f"    -> Fase 1: Exploración rápida (saltos de a {STEP} IDs). Buscando zonas pobladas...")
    resultados_barrido = {}
    
    # Batch processing para la exploración rápida
    lote_exploracion = 50
    for i in range(0, len(puntos_prueba), lote_exploracion):
        lote = puntos_prueba[i:i + lote_exploracion]
        resultados = chequear_existencia(page, lote)
        resultados_barrido.update(resultados)
        # Un pequeño respiro para no ahogar al servidor antes de empezar a scrapear
        time.sleep(0.1) 
        
    ids_validos = [int(k) for k, v in resultados_barrido.items() if v]
    
    if not ids_validos:
        print("    [!] No se encontró NINGÚN monstruo en el barrido. Asegurate de que la API responde.")
        return 1, 100
        
    primer_hit = min(ids_validos)
    ultimo_hit = max(ids_validos)
    
    print(f"    -> Zonas encontradas. Rango aproximado: {primer_hit} a {ultimo_hit}")
    print("    -> Fase 2: Cerrando espacios (Búsqueda Binaria) para acorralar el límite INFERIOR...")
    
    # Búsqueda Binaria para encontrar el mínimo exacto
    L = max(1, primer_hit - STEP + 1)
    R = primer_hit
    while L < R:
        mid = (L + R) // 2
        if chequear_existencia_unico(page, mid):
            R = mid # Si existe, el límite inferior debe estar acá o más abajo
        else:
            L = mid + 1 # Si no existe, el límite inferior está más arriba
            
    limite_inferior = L
    
    print("    -> Fase 3: Cerrando espacios (Búsqueda Binaria) para acorralar el límite SUPERIOR...")
    # Búsqueda Binaria para encontrar el máximo exacto
    L = ultimo_hit
    R = ultimo_hit + STEP - 1
    while L < R:
        mid = (L + R + 1) // 2
        if chequear_existencia_unico(page, mid):
            L = mid # Si existe, el límite superior debe estar acá o más arriba
        else:
            R = mid - 1 # Si no existe, el límite superior está más abajo
            
    limite_superior = L
    
    print(f"    [✓] ¡Límites exactos encontrados con éxito! Min: {limite_inferior} | Max: {limite_superior}\n")
    return limite_inferior, limite_superior

# --- SCRAPER PRINCIPAL ---

def extraer_monstruos_api():
    todos_los_monstruos = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("[*] 1. Entrando a la web para autorizar la sesión...")
        page.goto(URL_BASE, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)
        
        # Ejecutamos el algoritmo
        ID_INICIO, ID_FIN = detectar_limites(page)
        
        print(f"[*] 3. Iniciando extracción masiva desde el ID {ID_INICIO} hasta el {ID_FIN}...")
        
        for i in range(ID_INICIO, ID_FIN + 1, TAMANO_LOTE):
            rango_ids = list(range(i, min(i + TAMANO_LOTE, ID_FIN + 1)))
            ids_js_array = str(rango_ids)
            
            try:
                monsters_data = page.evaluate(f'''async () => {{
                    const ids = {ids_js_array};
                    const requests = ids.map(async (id) => {{
                        try {{
                            const res = await fetch(`https://www.gfviolet.com.br/api/dbviolet/monsters/${{id}}/`);
                            if (!res.ok) return null;
                            const json = await res.json();
                            return json.data ? json.data : json;
                        }} catch (e) {{
                            return null;
                        }}
                    }});
                    const results = await Promise.all(requests);
                    return results.filter(item => item !== null && (Array.isArray(item) ? item.length > 0 : Object.keys(item).length > 0));
                }}''')
                
                if monsters_data and len(monsters_data) > 0:
                    if isinstance(monsters_data[0], list):
                        for sublist in monsters_data:
                            todos_los_monstruos.extend(sublist)
                    else:
                        todos_los_monstruos.extend(monsters_data)
                        
                    print(f"[+] Lote {i} a {rango_ids[-1]} procesado. Monstruos extraídos: {len(monsters_data)}")
                else:
                    print(f"[-] Lote {i} a {rango_ids[-1]}: Vacío (Salteando hueco en la DB).")
                    
            except Exception as e:
                print(f"[!] Error en el lote {i}: {e}")
            
            time.sleep(1.0)
            
        browser.close()
        
    print("\n[*] Escribiendo archivo de monstruos en el disco...")
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as archivo:
        json.dump(todos_los_monstruos, archivo, ensure_ascii=False, indent=4)
        
    print(f"\n[✓] ¡Extracción Finalizada!")
    print(f"Se guardaron {len(todos_los_monstruos)} registros en '{ARCHIVO_SALIDA}'.")

if __name__ == "__main__":
    extraer_monstruos_api()
