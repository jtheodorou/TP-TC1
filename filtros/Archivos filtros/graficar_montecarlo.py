import matplotlib.pyplot as plt

# 1. La ruta de tu archivo
archivo_ltspice = r'C:\Users\nachi\OneDrive\Escritorio\montecarloc.txt'

corridas_frec = []
corridas_mag = []

# --- Contador de corridas y Paleta de colores (MÉTODO ACTUALIZADO) ---
run_count = 0  
# Usamos plt.get_cmap en lugar de cm.get_cmap
colormap = plt.get_cmap('turbo') 

plt.figure(figsize=(10, 6))

# 2. Abrir el archivo y leerlo
with open(archivo_ltspice, 'r', encoding='latin1') as f:
    lineas = f.readlines()

for linea in lineas:
    linea = linea.strip()
    
    if not linea or linea.startswith("Freq."):
        continue
    
    if linea.startswith("Step"):
        if corridas_frec:
            # Dividimos por 100 para obtener un color distinto de la paleta
            color_linea = colormap(run_count / 100.0)
            
            # Graficamos con ese color
            plt.semilogx(corridas_frec, corridas_mag, color=color_linea, alpha=0.6)
            
            corridas_frec = []
            corridas_mag = []
            run_count += 1  
        continue
        
    partes = linea.split('\t')
    if len(partes) == 2:
        try:
            frec = float(partes[0])
            mag_str = partes[1].split('dB')[0].replace('(', '')
            mag = float(mag_str)
            
            corridas_frec.append(frec)
            corridas_mag.append(mag)
        except ValueError:
            pass

# Graficar la última corrida que quedó al final
if corridas_frec:
    color_linea = colormap(run_count / 100.0)
    plt.semilogx(corridas_frec, corridas_mag, color=color_linea, alpha=0.6)

# 3. Ajustes estéticos
fig = plt.gcf()
for ax in fig.axes:
    ax.grid(False, which='both')
    ax.tick_params(which='minor', length=0)

plt.title('Análisis de Montecarlo - Filtro Notch (Circuito 5) Variando C', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Frecuencia (Hz)', fontsize=12)
plt.ylabel('Módulo (dB)', fontsize=12)

plt.tight_layout()
plt.show()