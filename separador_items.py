import os
import json

ARCHIVO_MAESTRO = "db_items_gfviolet.json"
CARPETA_SALIDA = "items_por_categoria"
ARCHIVO_RESUMEN = "resumen_itemtypes.txt"

def organizar_y_resumir():
    if not os.path.exists(ARCHIVO_MAESTRO):
        print(f"[!] No se encontró el archivo {ARCHIVO_MAESTRO}.")
        return

    print("[*] Leyendo el archivo maestro...")
    with open(ARCHIVO_MAESTRO, "r", encoding="utf-8") as f:
        todos_los_items = json.load(f)

    print(f"[+] Total de ítems cargados: {len(todos_los_items)}")
    print("[*] Agrupando catálogos...")

    categorias = {}

    for item in todos_los_items:
        itemtype = item.get("itemtype", 0)
        
        if itemtype not in categorias:
            categorias[itemtype] = []
            
        # Copia íntegra de toda la data del ítem
        categorias[itemtype].append(item)

    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    # Lista para almacenar los datos del resumen
    datos_resumen = []

    print("[*] Guardando archivos JSON por categoría...")
    for itemtype, items_lista in categorias.items():
        nombre_archivo = f"itemtype_{itemtype}.json"
        ruta_archivo = os.path.join(CARPETA_SALIDA, nombre_archivo)

        with open(ruta_archivo, "w", encoding="utf-8") as f_out:
            json.dump(items_lista, f_out, ensure_ascii=False, indent=4)
            
        cantidad = len(items_lista)
        print(f"[+] Guardado: {nombre_archivo} ({cantidad} ítems)")
        
        # Guardamos para el reporte
        datos_resumen.append((itemtype, cantidad))

    # Ordenamos de mayor a menor cantidad de objetos para que quede más prolijo
    datos_resumen.sort(key=lambda x: x[1], reverse=True)

    print(f"[*] Generando archivo de resumen ({ARCHIVO_RESUMEN})...")
    with open(ARCHIVO_RESUMEN, "w", encoding="utf-8") as f_resumen:
        f_resumen.write("==================================================\n")
        f_resumen.write("       RESUMEN DE CATEGORÍAS (ITEMTYPES)          \n")
        f_resumen.write("==================================================\n")
        f_resumen.write(f"{'ITEMTYPE':<12} | {'CANTIDAD DE OBJETOS':<20}\n")
        f_resumen.write("--------------------------------------------------\n")
        
        for itemtype, cantidad in datos_resumen:
            f_resumen.write(f"itemtype_{itemtype:<4} | {cantidad:<20}\n")
            
        f_resumen.write("--------------------------------------------------\n")
        f_resumen.write(f"Total de categorías únicas: {len(datos_resumen)}\n")
        f_resumen.write(f"Total general de ítems: {len(todos_los_items)}\n")

    print(f"\n[✓] ¡Proceso completado con éxito!")
    print(f"-> Archivos JSON en: '{CARPETA_SALIDA}/'")
    print(f"-> Reporte de texto en: '{ARCHIVO_RESUMEN}'")

if __name__ == "__main__":
    organizar_y_resumir()
