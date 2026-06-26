import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from spicelib import RawRead  # Lector nativo robusto
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'mc_output')

    if not os.path.exists(output_dir):
        print(f"No existe la carpeta {output_dir}. ¡Corré primero transitorio.py!")
        return

    # Buscamos todos los archivos .raw individuales (ignorando los .op.raw)
    all_raw_files = glob.glob(os.path.join(output_dir, '*.raw'))
    raw_files = [f for f in all_raw_files if not f.endswith('.op.raw')]

    if not raw_files:
        print(f"No se encontraron archivos de transitorio (.raw) en {output_dir}.")
        return

    print(f"Procesando {len(raw_files)} archivos de simulación con spicelib...")

    overshoots = []
    wd_values = []

    # Iteramos sobre cada archivo .raw individualmente
    for file_path in raw_files:
        try:
            # Leer el archivo actual
            LTR = RawRead(file_path)
            nodos_disponibles = LTR.get_trace_names()
            
            # Buscar el nombre correcto del nodo vo
            nodo_elegido = None
            for nombre in ['V(vo)', 'V(VO)', 'v(vo)', 'vo']:
                if nombre in nodos_disponibles:
                    nodo_elegido = nombre
                    break
            
            if nodo_elegido is None:
                # Si en este archivo particular no está el nodo, lo salteamos
                continue
            
            # Extraer las ondas (como son archivos individuales, usamos el índice 0)
            t = LTR.get_trace('time').get_wave(0)
            vo = LTR.get_trace(nodo_elegido).get_wave(0)
            
            if len(t) == 0 or len(vo) == 0:
                continue
                
            # --- Cálculo del Overshoot ---
            v_max = np.max(vo) 
            overshoots.append(v_max)
            
            # --- Cálculo de la Pseudofrecuencia (Wd) ---
            v_detrended = vo - np.mean(vo[-50:]) 
            zero_crossings = np.where(np.diff(np.sign(v_detrended)))[0]
            
            if len(zero_crossings) >= 2:
                t_crossings = t[zero_crossings]
                td = 2 * (t_crossings[1] - t_crossings[0])
                if td > 0:
                    wd = (2 * np.pi) / td
                    wd_values.append(wd)
                    
        except Exception as e:
            nombre_archivo = os.path.basename(file_path)
            print(f"Error procesando {nombre_archivo}: {e}")

    # 3. Graficar los Histogramas
    if not overshoots:
        print("\n[ALERTA] No se pudieron extraer datos de ningún archivo.")
        print("Verificá que las simulaciones no estén vacías y que el nodo se llame 'vo'.")
        return

    plt.figure(figsize=(12, 5))

    # Histograma del Overshoot
    plt.subplot(1, 2, 1)
    plt.hist(overshoots, bins=15, color='royalblue', edgecolor='black', alpha=0.7)
    plt.title('Distribución del Sobrepico Máximo ($V_{max}$)')
    plt.xlabel('Tensión Máxima [V]')
    plt.ylabel('Frecuencia (Cuentas)')
    plt.grid(True, linestyle='--', alpha=0.6)

    # Histograma de Wd
    plt.subplot(1, 2, 2)
    if wd_values:
        plt.hist(wd_values, bins=15, color='crimson', edgecolor='black', alpha=0.7)
        plt.title(r'Distribución de la Pseudofrecuencia ($\omega_d$)')
        plt.xlabel(r'$\omega_d$ [rad/s]')
        plt.ylabel('Frecuencia (Cuentas)')
    else:
        plt.text(0.5, 0.5, r'No se detectaron oscilaciones suficientes' + '\n' + r'para calcular $\omega_d$', 
                 ha='center', va='center', fontsize=12, color='red')
    plt.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        print("\n--------------------------------------------------")
        input("Presioná ENTER para cerrar...")