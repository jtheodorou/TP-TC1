import pandas as pd
import matplotlib.pyplot as plt
import os

# Esto asegura que el programa busque el archivo en la misma carpeta donde está el script
directorio_actual = os.path.dirname(os.path.abspath(__file__))
ruta_archivo = os.path.join(directorio_actual, "scope_16.csv")

# Leemos el CSV saltando la fila de las unidades (segunda fila, índice 1)
df = pd.read_csv(ruta_archivo, skiprows=[1])
print("¡Archivo leído con éxito!")
print(df.head())
    
# Contar la cantidad de columnas
cantidad_columnas = len(df.columns)

# Multiplicamos por el factor
df['x-axis'] *= 1e6
df.iloc[:, 1:] = df.iloc[:, 1:] * 1e3

print(df.head())

y_displacement = 0
y_scale = 1

df.iloc[:, 1:] = df.iloc[:, 1:]*y_scale + y_displacement

df.plot(x='x-axis', y=df.columns[1:], kind='line', figsize=(10, 6))  
plt.xlabel('Tiempo (µs)')
plt.ylabel('Voltaje (mV)')
plt.title('Osciloscopio - Señales')
plt.grid(True)
plt.show()