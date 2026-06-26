import numpy as np
import control as ctrl
import matplotlib.pyplot as plt
import pandas as pd

# ==========================================
# 1. PARÁMETROS TEÓRICOS
# ==========================================
R, L, C = 50.0, 1e-3, 10e-9
den = [L*C, R*C, 1]

# Elegí tu filtro: Pasa Banda - Circuito 4
num_Banda = [R*C, 0]  
sistema = ctrl.TransferFunction(num_Banda, den)
nombre_filtro = "Filtro Pasa Banda (Circuito 4)"

# Cálculo Teórico
f_min, f_max = 1e3, 1e6
w = np.logspace(np.log10(2 * np.pi * f_min), np.log10(2 * np.pi * f_max), 1000)
mag, phase, omega = ctrl.bode(sistema, w, plot=False)

frec_teorica = omega / (2 * np.pi)
mag_teorica = 20 * np.log10(mag)

# Corrección de fase (unwrap) como vimos antes
fase_teorica = np.degrees(phase)
while fase_teorica[0] < -90:
    fase_teorica += 360

# ==========================================
# 2. CARGAR DATOS SIMULADOS (LTSpice)
# ==========================================
# Cambiá esta ruta por tu archivo .txt exportado del Bode de LTSpice
archivo_simulado = r'C:\Users\nachi\OneDrive\Escritorio\sim4.txt'

frec_sim = []
mag_sim = []
fase_sim = []

try:
    with open(archivo_simulado, 'r', encoding='latin1') as f:
        lineas = f.readlines()
        for linea in lineas:
            if not linea.strip() or linea.startswith("Freq."): continue
            partes = linea.strip().split('\t')
            if len(partes) == 2:
                frec_sim.append(float(partes[0]))
                # LTSpice exporta así: "(-15dB,45°)"
                datos = partes[1].replace('(', '').replace(')', '').split(',')
                mag_sim.append(float(datos[0].replace('dB', '')))
                fase_sim.append(float(datos[1].replace('°', '')))
except FileNotFoundError:
    print("No se encontró el archivo simulado. Omitiendo...")

# ==========================================
# 3. CARGAR DATOS PRÁCTICOS (CSV)
# ==========================================
# Cambiá esta ruta por tu archivo .csv medido
archivo_practico = r'C:\Users\nachi\OneDrive\Escritorio\f5_bodenotch.csv'
frec_prac = []
mag_prac = []
fase_prac = []

try:
    # Agregamos encoding='latin1' para que no tire error con el símbolo °
    # Agregamos skipinitialspace=True para limpiar los espacios en blanco molestos de los títulos
    df = pd.read_csv(archivo_practico, sep=',', encoding='latin1', skipinitialspace=True) 
    
    # Ponemos exactamente los nombres que están en tu archivo CSV
    #frec_prac = df['Frequency (Hz)'].values
    #mag_prac = df['Gain (dB)'].values
    #fase_prac = df['Phase (°)'].values 
    
except FileNotFoundError:
    print("No se encontró el archivo CSV práctico. Omitiendo...")
except KeyError as e:
    print(f"Error en el CSV: No se encontró la columna {e}. Revisá los nombres de las columnas.")

# ==========================================
# 4. GRAFICADO SUPERPUESTO
# ==========================================
fig, ax1 = plt.subplots(figsize=(10, 6))

# --- EJE MAGNITUD (ROJO) ---
# 1. Teórico (Línea continua)
ax1.semilogx(frec_teorica, mag_teorica, color='red', linestyle='-', linewidth=2, label='Mag. Teórica')
# 2. Simulado (Línea punteada)
if frec_sim:
    ax1.semilogx(frec_sim, mag_sim, color='darkred', linestyle='--', linewidth=2, label='Mag. Simulada')
# 3. Práctico (Puntos/Cruces sueltas)
if len(frec_prac) > 0:
    ax1.semilogx(frec_prac, mag_prac, color='orange', marker='x', linestyle='None', markersize=8, label='Mag. Medida')

ax1.set_xlabel('Frecuencia (Hz)', fontsize=12)
ax1.set_ylabel('Módulo (dB)', color='red', fontsize=12)
ax1.tick_params(axis='y', labelcolor='red')
ax1.set_xlim([1e3, 1e6])

# --- EJE FASE (AZUL) ---
ax2 = ax1.twinx()
# 1. Teórico (Línea continua)
ax2.semilogx(frec_teorica, fase_teorica, color='blue', linestyle='-', linewidth=2, alpha=0.7, label='Fase Teórica')
# 2. Simulado (Línea punteada)
if frec_sim:
    ax2.semilogx(frec_sim, fase_sim, color='darkblue', linestyle='--', linewidth=2, alpha=0.7, label='Fase Simulada')
# 3. Práctico (Puntos/Cruces sueltas)
if len(fase_prac) > 0:
    ax2.semilogx(frec_prac, fase_prac, color='cyan', marker='o', linestyle='None', markersize=5, label='Fase Medida')

ax2.set_ylabel('Fase (grados)', color='blue', fontsize=12)
ax2.tick_params(axis='y', labelcolor='blue')

# --- APAGAR GRILLAS Y UNIR LEYENDAS ---
ax1.grid(False, which='both')
ax2.grid(False, which='both')
ax1.tick_params(which='minor', length=0)
ax2.tick_params(which='minor', length=0)

lineas1, etiquetas1 = ax1.get_legend_handles_labels()
lineas2, etiquetas2 = ax2.get_legend_handles_labels()
# Ponemos la leyenda afuera o en un lugar que no moleste
ax1.legend(lineas1 + lineas2, etiquetas1 + etiquetas2, loc='upper right', fontsize=9)

plt.title(f'Comparativa Bode - {nombre_filtro}', fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.show()