import math
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
        ctk.CTk.__init__(self, *args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

# 3. Inherit from the new hybrid class instead of ctk.CTk
class CSVPlotterApp(CTkWindowWithDnD):
    def __init__(self):
        super().__init__()
        
        self.title("Análisis de Señales - Osciloscopio")
        self.geometry("600x720")
        
        self.time_file_path = ""
        self.freq_file_path = ""
        self.lissajous_file_path = ""
        self.time_signal_inputs = []
        self.freq_signal_inputs = []
        self.lissajous_columns = []
        self.unit_multipliers = {
            "s": 1, "ms": 1e3, "µs": 1e6, "ns": 1e9, "ps": 1e12,
            "V": 1, "mV": 1e3, "µV": 1e6, "nV": 1e9
        }
        
        # --- Pantalla de Selección Inicial ---
        self.selection_frame = ctk.CTkFrame(self)
        self.selection_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.selection_frame, text="¿Qué tipo de análisis desea realizar?", 
                     font=("Arial", 18, "bold")).pack(pady=40)
        
        self.btn_time = ctk.CTkButton(self.selection_frame, text="Respuesta en Tiempo", 
                                      command=lambda: self.select_mode("Tiempo"), width=200, height=50)
        self.btn_time.pack(pady=10)
        
        self.btn_freq = ctk.CTkButton(self.selection_frame, text="Respuesta en Frecuencia",
                                      command=lambda: self.select_mode("Frecuencia"), width=200, height=50)
        self.btn_freq.pack(pady=10)

        self.btn_lissajous = ctk.CTkButton(self.selection_frame, text="Figuras de Lissajous",
                                           command=lambda: self.select_mode("Lissajous"), width=200, height=50)
        self.btn_lissajous.pack(pady=10)

        # --- Contenedor de Pestañas (Oculto al inicio) ---
        self.tabview = ctk.CTkTabview(self)
        self.tab_time = self.tabview.add("Respuesta en Tiempo")
        self.tab_freq = self.tabview.add("Respuesta en Frecuencia")
        self.tab_lissajous = self.tabview.add("Figuras de Lissajous")

        self.setup_time_response_ui(self.tab_time)
        self.setup_freq_response_ui(self.tab_freq)
        self.setup_lissajous_ui(self.tab_lissajous)

        # --- 4. Drag and Drop Setup ---
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

        # Vincular la tecla Enter para generar el gráfico automáticamente
        self.bind("<Return>", self.on_enter_pressed)

    def on_enter_pressed(self, event):
        """Maneja la ejecución del gráfico al presionar Enter."""
        # Solo actuar si ya pasamos la pantalla de selección inicial
        if not self.tabview.winfo_ismapped():
            return
            
        current_tab = self.tabview.get()
        if current_tab == "Respuesta en Tiempo" and self.time_plot_btn.cget("state") == "normal":
            self.plot_data()
        elif current_tab == "Respuesta en Frecuencia" and self.freq_plot_btn.cget("state") == "normal":
            self.plot_freq_data()
        elif current_tab == "Figuras de Lissajous" and self.lissajous_plot_btn.cget("state") == "normal":
            self.plot_lissajous()

    def select_mode(self, mode):
        """Cambia de la pantalla de selección a las pestañas"""
        self.selection_frame.pack_forget()
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        if mode == "Tiempo":
            self.tabview.set("Respuesta en Tiempo")
        elif mode == "Frecuencia":
            self.tabview.set("Respuesta en Frecuencia")
        else:
            self.tabview.set("Figuras de Lissajous")

    def setup_time_response_ui(self, parent):
        """Configura la interfaz original de respuesta en tiempo dentro de un parent"""
        self.time_label = ctk.CTkLabel(parent, text="Selecciona o arrastra un archivo CSV aquí", font=("Arial", 16, "bold"))
        self.time_label.pack(pady=10)
        
        # Button to browse for file
        self.time_browse_btn = ctk.CTkButton(parent, text="Buscar CSV", command=self.browse_file)
        self.time_browse_btn.pack(pady=5)
        
        # Label to show selected file path
        self.time_path_label = ctk.CTkLabel(parent, text="No fue seleccionado ningún archivo", font=("Arial", 10, "italic"), text_color="gray")
        self.time_path_label.pack(pady=5)
        
        # Frame con scroll para los parámetros de cada señal
        self.time_scroll_frame = ctk.CTkScrollableFrame(parent, width=500, height=180, label_text="Configuración por Señal")
        self.time_scroll_frame.pack(pady=5, padx=10)
        
        # Frame para opciones de visualización
        self.time_options_frame = ctk.CTkScrollableFrame(parent, height=105, label_text="Opciones del Gráfico")
        self.time_options_frame.pack(pady=2, padx=10, fill="x")
        self.time_options_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="col")

        # Row 0: Title
        title_row_frame = ctk.CTkFrame(self.time_options_frame, fg_color="transparent")
        title_row_frame.grid(row=0, column=0, columnspan=6, pady=2)
        ctk.CTkLabel(title_row_frame, text="Título:").pack(side="left", padx=5)
        self.title_entry = ctk.CTkEntry(title_row_frame, width=200, placeholder_text="Nombre del gráfico...")
        self.title_entry.insert(0, "Osciloscopio - Señales")
        self.title_entry.pack(side="left", padx=5)

        # Row 1: All checkboxes + grid width in one row
        self.log_x_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.time_options_frame, text="Eje X Log", variable=self.log_x_var).grid(row=1, column=0, padx=5, pady=4)

        self.log_y_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.time_options_frame, text="Eje Y Log", variable=self.log_y_var).grid(row=1, column=1, padx=5, pady=4)

        self.show_peaks_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.time_options_frame, text="Ver Max/Min", variable=self.show_peaks_var).grid(row=1, column=2, padx=5, pady=4)

        self.show_cursors_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.time_options_frame, text="Ver Cursores", variable=self.show_cursors_var).grid(row=1, column=3, padx=5, pady=4)

        self.show_grid_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.time_options_frame, text="Ver Grilla", variable=self.show_grid_var).grid(row=1, column=4, padx=5, pady=4)

        grid_width_frame = ctk.CTkFrame(self.time_options_frame, fg_color="transparent")
        grid_width_frame.grid(row=1, column=5, padx=5, pady=4)
        ctk.CTkLabel(grid_width_frame, text="Grosor:").pack(side="left")
        self.grid_width_entry = ctk.CTkEntry(grid_width_frame, width=50)
        self.grid_width_entry.insert(0, "0.6")
        self.grid_width_entry.pack(side="left", padx=5)

        # Row 2: Both axis scale settings in one row
        scale_frame = ctk.CTkFrame(self.time_options_frame, fg_color="transparent")
        scale_frame.grid(row=2, column=0, columnspan=6, pady=4)

        ctk.CTkLabel(scale_frame, text="Eje X:").pack(side="left", padx=2)
        self.unit_x_menu = ctk.CTkOptionMenu(scale_frame, values=["s", "ms", "µs", "ns", "ps"], width=75)
        self.unit_x_menu.set("µs")
        self.unit_x_menu.pack(side="left", padx=2)
        ctk.CTkLabel(scale_frame, text="Div:").pack(side="left", padx=2)
        self.grid_spacing_x_entry = ctk.CTkEntry(scale_frame, width=50)
        self.grid_spacing_x_entry.pack(side="left", padx=2)

        ctk.CTkLabel(scale_frame, text="   Eje Y:").pack(side="left", padx=2)
        self.unit_y_menu = ctk.CTkOptionMenu(scale_frame, values=["V", "mV", "µV"], width=75)
        self.unit_y_menu.set("mV")
        self.unit_y_menu.pack(side="left", padx=2)
        ctk.CTkLabel(scale_frame, text="Div:").pack(side="left", padx=2)
        self.grid_spacing_y_entry = ctk.CTkEntry(scale_frame, width=50)
        self.grid_spacing_y_entry.pack(side="left", padx=2)

        self.time_plot_btn = ctk.CTkButton(parent, text="Graficar datos", command=self.plot_data, state="disabled", fg_color="green")
        self.time_plot_btn.pack(pady=15)

    def setup_freq_response_ui(self, parent):
        """Configura la interfaz de respuesta en frecuencia (análoga a tiempo)"""
        self.freq_label = ctk.CTkLabel(parent, text="Selecciona o arrastra un archivo CSV aquí", font=("Arial", 16, "bold"))
        self.freq_label.pack(pady=10)
        
        self.freq_browse_btn = ctk.CTkButton(parent, text="Buscar CSV", command=self.browse_file)
        self.freq_browse_btn.pack(pady=5)
        
        self.freq_path_label = ctk.CTkLabel(parent, text="No fue seleccionado ningún archivo", font=("Arial", 10, "italic"), text_color="gray")
        self.freq_path_label.pack(pady=5)
        
        # Panel de Mapeo de Columnas (Indices desde 0)
        mapping_frame = ctk.CTkFrame(parent)
        mapping_frame.pack(pady=5, fill="x", padx=10)
        mapping_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        
        ctk.CTkLabel(mapping_frame, text="Mapeo de Columnas (Índices desde 0):", 
                     font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=6, pady=5)
        
        ctk.CTkLabel(mapping_frame, text="Freq:").grid(row=1, column=0, padx=2, sticky="e")
        self.freq_col_idx = ctk.CTkEntry(mapping_frame, width=50); self.freq_col_idx.insert(0, "1")
        self.freq_col_idx.grid(row=1, column=1, padx=2, sticky="w", pady=5)
        
        ctk.CTkLabel(mapping_frame, text="Gan:").grid(row=1, column=2, padx=2, sticky="e")
        self.gain_col_idx = ctk.CTkEntry(mapping_frame, width=50); self.gain_col_idx.insert(0, "3")
        self.gain_col_idx.grid(row=1, column=3, padx=2, sticky="w", pady=5)
        
        ctk.CTkLabel(mapping_frame, text="Fase:").grid(row=1, column=4, padx=2, sticky="e")
        self.phase_col_idx = ctk.CTkEntry(mapping_frame, width=50); self.phase_col_idx.insert(0, "4")
        self.phase_col_idx.grid(row=1, column=5, padx=2, sticky="w", pady=5)

        self.freq_scroll_frame = ctk.CTkScrollableFrame(parent, width=500, height=150, label_text="Configuración por Señal")
        self.freq_scroll_frame.pack(pady=5, padx=10)

        self.freq_options_frame = ctk.CTkScrollableFrame(parent, height=140, label_text="Opciones de Frecuencia")
        self.freq_options_frame.pack(pady=2, padx=10, fill="x")
        self.freq_options_frame.grid_columnconfigure((0, 1), weight=1, uniform="col")

        freq_title_row_frame = ctk.CTkFrame(self.freq_options_frame, fg_color="transparent")
        freq_title_row_frame.grid(row=0, column=0, columnspan=2, pady=2)
        ctk.CTkLabel(freq_title_row_frame, text="Título:").pack(side="left", padx=5)
        self.freq_title_entry = ctk.CTkEntry(freq_title_row_frame, width=200, placeholder_text="Nombre del gráfico...")
        self.freq_title_entry.insert(0, "Respuesta en Frecuencia")
        self.freq_title_entry.pack(side="left", padx=5)

        self.freq_show_peaks_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.freq_options_frame, text="Ver Max/Min", variable=self.freq_show_peaks_var).grid(row=1, column=0, padx=10, pady=2, sticky="e")

        self.freq_show_cursors_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.freq_options_frame, text="Ver Cursores", variable=self.freq_show_cursors_var).grid(row=1, column=1, padx=10, pady=2, sticky="w")

        self.freq_show_grid_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.freq_options_frame, text="Ver Grilla", variable=self.freq_show_grid_var).grid(row=2, column=0, padx=10, pady=2, sticky="e")

        grid_width_frame = ctk.CTkFrame(self.freq_options_frame, fg_color="transparent")
        grid_width_frame.grid(row=2, column=1, padx=10, pady=2, sticky="w")
        ctk.CTkLabel(grid_width_frame, text="Grosor:").pack(side="left")
        self.freq_grid_width_entry = ctk.CTkEntry(grid_width_frame, width=50)
        self.freq_grid_width_entry.insert(0, "0.6")
        self.freq_grid_width_entry.pack(side="left", padx=5)

        self.freq_plot_btn = ctk.CTkButton(parent, text="Calcular FFT", command=self.plot_freq_data, state="disabled", fg_color="green")
        self.freq_plot_btn.pack(pady=15)

    def plot_freq_data(self):
        try:
            # 1. Obtener índices del mapeo
            f_idx = int(self.freq_col_idx.get())
            g_idx = int(self.gain_col_idx.get())
            p_idx = int(self.phase_col_idx.get())

            # 2. Obtener nombres de columnas reales para extraer los datos correctamente
            df_headers = pd.read_csv(self.freq_file_path, skiprows=[1], nrows=0, encoding='latin1')
            col_names = df_headers.columns
            
            f_name = col_names[f_idx]
            g_name = col_names[g_idx]
            p_name = col_names[p_idx]

            # 3. Leer solo las 3 columnas necesarias
            df = pd.read_csv(self.freq_file_path, skiprows=[1], encoding='latin1', usecols=[f_idx, g_idx, p_idx])
            if df.empty: return

            f_data = df[f_name]
            g_data = df[g_name]
            p_data = df[p_name]

            # 4. Usar configuración fija: índice 0 para Ganancia, índice 1 para Fase
            g_config = self.freq_signal_inputs[0]
            p_config = self.freq_signal_inputs[1]

            fig, ax1 = plt.subplots(figsize=(10, 6))
            ax2 = ax1.twinx()

            try:
                fg_width = float(self.freq_grid_width_entry.get())
            except ValueError:
                fg_width = 0.6

            g_color = g_config["color"].get()
            p_color = p_config["color"].get()

            # Ganancia en el eje izquierdo
            line_g, = ax1.semilogx(f_data, g_data, color=g_color, linewidth=1.5, label=g_config["alias"].get())
            ax1.set_ylabel(f'{g_config["alias"].get()} (dB)', color=g_color)
            ax1.tick_params(axis='y', labelcolor=g_color)
            ax1.grid(self.freq_show_grid_var.get(), which='both', linestyle='--', alpha=0.6, linewidth=fg_width)

            # Fase en el eje derecho
            line_p, = ax2.semilogx(f_data, p_data, color=p_color, linewidth=1.5, label=p_config["alias"].get())
            ax2.set_ylabel(f'{p_config["alias"].get()} (grados)', color=p_color)
            ax2.tick_params(axis='y', labelcolor=p_color)

            ax1.set_xlabel('Frecuencia (Hz)')

            # --- Tick synchronization ---
            # Phase ticks: 15° increments covering the data range
            step_p = 15
            p_min, p_max = float(p_data.min()), float(p_data.max())
            p_range = max(p_max - p_min, 1.0)
            p_lo = p_min - p_range * 0.05
            p_hi = p_max + p_range * 0.05

            first_p = math.floor(p_lo / step_p) * step_p
            phase_ticks = []
            t = first_p
            while t <= p_hi + 1e-9:
                phase_ticks.append(round(t, 6))
                t += step_p
            n = len(phase_ticks)

            # Gain ticks: same count n, step rounded to a nice number, first tick a round multiple
            g_min, g_max = float(g_data.min()), float(g_data.max())
            g_range = max(g_max - g_min, 1.0)
            g_lo = g_min - g_range * 0.05
            g_hi = g_max + g_range * 0.05

            ideal_step = (g_hi - g_lo) / max(n - 1, 1)
            nice_steps = [0.1, 0.2, 0.5, 1, 2, 3, 5, 10, 20, 25, 50, 100, 200]
            gain_step = min(nice_steps, key=lambda s: abs(s - ideal_step))

            first_g = math.floor(g_lo / gain_step) * gain_step
            gain_ticks = [first_g + i * gain_step for i in range(n)]

            # If gain ticks don't reach g_hi, extend both lists together to keep them in sync
            while gain_ticks[-1] < g_hi - 1e-9:
                gain_ticks.append(round(gain_ticks[-1] + gain_step, 10))
                phase_ticks.append(round(phase_ticks[-1] + step_p, 6))

            # ylim strictly from ticks so every grid line has a tick
            ax1.set_ylim(gain_ticks[0] - gain_step * 0.5, gain_ticks[-1] + gain_step * 0.5)
            ax1.set_yticks(gain_ticks)
            ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g'))

            ax2.set_ylim(phase_ticks[0] - step_p * 0.5, phase_ticks[-1] + step_p * 0.5)
            ax2.set_yticks(phase_ticks)
            ax2.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g'))

            # Anotaciones de Máximos y Mínimos
            if self.freq_show_peaks_var.get():
                idx_max_g = g_data.idxmax()
                ax1.annotate(f'Max: {g_data[idx_max_g]:.2g}', xy=(f_data[idx_max_g], g_data[idx_max_g]), xytext=(5, 5),
                             textcoords='offset points', color=g_color, fontweight='bold')
                idx_min_g = g_data.idxmin()
                ax1.annotate(f'Min: {g_data[idx_min_g]:.2g}', xy=(f_data[idx_min_g], g_data[idx_min_g]), xytext=(5, -15),
                             textcoords='offset points', color=g_color, fontweight='bold')

                idx_max_p = p_data.idxmax()
                ax2.annotate(f'Max: {p_data[idx_max_p]:.2g}', xy=(f_data[idx_max_p], p_data[idx_max_p]), xytext=(5, 5),
                             textcoords='offset points', color=p_color, fontweight='bold')
                idx_min_p = p_data.idxmin()
                ax2.annotate(f'Min: {p_data[idx_min_p]:.2g}', xy=(f_data[idx_min_p], p_data[idx_min_p]), xytext=(5, -15),
                             textcoords='offset points', color=p_color, fontweight='bold')

            if self.freq_show_cursors_var.get():
                mplcursors.cursor([line_g, line_p], hover=True)

            lines = [line_g, line_p]
            ax1.legend(lines, [l.get_label() for l in lines], loc='best')

            fig.suptitle(self.freq_title_entry.get() or "Respuesta en Frecuencia")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Error", f"Error al graficar respuesta en frecuencia: {e}")

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
        current_tab = self.tabview.get()
        short_name = path.replace("\\", "/").split("/")[-1]
        
        if current_tab == "Respuesta en Tiempo":
            self.time_file_path = path
            self.time_path_label.configure(text=f"Cargado: {short_name}", text_color="white")
            self.time_plot_btn.configure(state="normal")
        elif current_tab == "Figuras de Lissajous":
            self.lissajous_file_path = path
            self.lissajous_path_label.configure(text=f"Cargado: {short_name}", text_color="white")
            self.lissajous_plot_btn.configure(state="normal")
            self._populate_lissajous_columns(path)
            return
        else:
            self.freq_file_path = path
            self.freq_path_label.configure(text=f"Cargado: {short_name}", text_color="white")
            self.freq_plot_btn.configure(state="normal")

        self.setup_dynamic_inputs()

    def setup_dynamic_inputs(self):
        current_tab = self.tabview.get()
        if current_tab == "Respuesta en Tiempo":
            scroll_frame = self.time_scroll_frame
            file_path = self.time_file_path
            self.time_signal_inputs = []
            inputs_list = self.time_signal_inputs
            start_idx = 1 # Saltar x-axis
        else:
            scroll_frame = self.freq_scroll_frame
            file_path = self.freq_file_path
            self.freq_signal_inputs = []
            inputs_list = self.freq_signal_inputs
            start_idx = 0 # No se usa para el loop de frecuencia

        for widget in scroll_frame.winfo_children():
            widget.destroy()

        try:
            # Definir qué señales mostrar según la pestaña
            if current_tab == "Respuesta en Tiempo":
                df_headers = pd.read_csv(file_path, skiprows=[1], nrows=0)
                signals = df_headers.columns[start_idx:]
            else:
                # Respuesta en Frecuencia siempre tiene estos dos parámetros configurables
                signals = ["Ganancia", "Fase"]

            if current_tab == "Respuesta en Tiempo":
                ctk.CTkLabel(scroll_frame, text="Índices de columna con base 0  (col. 0 = tiempo)",
                             font=("Arial", 10, "italic"), text_color="gray").pack(pady=(4, 0))

            for i, col in enumerate(signals):
                frame = ctk.CTkFrame(scroll_frame)
                frame.pack(pady=5, fill="x", padx=5)

                frame.grid_columnconfigure((0, 1), weight=1, uniform="col")

                title_text = col if current_tab == "Respuesta en Frecuencia" else f"Señal: {col}"
                ctk.CTkLabel(frame, text=title_text, font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=2)

                # Checkbox "Incluir" solo para Tiempo
                enabled_var = ctk.BooleanVar(value=True)
                if current_tab == "Respuesta en Tiempo":
                    ctk.CTkCheckBox(frame, text="Incluir", variable=enabled_var).grid(row=1, column=0, columnspan=2, pady=2)

                name_row = 2 if current_tab == "Respuesta en Tiempo" else 1
                ctk.CTkLabel(frame, text="Nombre:").grid(row=name_row, column=0, padx=5, sticky="e")
                n_entry = ctk.CTkEntry(frame, width=120); n_entry.insert(0, col); n_entry.grid(row=name_row, column=1, pady=2, sticky="w")

                # Columna, Escala y Desplazamiento solo para Tiempo
                s_entry = d_entry = col_idx_entry = None
                if current_tab == "Respuesta en Tiempo":
                    ctk.CTkLabel(frame, text="Columna (idx):").grid(row=3, column=0, padx=5, sticky="e")
                    col_idx_entry = ctk.CTkEntry(frame, width=80)
                    col_idx_entry.insert(0, str(start_idx + i))
                    col_idx_entry.grid(row=3, column=1, pady=2, sticky="w")

                    ctk.CTkLabel(frame, text="Escala:").grid(row=4, column=0, padx=5, sticky="e")
                    s_entry = ctk.CTkEntry(frame, width=80); s_entry.insert(0, "1"); s_entry.grid(row=4, column=1, pady=2, sticky="w")

                    ctk.CTkLabel(frame, text="Despl. (mV):").grid(row=5, column=0, padx=5, sticky="e")
                    d_entry = ctk.CTkEntry(frame, width=80); d_entry.insert(0, "0"); d_entry.grid(row=5, column=1, pady=2, sticky="w")

                color_row = 6 if current_tab == "Respuesta en Tiempo" else 4
                ctk.CTkLabel(frame, text="Color:").grid(row=color_row, column=0, padx=5, sticky="e")

                # Función para actualizar el color visual del menú
                def set_color(choice, menu=None):
                    if menu:
                        menu.configure(fg_color=choice, button_color=choice, button_hover_color=choice)

                color_menu = ctk.CTkOptionMenu(frame, values=["blue", "red", "green", "orange", "purple", "black", "cyan", "magenta"], width=100)
                color_menu.configure(command=lambda c, m=color_menu: set_color(c, m))

                default_colors = ["blue", "red", "green", "orange", "purple", "black", "cyan", "magenta"]
                initial_color = default_colors[i % len(default_colors)]
                color_menu.set(initial_color)
                set_color(initial_color, color_menu)
                color_menu.grid(row=color_row, column=1, pady=2, sticky="w")

                inputs_list.append({
                    "name": col, "alias": n_entry, "scale": s_entry,
                    "disp": d_entry, "color": color_menu, "col_idx": col_idx_entry,
                    "enabled": enabled_var
                })
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer columnas: {e}")

    def plot_data(self):
        try:
            df = pd.read_csv(self.time_file_path, skiprows=[1])
            if df.empty:
                messagebox.showerror("Error", "The selected CSV file is empty.")
                return
            if len(df.columns) < 2:
                messagebox.showerror("Error", "The CSV must have at least 2 columns (X and Y).")
                return

            u_x = self.unit_x_menu.get()
            u_y = self.unit_y_menu.get()
            x_data = df.iloc[:, 0] * self.unit_multipliers[u_x]

            # base_div is the mV/div at scale=1; actual div per signal = base_div / scale
            try:
                base_div = float(self.grid_spacing_y_entry.get()) if self.grid_spacing_y_entry.get().strip() else None
            except ValueError:
                base_div = None

            try:
                g_width = float(self.grid_width_entry.get())
            except ValueError:
                g_width = 0.6

            try:
                x_spacing = float(self.grid_spacing_x_entry.get()) if self.grid_spacing_x_entry.get().strip() else None
            except ValueError:
                x_spacing = None

            nice_steps = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]

            def resolve_div(scale, y_min, y_max):
                if base_div is not None and scale > 0:
                    return base_div / scale
                y_range = max(y_max - y_min, 1e-9)
                return min(nice_steps, key=lambda s: abs(s - y_range / 6))

            def n_bounds(y_min, y_max, div):
                # Number of ticks below and above zero needed to cover the data range
                return (math.ceil(max(-y_min, 0) / div) + 1,
                        math.ceil(max(y_max, 0) / div) + 1)

            def build_ticks(div, n_below, n_above):
                # Ticks centered on zero: 0 is always at index n_below
                return [round((-n_below + i) * div, 10) for i in range(n_below + n_above + 1)]

            def parse_sig(sig):
                try:
                    scale = float(sig["scale"].get())
                except (ValueError, AttributeError):
                    scale = 1.0
                try:
                    disp = float(sig["disp"].get())
                except (ValueError, AttributeError):
                    disp = 0.0
                try:
                    col_idx = int(sig["col_idx"].get())
                except (ValueError, AttributeError):
                    col_idx = None
                if col_idx is not None:
                    y = df.iloc[:, col_idx] * self.unit_multipliers[u_y] + disp
                else:
                    y = df[sig["name"]] * self.unit_multipliers[u_y] + disp
                return scale, y

            def annotate_peaks(ax, y_data, sig):
                color, alias = sig["color"].get(), sig["alias"].get()
                max_idx = y_data.idxmax()
                ax.annotate(f'{alias} Max: {y_data[max_idx]:.2g}',
                            xy=(x_data[max_idx], y_data[max_idx]),
                            xytext=(5, 5), textcoords='offset points',
                            color=color, fontsize=9, fontweight='bold')
                min_idx = y_data.idxmin()
                ax.annotate(f'{alias} Min: {y_data[min_idx]:.2g}',
                            xy=(x_data[min_idx], y_data[min_idx]),
                            xytext=(5, -15), textcoords='offset points',
                            color=color, fontsize=9, fontweight='bold')

            signals = [s for s in self.time_signal_inputs if s["enabled"].get()]
            if not signals:
                messagebox.showwarning("Aviso", "No hay señales seleccionadas para graficar.")
                return

            for pair_start in range(0, len(signals), 2):
                pair = signals[pair_start:pair_start + 2]
                fig, ax1 = plt.subplots(figsize=(10, 6))
                fig.suptitle(self.title_entry.get() or "Osciloscopio - Señales")
                ax2 = None

                sig1 = pair[0]
                scale1, y1 = parse_sig(sig1)

                if len(pair) == 2:
                    sig2 = pair[1]
                    scale2, y2 = parse_sig(sig2)
                    same_scale = abs(scale1 - scale2) < 1e-9
                else:
                    sig2, scale2, y2 = None, None, None
                    same_scale = True

                if same_scale:
                    # Single Y axis — covers both signals' range
                    all_min = float(y1.min()) if y2 is None else float(min(y1.min(), y2.min()))
                    all_max = float(y1.max()) if y2 is None else float(max(y1.max(), y2.max()))
                    div = resolve_div(scale1, all_min, all_max)
                    nb, na = n_bounds(all_min, all_max, div)
                    ticks = build_ticks(div, nb, na)

                    line1, = ax1.plot(x_data, y1, color=sig1["color"].get(), label=sig1["alias"].get())
                    lines = [line1]
                    if sig2 is not None:
                        line2, = ax1.plot(x_data, y2, color=sig2["color"].get(), label=sig2["alias"].get())
                        lines.append(line2)

                    ax1.set_ylabel(f'Voltaje ({u_y})')
                    ax1.set_xlabel(f'Tiempo ({u_x})')
                    ax1.set_yticks(ticks)
                    ax1.set_ylim(ticks[0] - div * 0.5, ticks[-1] + div * 0.5)
                    ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g'))
                    ax1.grid(self.show_grid_var.get(), linestyle='--', alpha=0.6, linewidth=g_width)

                    if self.show_peaks_var.get():
                        annotate_peaks(ax1, y1, sig1)
                        if sig2 is not None:
                            annotate_peaks(ax1, y2, sig2)

                else:
                    # Dual Y axes — ticks built symmetrically around zero so both zero lines coincide
                    div1 = resolve_div(scale1, float(y1.min()), float(y1.max()))
                    div2 = resolve_div(scale2, float(y2.min()), float(y2.max()))

                    nb1, na1 = n_bounds(float(y1.min()), float(y1.max()), div1)
                    nb2, na2 = n_bounds(float(y2.min()), float(y2.max()), div2)
                    # Use the same n_below/n_above for both axes so zero is at the same grid line
                    n_below = max(nb1, nb2)
                    n_above = max(na1, na2)

                    ticks1 = build_ticks(div1, n_below, n_above)
                    ticks2 = build_ticks(div2, n_below, n_above)

                    line1, = ax1.plot(x_data, y1, color=sig1["color"].get(), label=sig1["alias"].get())
                    ax1.set_ylabel(f'{sig1["alias"].get()} ({u_y})', color=sig1["color"].get())
                    ax1.tick_params(axis='y', labelcolor=sig1["color"].get())
                    ax1.set_xlabel(f'Tiempo ({u_x})')
                    lines = [line1]

                    ax2 = ax1.twinx()
                    line2, = ax2.plot(x_data, y2, color=sig2["color"].get(), label=sig2["alias"].get())
                    ax2.set_ylabel(f'{sig2["alias"].get()} ({u_y})', color=sig2["color"].get())
                    ax2.tick_params(axis='y', labelcolor=sig2["color"].get())
                    lines.append(line2)

                    ax1.set_yticks(ticks1)
                    ax1.set_ylim(ticks1[0] - div1 * 0.5, ticks1[-1] + div1 * 0.5)
                    ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g'))
                    ax1.grid(self.show_grid_var.get(), linestyle='--', alpha=0.6, linewidth=g_width)

                    ax2.set_yticks(ticks2)
                    ax2.set_ylim(ticks2[0] - div2 * 0.5, ticks2[-1] + div2 * 0.5)
                    ax2.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g'))

                    if self.show_peaks_var.get():
                        annotate_peaks(ax1, y1, sig1)
                        annotate_peaks(ax2, y2, sig2)

                if x_spacing:
                    ax1.xaxis.set_major_locator(ticker.MultipleLocator(x_spacing))

                if self.log_x_var.get():
                    ax1.set_xscale('symlog')
                if self.log_y_var.get():
                    ax1.set_yscale('symlog')
                    if ax2:
                        ax2.set_yscale('symlog')

                if self.show_cursors_var.get():
                    mplcursors.cursor(lines, hover=True)

                ax1.legend(lines, [l.get_label() for l in lines], loc='best')
                plt.tight_layout()

            plt.show()

        except Exception as e:
            messagebox.showerror("Error", f"Could not parse or plot data.\nDetails: {e}")

    def setup_lissajous_ui(self, parent):
        """Configura la interfaz para figuras de Lissajous."""
        ctk.CTkLabel(parent, text="Selecciona o arrastra un archivo CSV aquí",
                     font=("Arial", 16, "bold")).pack(pady=10)

        ctk.CTkButton(parent, text="Buscar CSV", command=self.browse_file).pack(pady=5)

        self.lissajous_path_label = ctk.CTkLabel(parent, text="No fue seleccionado ningún archivo",
                                                  font=("Arial", 10, "italic"), text_color="gray")
        self.lissajous_path_label.pack(pady=5)

        # Selección de columnas
        col_frame = ctk.CTkFrame(parent)
        col_frame.pack(pady=5, fill="x", padx=10)
        col_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(col_frame, text="Selección de Señales:", font=("Arial", 12, "bold")).grid(
            row=0, column=0, columnspan=4, pady=5)

        ctk.CTkLabel(col_frame, text="Eje X (CH):").grid(row=1, column=0, padx=5, sticky="e")
        self.lissajous_x_menu = ctk.CTkOptionMenu(col_frame, values=["—"], width=130)
        self.lissajous_x_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(col_frame, text="Eje Y (CH):").grid(row=1, column=2, padx=5, sticky="e")
        self.lissajous_y_menu = ctk.CTkOptionMenu(col_frame, values=["—"], width=130)
        self.lissajous_y_menu.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        # Opciones
        opts_frame = ctk.CTkScrollableFrame(parent, height=130, label_text="Opciones del Gráfico")
        opts_frame.pack(pady=5, padx=10, fill="x")
        opts_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="col")

        title_row = ctk.CTkFrame(opts_frame, fg_color="transparent")
        title_row.grid(row=0, column=0, columnspan=4, pady=2)
        ctk.CTkLabel(title_row, text="Título:").pack(side="left", padx=5)
        self.lissajous_title_entry = ctk.CTkEntry(title_row, width=200, placeholder_text="Nombre del gráfico...")
        self.lissajous_title_entry.insert(0, "Figura de Lissajous")
        self.lissajous_title_entry.pack(side="left", padx=5)

        self.lissajous_show_grid_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts_frame, text="Ver Grilla", variable=self.lissajous_show_grid_var).grid(
            row=1, column=0, padx=5, pady=4)

        self.lissajous_show_cursors_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts_frame, text="Ver Cursores", variable=self.lissajous_show_cursors_var).grid(
            row=1, column=1, padx=5, pady=4)

        self.lissajous_equal_aspect_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts_frame, text="Aspecto 1:1", variable=self.lissajous_equal_aspect_var).grid(
            row=1, column=2, padx=5, pady=4)

        color_frame = ctk.CTkFrame(opts_frame, fg_color="transparent")
        color_frame.grid(row=1, column=3, padx=5, pady=4)
        ctk.CTkLabel(color_frame, text="Color:").pack(side="left")

        def set_lissajous_color(choice):
            self.lissajous_color_menu.configure(fg_color=choice, button_color=choice, button_hover_color=choice)

        self.lissajous_color_menu = ctk.CTkOptionMenu(
            color_frame,
            values=["blue", "red", "green", "orange", "purple", "black", "cyan", "magenta"],
            width=100, command=set_lissajous_color)
        self.lissajous_color_menu.set("blue")
        set_lissajous_color("blue")
        self.lissajous_color_menu.pack(side="left", padx=5)

        # Unidades de los ejes
        units_row = ctk.CTkFrame(opts_frame, fg_color="transparent")
        units_row.grid(row=2, column=0, columnspan=4, pady=4)
        ctk.CTkLabel(units_row, text="Unidad X:").pack(side="left", padx=3)
        self.lissajous_unit_x = ctk.CTkOptionMenu(units_row, values=["V", "mV", "µV", "nV"], width=75)
        self.lissajous_unit_x.set("mV")
        self.lissajous_unit_x.pack(side="left", padx=3)
        ctk.CTkLabel(units_row, text="Unidad Y:").pack(side="left", padx=3)
        self.lissajous_unit_y = ctk.CTkOptionMenu(units_row, values=["V", "mV", "µV", "nV"], width=75)
        self.lissajous_unit_y.set("mV")
        self.lissajous_unit_y.pack(side="left", padx=3)

        self.lissajous_plot_btn = ctk.CTkButton(parent, text="Generar Lissajous",
                                                 command=self.plot_lissajous, state="disabled", fg_color="green")
        self.lissajous_plot_btn.pack(pady=15)

    def _populate_lissajous_columns(self, path):
        """Carga los nombres de columna del CSV y los pone en los menús X/Y."""
        try:
            df_headers = pd.read_csv(path, skiprows=[1], nrows=0, encoding='latin1')
            self.lissajous_columns = list(df_headers.columns)
        except Exception:
            try:
                df_headers = pd.read_csv(path, nrows=0, encoding='latin1')
                self.lissajous_columns = list(df_headers.columns)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron leer columnas: {e}")
                return

        if not self.lissajous_columns:
            return

        self.lissajous_x_menu.configure(values=self.lissajous_columns)
        self.lissajous_y_menu.configure(values=self.lissajous_columns)

        # Defaults: segunda y tercera columna (primera suele ser tiempo)
        default_x = self.lissajous_columns[1] if len(self.lissajous_columns) > 1 else self.lissajous_columns[0]
        default_y = self.lissajous_columns[2] if len(self.lissajous_columns) > 2 else self.lissajous_columns[-1]
        self.lissajous_x_menu.set(default_x)
        self.lissajous_y_menu.set(default_y)

    def plot_lissajous(self):
        """Genera la figura de Lissajous graficando la señal Y vs señal X."""
        try:
            x_col = self.lissajous_x_menu.get()
            y_col = self.lissajous_y_menu.get()

            try:
                df = pd.read_csv(self.lissajous_file_path, skiprows=[1], encoding='latin1')
            except Exception:
                df = pd.read_csv(self.lissajous_file_path, encoding='latin1')

            if df.empty:
                messagebox.showerror("Error", "El archivo CSV está vacío.")
                return
            if x_col not in df.columns or y_col not in df.columns:
                messagebox.showerror("Error", f"Columnas '{x_col}' o '{y_col}' no encontradas.")
                return

            mx = self.unit_multipliers[self.lissajous_unit_x.get()]
            my = self.unit_multipliers[self.lissajous_unit_y.get()]
            x_data = df[x_col] * mx
            y_data = df[y_col] * my

            color = self.lissajous_color_menu.get()
            title = self.lissajous_title_entry.get() or "Figura de Lissajous"
            u_x = self.lissajous_unit_x.get()
            u_y = self.lissajous_unit_y.get()

            fig, ax = plt.subplots(figsize=(7, 7))
            line, = ax.plot(x_data, y_data, color=color, linewidth=1.2)

            ax.set_xlabel(f"{x_col} ({u_x})")
            ax.set_ylabel(f"{y_col} ({u_y})")
            ax.set_title(title)

            if self.lissajous_show_grid_var.get():
                ax.grid(True, linestyle='--', alpha=0.6)

            if self.lissajous_equal_aspect_var.get():
                ax.set_aspect('equal', adjustable='box')

            if self.lissajous_show_cursors_var.get():
                mplcursors.cursor(line, hover=True)

            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar figura de Lissajous:\n{e}")


if __name__ == "__main__":
    app = CSVPlotterApp()
    app.mainloop()