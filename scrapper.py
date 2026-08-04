import json
import time
from playwright.sync_api import sync_playwright

# ==========================================
# CONFIGURACIÓN PARA MONSTRUOS
# ==========================================
URL_BASE = "https://gfviolet.com.br/db"
ARCHIVO_SALIDA = "db_monsters_gfviolet.json"

ID_INICIO = 1     
ID_FIN = 70000  # Podés ajustar este rango si descubrís hasta qué ID llega la tabla de bichos
TAMANO_LOTE = 50 

def extraer_monstruos_api():
    todos_los_monstruos = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("[*] 1. Entrando a la web para autorizar la sesión...")
        page.goto(URL_BASE, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)
        
        print("[+] ¡Adentro! Empezando a succionar la API de monstruos...")
        
        for i in range(ID_INICIO, ID_FIN + 1, TAMANO_LOTE):
            rango_ids = range(i, min(i + TAMANO_LOTE, ID_FIN + 1))
            ids_param = ",".join([str(id_num) for id_num in rango_ids])
            
            # LA ÚNICA DIFERENCIA: Cambiamos la ruta a /monsters/
            api_endpoint = f"https://gfviolet.com.br/api/dbviolet/monsters/?ids={ids_param}"
            
            try:
                json_response = page.evaluate(f'''async () => {{
                    const res = await fetch("{api_endpoint}");
                    if (!res.ok) return null;
                    return await res.json();
                }}''')
                
                if json_response and isinstance(json_response, dict) and 'data' in json_response:
                    monsters = json_response['data']
                    
                    if monsters and len(monsters) > 0:
                        todos_los_monstruos.extend(monsters)
                        print(f"[+] Lote {i} a {rango_ids[-1]} procesado. Monstruos extraídos: {len(monsters)}")
                    else:
                        print(f"[-] Lote {i} a {rango_ids[-1]}: Vacío.")
                else:
                    print(f"[-] Lote {i} a {rango_ids[-1]}: Vacío o sin formato esperado.")
                    
            except Exception as e:
                print(f"[!] Error en el lote {i}: {e}")
            
            time.sleep(1.0)
            
        browser.close()
        
    print("\n[*] Escribiendo archivo de monstruos en el disco...")
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as archivo:
        json.dump(todos_los_monstruos, archivo, ensure_ascii=False, indent=4)
        
    print(f"\n[✓] ¡Extracción de Monstruos Finalizada!")
    print(f"Se guardaron {len(todos_los_monstruos)} registros en '{ARCHIVO_SALIDA}'.")

if __name__ == "__main__":
    extraer_monstruos_api()
