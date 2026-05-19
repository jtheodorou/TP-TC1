import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import mplcursors
import matplotlib.ticker as ticker

# 1. Import tkinterdnd2
from tkinterdnd2 import TkinterDnD, DND_FILES

# Set up CustomTkinter theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# 2. Create a hybrid window class to combine CustomTkinter with Drag and Drop
class CTkWindowWithDnD(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

# 3. Inherit from the new hybrid class instead of ctk.CTk
class CSVPlotterApp(CTkWindowWithDnD):
    def __init__(self):
        super().__init__()
        
        self.title("CSV Data Plotter")
        self.geometry("500x650")
        
        self.file_path = ""
        self.signal_inputs = []  # Lista para guardar los widgets de cada señal
        
        # --- UI Elements ---
        self.label = ctk.CTkLabel(self, text="Selecciona o arrastra un archivo CSV aquí", font=("Arial", 16, "bold"))
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
        
        # Frame para opciones de visualización (Escalas logarítmicas)
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(pady=5)
        
        self.log_x_var = ctk.BooleanVar(value=False)
        self.log_x_check = ctk.CTkCheckBox(self.options_frame, text="Eje X SymLog", variable=self.log_x_var)
        self.log_x_check.grid(row=0, column=0, padx=10)
        
        self.log_y_var = ctk.BooleanVar(value=False)
        self.log_y_check = ctk.CTkCheckBox(self.options_frame, text="Eje Y SymLog", variable=self.log_y_var)
        self.log_y_check.grid(row=0, column=1, padx=10)

        # Opciones de grilla
        self.show_grid_var = ctk.BooleanVar(value=True)
        self.show_grid_check = ctk.CTkCheckBox(self.options_frame, text="Ver Grilla", variable=self.show_grid_var)
        self.show_grid_check.grid(row=1, column=0, padx=10, pady=5)

        grid_width_frame = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        grid_width_frame.grid(row=1, column=1, padx=10, pady=5)
        ctk.CTkLabel(grid_width_frame, text="Grosor:").pack(side="left")
        self.grid_width_entry = ctk.CTkEntry(grid_width_frame, width=50)
        self.grid_width_entry.insert(0, "0.6")
        self.grid_width_entry.pack(side="left", padx=5)

        # Opciones de espaciado (tamaño de cuadriculas)
        grid_spacing_frame = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        grid_spacing_frame.grid(row=2, column=0, columnspan=2, pady=5)
        ctk.CTkLabel(grid_spacing_frame, text="Div. X (µs):").pack(side="left")
        self.grid_spacing_x_entry = ctk.CTkEntry(grid_spacing_frame, width=60)
        self.grid_spacing_x_entry.pack(side="left", padx=2)
        ctk.CTkLabel(grid_spacing_frame, text=" Div. Y (mV):").pack(side="left")
        self.grid_spacing_y_entry = ctk.CTkEntry(grid_spacing_frame, width=60)
        self.grid_spacing_y_entry.pack(side="left", padx=2)

        # Button to plot data (disabled until a file is loaded)
        self.plot_btn = ctk.CTkButton(self, text="Graficar datos", command=self.plot_data, state="disabled", fg_color="green")
        self.plot_btn.pack(pady=15)

        # --- 4. Drag and Drop Setup ---
        # Register the whole window as a drop target for files
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

    # --- 5. New Method to Handle Dropped Files ---
    def handle_drop(self, event):
        # Clean the file path (Windows sometimes adds curly braces if there are spaces in the path)
        dropped_file = event.data.strip('{}')
        
        # Validate that it is actually a CSV
        if dropped_file.lower().endswith('.csv'):
            self.load_csv(dropped_file)
        else:
            messagebox.showerror("Error", "El archivo debe ser un .csv")

    def browse_file(self):
        # Open a file dialog that only accepts CSV files
        file_selected = filedialog.askopenfilename(
            title="Select a CSV File",
            filetypes=[("CSV Files", "*.csv")]
        )
        
        if file_selected:
            self.load_csv(file_selected)

    def load_csv(self, path):
        self.file_path = path
        # Normalizar separadores de ruta para mostrar el nombre corto
        short_name = path.replace("\\", "/").split("/")[-1]
        self.path_label.configure(text=f"Cargado: {short_name}", text_color="white")
        self.plot_btn.configure(state="normal")
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
            
            for i, col in enumerate(signals):
                frame = ctk.CTkFrame(self.scroll_frame)
                frame.pack(pady=5, fill="x", padx=5)
                
                ctk.CTkLabel(frame, text=f"Señal: {col}", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=2)
                
                ctk.CTkLabel(frame, text="Nombre:").grid(row=1, column=0, padx=5)
                n_entry = ctk.CTkEntry(frame, width=120); n_entry.insert(0, col); n_entry.grid(row=1, column=1, pady=2)
                
                ctk.CTkLabel(frame, text="Escala:").grid(row=2, column=0, padx=5)
                s_entry = ctk.CTkEntry(frame, width=80); s_entry.insert(0, "1"); s_entry.grid(row=2, column=1, pady=2)
                
                ctk.CTkLabel(frame, text="Despl. (mV):").grid(row=3, column=0, padx=5)
                d_entry = ctk.CTkEntry(frame, width=80); d_entry.insert(0, "0"); d_entry.grid(row=3, column=1, pady=2)
                
                ctk.CTkLabel(frame, text="Color:").grid(row=4, column=0, padx=5)
                
                # Función para actualizar el color visual del menú
                def set_color(choice, menu=None):
                    if menu:
                        menu.configure(fg_color=choice, button_color=choice, button_hover_color=choice)

                color_menu = ctk.CTkOptionMenu(frame, values=["blue", "red", "green", "orange", "purple", "black", "cyan", "magenta"], width=100)
                color_menu.configure(command=lambda c, m=color_menu: set_color(c, m))
                
                default_colors = ["blue", "red", "green", "orange", "purple", "black", "cyan", "magenta"]
                initial_color = default_colors[i % len(default_colors)]
                color_menu.set(initial_color)
                set_color(initial_color, color_menu) # Aplicar color inicial
                color_menu.grid(row=4, column=1, pady=2)
                
                # Checkboxes para Max/Min
                max_var = ctk.BooleanVar(value=False)
                min_var = ctk.BooleanVar(value=False)
                ctk.CTkCheckBox(frame, text="Máximo", variable=max_var, font=("Arial", 10)).grid(row=5, column=0, padx=5, pady=2)
                ctk.CTkCheckBox(frame, text="Mínimo", variable=min_var, font=("Arial", 10)).grid(row=5, column=1, padx=5, pady=2)
                
                self.signal_inputs.append({
                    "name": col, "alias": n_entry, "scale": s_entry, 
                    "disp": d_entry, "color": color_menu,
                    "maxima_var": max_var, "minima_var": min_var
                })
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
            colors = []
            legend_labels = []
            # Primero, aplicar escala y desplazamiento a todas las señales
            for i, input_set in enumerate(self.signal_inputs):
                col_name = input_set["name"]
                try:
                    scale = float(input_set["scale"].get())
                    disp = float(input_set["disp"].get())
                    df[col_name] = df[col_name] * scale + disp
                    colors.append(input_set["color"].get())
                    legend_labels.append(input_set["alias"].get())
                except ValueError:
                    messagebox.showerror("Error", f"Valores inválidos en la señal {col_name}")
                    return

            # 3. Create the Matplotlib plot
            ax = df.plot(x='x-axis', y=df.columns[1:], kind='line', figsize=(10, 6), color=colors) 
            
            # Señalar máximos y mínimos si están seleccionados
            for input_set in self.signal_inputs:
                col_name = input_set["name"]
                alias = input_set["alias"].get()
                color = input_set["color"].get()
                
                if input_set["maxima_var"].get():
                    max_idx = df[col_name].idxmax()
                    max_x = df.loc[max_idx, 'x-axis']
                    max_y = df.loc[max_idx, col_name]
                    ax.annotate(f'{alias} Max: {max_y:.2g}', xy=(max_x, max_y), 
                                xytext=(5, 5), textcoords='offset points',
                                color=color, fontsize=9, fontweight='bold')
                
                if input_set["minima_var"].get():
                    min_idx = df[col_name].idxmin()
                    min_x = df.loc[min_idx, 'x-axis']
                    min_y = df.loc[min_idx, col_name]
                    ax.annotate(f'{alias} Min: {min_y:.2g}', xy=(min_x, min_y), 
                                xytext=(5, -15), textcoords='offset points',
                                color=color, fontsize=9, fontweight='bold')

            # Aplicar escalas logarítmicas si están seleccionadas
            if self.log_x_var.get():
                ax.set_xscale('symlog')
            if self.log_y_var.get():
                ax.set_yscale('symlog')

            # Customize the graph labels
            plt.xlabel('Tiempo (µs)')
            plt.ylabel('Voltaje (mV)')
            plt.title('Osciloscopio - Señales')
            
            # Aplicar configuración de grilla
            try:
                g_width = float(self.grid_width_entry.get())
            except ValueError:
                g_width = 0.6
            ax.grid(self.show_grid_var.get(), linestyle='--', alpha=0.6, linewidth=g_width)

            # Aplicar espaciado manual de la grilla (tamaño de cuadros)
            try:
                x_sp = self.grid_spacing_x_entry.get()
                if x_sp: ax.xaxis.set_major_locator(ticker.MultipleLocator(float(x_sp)))
                y_sp = self.grid_spacing_y_entry.get()
                if y_sp: ax.yaxis.set_major_locator(ticker.MultipleLocator(float(y_sp)))
            except ValueError:
                pass

            mplcursors.cursor(ax, hover=True)

            plt.legend(legend_labels)
            
            # 4. Display the graph window
            plt.show()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not parse or plot data.\nDetails: {e}")

if __name__ == "__main__":
    app = CSVPlotterApp()
    app.mainloop()