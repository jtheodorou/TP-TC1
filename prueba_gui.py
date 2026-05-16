import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt

# Set up CustomTkinter theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class CSVPlotterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("CSV Data Plotter")
        self.geometry("500x650")
        
        self.file_path = ""
        self.signal_inputs = []  # Lista para guardar los widgets de cada señal
        
        # --- UI Elements ---
        self.label = ctk.CTkLabel(self, text="Selecciona un archivo CSV", font=("Arial", 16, "bold"))
        self.label.pack(pady=10)
        
        # Button to browse for file
        self.browse_btn = ctk.CTkButton(self, text="Buscar CSV", command=self.browse_file)
        self.browse_btn.pack(pady=5)
        
        # Label to show selected file path
        self.path_label = ctk.CTkLabel(self, text="No fue seleccionado ningún archivo", font=("Arial", 10, "italic"), text_color="gray")
        self.path_label.pack(pady=5)
        
        # Frame con scroll para los parámetros de cada señal
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=450, height=300, label_text="Configuración por Señal")
        self.scroll_frame.pack(pady=10, padx=10)

        # Button to plot data (disabled until a file is loaded)
        self.plot_btn = ctk.CTkButton(self, text="Graficar datos", command=self.plot_data, state="disabled", fg_color="green")
        self.plot_btn.pack(pady=15)

    def browse_file(self):
        # Open a file dialog that only accepts CSV files
        file_selected = filedialog.askopenfilename(
            title="Select a CSV File",
            filetypes=[("CSV Files", "*.csv")]
        )
        
        if file_selected:
            self.file_path = file_selected
            # Show shortened file name in the GUI
            short_name = file_selected.split("/")[-1]
            self.path_label.configure(text=f"Cargado: {short_name}", text_color="white")
            # Enable the graph button
            self.plot_btn.configure(state="normal")
            
            # Generar campos dinámicos
            self.setup_dynamic_inputs()

    def setup_dynamic_inputs(self):
        # Limpiar entradas anteriores
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.signal_inputs = []

        try:
            # Leemos solo la cabecera para saber las columnas
            df_headers = pd.read_csv(self.file_path, skiprows=[1], nrows=0)
            signals = df_headers.columns[1:] # Ignoramos el x-axis

            for col in signals:
                frame = ctk.CTkFrame(self.scroll_frame)
                frame.pack(pady=5, fill="x", padx=5)
                
                ctk.CTkLabel(frame, text=f"Señal: {col}", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=2)
                
                ctk.CTkLabel(frame, text="Escala:").grid(row=1, column=0, padx=5)
                s_entry = ctk.CTkEntry(frame, width=80); s_entry.insert(0, "1"); s_entry.grid(row=1, column=1, pady=2)
                
                ctk.CTkLabel(frame, text="Despl. (mV):").grid(row=2, column=0, padx=5)
                d_entry = ctk.CTkEntry(frame, width=80); d_entry.insert(0, "0"); d_entry.grid(row=2, column=1, pady=2)
                
                self.signal_inputs.append({"name": col, "scale": s_entry, "disp": d_entry})
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer columnas: {e}")

    def plot_data(self):
        try:
            # 1. Read the CSV using Pandas
            df = pd.read_csv(self.file_path, skiprows=[1])  # Skip the second row if it contains units
            
            # Quick check to ensure the CSV actually has data
            if df.empty:
                messagebox.showerror("Error", "The selected CSV file is empty.")
                return
            
            # 2. Determine columns to plot
            # For simplicity, we use the 1st column as X and the 2nd column as Y
            if len(df.columns) < 2:
                messagebox.showerror("Error", "The CSV must have at least 2 columns (X and Y).")
                return
                
            df['x-axis'] *= 1e6
            df.iloc[:, 1:] = df.iloc[:, 1:] * 1e3
            
            # Aplicar parámetros individuales
            for i, input_set in enumerate(self.signal_inputs):
                col_name = input_set["name"]
                try:
                    scale = float(input_set["scale"].get())
                    disp = float(input_set["disp"].get())
                    df[col_name] = df[col_name] * scale + disp
                except ValueError:
                    messagebox.showerror("Error", f"Valores inválidos en la señal {col_name}")
                    return

            # 3. Create the Matplotlib plot
            df.plot(x='x-axis', y=df.columns[1:], kind='line', figsize=(10, 6)) 
            
            # Customize the graph labels
            plt.xlabel('Tiempo (µs)')
            plt.ylabel('Voltaje (mV)')
            plt.title('Osciloscopio - Señales')
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.legend()
            
            # 4. Display the graph window
            plt.show()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not parse or plot data.\nDetails: {e}")

if __name__ == "__main__":
    app = CSVPlotterApp()
    app.mainloop()