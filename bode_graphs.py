import pandas as pd
import matplotlib.pyplot as plt

csv_path = "scope_10.csv"
df = pd.read_csv(csv_path, encoding='latin1')

fig, ax1 = plt.subplots()
ax1.set_xlabel('Frecuencia [Hz]')
ax1.set_ylabel('Ganancia [dB]')
ax1.plot(df.iloc[:, 1], df.iloc[:, 3], color='red')
ax1.tick_params(axis='y', labelcolor='red')

ax2 = ax1.twinx()
ax2.set_ylabel('Fase [°]')
ax2.plot(df.iloc[:, 1], df.iloc[:, 4], color='blue')
ax2.tick_params(axis='y', labelcolor='blue')    

fig.tight_layout()
plt.show()