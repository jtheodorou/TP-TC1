import sys
import os

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np

    # 1. INTENTO DE RUTA AUTOMÁTICA INTELIGENTE
    nombre_archivo = 'transitorio.txt'
    ruta_archivo = os.path.join(os.getcwd(), nombre_archivo)

    # Si no se encuentra en la ruta por defecto, se intenta usando el directorio del script
    if not os.path.exists(ruta_archivo) and '__file__' in locals():
        directorio_script = os.path.dirname(os.path.abspath(__file__))
        ruta_archivo = os.path.join(directorio_script, nombre_archivo)

    # Si sigue sin aparecer, abrimos un buscador de archivos de Windows para que no crashee
    if not os.path.exists(ruta_archivo):
        print("🔍 No se encontró 'transitorio.txt' automáticamente.")
        print("📂 Por favor, seleccioná el archivo en la ventana emergente...")
        from tkinter import filedialog, Tk
        root = Tk()
        root.withdraw() # Esconder ventana principal de tkinter
        ruta_archivo = filedialog.askopenfilename(
            title="Seleccioná tu archivo transitorio.txt",
            filetypes=[("Archivos de texto", "*.txt")]
        )
        if not ruta_archivo:
            raise FileNotFoundError("No seleccionaste ningún archivo. Operación cancelada.")

    # 2. CARGA DE DATOS
    df = pd.read_csv(ruta_archivo, sep='\t')
    df.columns = df.columns.str.strip()

    # Pasar el tiempo a milisegundos
    df['time_ms'] = df['time'] * 1000
    time_ms = df['time_ms'].values
    vl = df['V(vo,P002)'].values
    ic = df['I(C1)'].values

    # Pseudofrecuencia teórica unificada exigida
    fd_fija = 12.78  # kHz

    # 3. BÚSQUEDA DEL PRIMER SOBREPICO REAL (Filtrando el inicio en t > 0.04 ms)
    idx_transitorio = np.where(time_ms > 0.04)[0]

    # Primer sobrepico de Voltaje
    idx_v_max = idx_transitorio[np.argmax(vl[idx_transitorio])]
    t_v_max = time_ms[idx_v_max]
    v_max = vl[idx_v_max]

    # Primer sobrepico de Corriente
    idx_i_max = idx_transitorio[np.argmax(ic[idx_transitorio])]
    t_i_max = time_ms[idx_i_max]
    i_max = ic[idx_i_max]

    # 4. GENERACIÓN DE LOS GRÁFICOS
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9), sharex=True)

    # --- GRÁFICO 1: VOLTAJE EN LA BOBINA (VL) ---
    ax1.plot(time_ms, vl, color='blue', label='Voltaje $V_L(t)$', linewidth=1.5)
    ax1.plot(t_v_max, v_max, 'ro', markersize=8, label='Sobrepico')
    
    # Cartel de Sobrepico bien alto en zona limpia
    ax1.annotate(f'Sobrepico: {v_max:.2f} V', xy=(t_v_max, v_max), 
                 xytext=(t_v_max + 0.04, v_max + 1.5),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6))

    # Cartel de Pseudofrecuencia abajo a la derecha
    ax1.text(0.75, 0.10, f'Pseudofrecuencia:\n$f_d = {fd_fija:.2f}$ kHz', 
             transform=ax1.transAxes, bbox=dict(facecolor='white', alpha=0.9, edgecolor='blue'), fontsize=10)

    ax1.set_title('Análisis Transitorio - Voltaje en la Bobina $V_L$', fontsize=12)
    ax1.set_ylabel('Voltaje (V)')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc='upper right')
    
    # Límites holgados en Y para que nada se solape
    ax1.set_ylim([np.min(vl) - 1, np.max(vl) + 3]) 

    # --- GRÁFICO 2: CORRIENTE EN EL CAPACITOR (IC) ---
    ax2.plot(time_ms, ic, color='orange', label='Corriente $I_C(t)$', linewidth=1.5)
    ax2.plot(t_i_max, i_max, 'ro', markersize=8, label='Sobrepico')
    
    # Cartel de Sobrepico bien alto en zona limpia
    ax2.annotate(f'Sobrepico: {i_max*1000:.1f} mA', xy=(t_i_max, i_max), 
                 xytext=(t_i_max + 0.04, i_max + 0.025),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6))

    # Cartel de Pseudofrecuencia abajo a la derecha
    ax2.text(0.75, 0.10, f'Pseudofrecuencia:\n$f_d = {fd_fija:.2f}$ kHz', 
             transform=ax2.transAxes, bbox=dict(facecolor='white', alpha=0.9, edgecolor='orange'), fontsize=10)

    ax2.set_title('Análisis Transitorio - Corriente en el Capacitor $I_C$', fontsize=12)
    ax2.set_xlabel('Tiempo (ms)')
    ax2.set_ylabel('Corriente (A)')
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend(loc='upper right')
    
    ax2.set_ylim([np.min(ic) - 0.02, np.max(ic) + 0.04])
    ax2.set_xlim([0, 0.4]) 

    plt.tight_layout()
    plt.show()

except Exception as e:
    print("\n❌ OCURRIÓ UN ERROR DETALLADO EN LA EJECUCIÓN:")
    import traceback
    traceback.print_exc()
    input("\nPresioná ENTER para cerrar...")