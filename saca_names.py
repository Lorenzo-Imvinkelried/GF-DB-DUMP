import os
import json

CARPETA_ENTRADA = "items_por_categoria"
ARCHIVO_SALIDA = "nombres_por_itemtype.txt"

def generar_reporte_nombres():
    if not os.path.exists(CARPETA_ENTRADA):
        print(f"[!] No se encontró la carpeta '{CARPETA_ENTRADA}/'. Ejecutá primero el script anterior para generar los JSONs por categoría.")
        return

    print("[*] Leyendo las categorías y extrayendo nombres en español...")

    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f_out:
        f_out.write("==================================================\n")
        f_out.write("       CATÁLOGO DE NOMBRES POR ITEMTYPE (0-60)    \n")
        f_out.write("==================================================\n\n")

        # Recorremos estrictamente del 0 al 60
        for itemtype in range(61):
            nombre_archivo = f"itemtype_{itemtype}.json"
            ruta_archivo = os.path.join(CARPETA_ENTRADA, nombre_archivo)

            f_out.write(f"ITEM TYPE: {itemtype}\n")
            
            # Verificamos si existe el archivo para este itemtype específico
            if os.path.exists(ruta_archivo):
                with open(ruta_archivo, "r", encoding="utf-8") as f_json:
                    items = json.load(f_json)

                elementos = []
                for item in items:
                    item_id = item.get("id", "N/A")
                    nombre_es = item.get("name_es", "").strip()
                    
                    if not nombre_es:
                        nombre_es = item.get("name_en", "Sin nombre")
                        
                    elementos.append(f"[ID: {item_id}, Nombre: {nombre_es}]")

                f_out.write("[\n    " + ",\n    ".join(elementos) + "\n]\n")
                print(f"[+] Procesado itemtype_{itemtype} ({len(items)} ítems)")
            else:
                f_out.write("[] (Categoría vacía o no existente en el set)\n")
                print(f"[-] itemtype_{itemtype} no encontrado.")

            f_out.write("\n" + "-" * 50 + "\n\n")

    print(f"\n[✓] ¡Reporte generado con éxito en '{ARCHIVO_SALIDA}'!")

if __name__ == "__main__":
    generar_reporte_nombres()
