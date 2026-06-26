import math
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import mplcursors
import matplotlib.ticker as ticker
from tkinterdnd2 import TkinterDnD, DND_FILES

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

COLORS = ["blue", "red", "green", "orange", "purple", "black", "cyan", "magenta"]
UNIT_MULTIPLIERS = {
    "s": 1, "ms": 1e3, "µs": 1e6, "ns": 1e9, "ps": 1e12,
    "V": 1, "mV": 1e3, "µV": 1e6, "nV": 1e9,
}
NICE_STEPS_TIME = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
NICE_STEPS_FREQ = [0.1, 0.2, 0.5, 1, 2, 3, 5, 10, 20, 25, 50, 100, 200]
PEAK_BOX = dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='gray', alpha=0.85)


def _n_bounds(y_min, y_max, div):
    return (math.ceil(max(-y_min, 0) / div) + 1,
            math.ceil(max(y_max, 0) / div) + 1)


def _build_ticks(div, n_below, n_above):
    return [round((-n_below + i) * div, 10) for i in range(n_below + n_above + 1)]


class CTkWindowWithDnD(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        ctk.CTk.__init__(self, *args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


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

        self._build_selection_screen()
        self._build_tabs()

        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)
        self.bind("<Return>", self._on_enter)

    # ── UI helpers ────────────────────────────────────────────────────────────

    def _tab_header(self, parent, path_attr):
        ctk.CTkLabel(parent, text="Selecciona o arrastra un archivo CSV aquí",
                     font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkButton(parent, text="Buscar CSV", command=self.browse_file).pack(pady=5)
        lbl = ctk.CTkLabel(parent, text="No fue seleccionado ningún archivo",
                           font=("Arial", 10, "italic"), text_color="gray")
        lbl.pack(pady=5)
        setattr(self, path_attr, lbl)

    def _enter_hint(self, parent, text="Presioná Enter para graficar"):
        ctk.CTkLabel(parent, text=text, font=("Arial", 10, "italic"),
                     text_color="gray").pack(side="bottom", pady=8)

    @staticmethod
    def _apply_color(menu, color):
        menu.configure(fg_color=color, button_color=color, button_hover_color=color)

    def _make_color_menu(self, parent, default="blue"):
        menu = ctk.CTkOptionMenu(parent, values=COLORS, width=100)
        menu.configure(command=lambda c, m=menu: self._apply_color(m, c))
        menu.set(default)
        self._apply_color(menu, default)
        return menu

    @staticmethod
    def _try_float(widget, default=None):
        try:
            val = widget.get().strip()
            return float(val) if val else default
        except (ValueError, AttributeError):
            return default

    # ── Screen construction ───────────────────────────────────────────────────

    def _build_selection_screen(self):
        self.selection_frame = ctk.CTkFrame(self)
        self.selection_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.selection_frame, text="¿Qué tipo de análisis desea realizar?",
                     font=("Arial", 18, "bold")).pack(pady=40)
        for label, mode in [("Respuesta en Tiempo", "Tiempo"),
                             ("Respuesta en Frecuencia", "Frecuencia"),
                             ("Figuras de Lissajous", "Lissajous")]:
            ctk.CTkButton(self.selection_frame, text=label, width=200, height=50,
                          command=lambda m=mode: self.select_mode(m)).pack(pady=10)

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tab_time = self.tabview.add("Respuesta en Tiempo")
        self.tab_freq = self.tabview.add("Respuesta en Frecuencia")
        self.tab_lissajous = self.tabview.add("Figuras de Lissajous")
        self._setup_time_ui(self.tab_time)
        self._setup_freq_ui(self.tab_freq)
        self._setup_lissajous_ui(self.tab_lissajous)

    def _setup_time_ui(self, parent):
        self._tab_header(parent, "time_path_label")
        self._enter_hint(parent)

        self.time_scroll_frame = ctk.CTkScrollableFrame(
            parent, width=500, height=180, label_text="Configuración por Señal")
        self.time_scroll_frame.pack(pady=5, padx=10)

        opts = ctk.CTkScrollableFrame(parent, height=105, label_text="Opciones del Gráfico")
        opts.pack(pady=2, padx=10, fill="x")
        opts.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="col")

        tr = ctk.CTkFrame(opts, fg_color="transparent")
        tr.grid(row=0, column=0, columnspan=6, pady=2)
        ctk.CTkLabel(tr, text="Título:").pack(side="left", padx=5)
        self.title_entry = ctk.CTkEntry(tr, width=200, placeholder_text="Nombre del gráfico...")
        self.title_entry.insert(0, "Osciloscopio - Señales")
        self.title_entry.pack(side="left", padx=5)

        self.log_x_var = ctk.BooleanVar(value=False)
        self.log_y_var = ctk.BooleanVar(value=False)
        self.show_peaks_var = ctk.BooleanVar(value=True)
        self.show_cursors_var = ctk.BooleanVar(value=True)
        for col, (text, var) in enumerate([
            ("Eje X Log", self.log_x_var), ("Eje Y Log", self.log_y_var),
            ("Ver Max/Min", self.show_peaks_var), ("Ver Cursores", self.show_cursors_var),
        ]):
            ctk.CTkCheckBox(opts, text=text, variable=var).grid(row=1, column=col, padx=5, pady=4)

        wf = ctk.CTkFrame(opts, fg_color="transparent")
        wf.grid(row=1, column=5, padx=5, pady=4)
        ctk.CTkLabel(wf, text="Grilla:").pack(side="left")
        self.grid_width_entry = ctk.CTkEntry(wf, width=45)
        self.grid_width_entry.insert(0, "0.6")
        self.grid_width_entry.pack(side="left", padx=(2, 5))
        ctk.CTkLabel(wf, text="Señal:").pack(side="left")
        self.time_signal_width_entry = ctk.CTkEntry(wf, width=45)
        self.time_signal_width_entry.insert(0, "1.5")
        self.time_signal_width_entry.pack(side="left", padx=2)

        sf = ctk.CTkFrame(opts, fg_color="transparent")
        sf.grid(row=2, column=0, columnspan=6, pady=4)
        ctk.CTkLabel(sf, text="Eje X:").pack(side="left", padx=2)
        self.unit_x_menu = ctk.CTkOptionMenu(sf, values=["s", "ms", "µs", "ns", "ps"], width=75)
        self.unit_x_menu.set("µs")
        self.unit_x_menu.pack(side="left", padx=2)
        ctk.CTkLabel(sf, text="Div:").pack(side="left", padx=2)
        self.grid_spacing_x_entry = ctk.CTkEntry(sf, width=50)
        self.grid_spacing_x_entry.pack(side="left", padx=2)
        ctk.CTkLabel(sf, text="   Eje Y:").pack(side="left", padx=2)
        self.unit_y_menu = ctk.CTkOptionMenu(sf, values=["V", "mV", "µV"], width=75)
        self.unit_y_menu.set("mV")
        self.unit_y_menu.pack(side="left", padx=2)
        ctk.CTkLabel(sf, text="Div:").pack(side="left", padx=2)
        self.grid_spacing_y_entry = ctk.CTkEntry(sf, width=50)
        self.grid_spacing_y_entry.pack(side="left", padx=2)

    def _setup_freq_ui(self, parent):
        self._tab_header(parent, "freq_path_label")
        self._enter_hint(parent)

        mf = ctk.CTkFrame(parent)
        mf.pack(pady=5, fill="x", padx=10)
        mf.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        ctk.CTkLabel(mf, text="Mapeo de Columnas (Índices desde 0):",
                     font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=6, pady=5)
        for i, (lbl, attr, default) in enumerate([
            ("Freq:", "freq_col_idx", "1"),
            ("Gan:", "gain_col_idx", "3"),
            ("Fase:", "phase_col_idx", "4"),
        ]):
            ctk.CTkLabel(mf, text=lbl).grid(row=1, column=i * 2, padx=2, sticky="e")
            entry = ctk.CTkEntry(mf, width=50)
            entry.insert(0, default)
            entry.grid(row=1, column=i * 2 + 1, padx=2, sticky="w", pady=5)
            setattr(self, attr, entry)

        self.freq_scroll_frame = ctk.CTkScrollableFrame(
            parent, width=500, height=150, label_text="Configuración por Señal")
        self.freq_scroll_frame.pack(pady=5, padx=10)

        opts = ctk.CTkScrollableFrame(parent, height=140, label_text="Opciones de Frecuencia")
        opts.pack(pady=2, padx=10, fill="x")
        opts.grid_columnconfigure((0, 1), weight=1, uniform="col")

        tr = ctk.CTkFrame(opts, fg_color="transparent")
        tr.grid(row=0, column=0, columnspan=2, pady=2)
        ctk.CTkLabel(tr, text="Título:").pack(side="left", padx=5)
        self.freq_title_entry = ctk.CTkEntry(tr, width=200, placeholder_text="Nombre del gráfico...")
        self.freq_title_entry.insert(0, "Respuesta en Frecuencia")
        self.freq_title_entry.pack(side="left", padx=5)

        self.freq_show_peaks_var = ctk.BooleanVar(value=True)
        self.freq_show_cursors_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts, text="Ver Max/Min", variable=self.freq_show_peaks_var).grid(
            row=1, column=0, padx=10, pady=2, sticky="e")
        ctk.CTkCheckBox(opts, text="Ver Cursores", variable=self.freq_show_cursors_var).grid(
            row=1, column=1, padx=10, pady=2, sticky="w")

        wf = ctk.CTkFrame(opts, fg_color="transparent")
        wf.grid(row=2, column=1, padx=10, pady=2, sticky="w")
        ctk.CTkLabel(wf, text="Grilla:").pack(side="left")
        self.freq_grid_width_entry = ctk.CTkEntry(wf, width=45)
        self.freq_grid_width_entry.insert(0, "0.6")
        self.freq_grid_width_entry.pack(side="left", padx=(2, 5))
        ctk.CTkLabel(wf, text="Señal:").pack(side="left")
        self.freq_signal_width_entry = ctk.CTkEntry(wf, width=45)
        self.freq_signal_width_entry.insert(0, "1.5")
        self.freq_signal_width_entry.pack(side="left", padx=2)

    def _setup_lissajous_ui(self, parent):
        self._tab_header(parent, "lissajous_path_label")

        cf = ctk.CTkFrame(parent)
        cf.pack(pady=5, fill="x", padx=10)
        cf.grid_columnconfigure((0, 1, 2, 3), weight=1)
        ctk.CTkLabel(cf, text="Selección de Señales:", font=("Arial", 12, "bold")).grid(
            row=0, column=0, columnspan=4, pady=5)
        for i, (lbl, attr) in enumerate([("Eje X (CH):", "lissajous_x_menu"),
                                          ("Eje Y (CH):", "lissajous_y_menu")]):
            ctk.CTkLabel(cf, text=lbl).grid(row=1, column=i * 2, padx=5, sticky="e")
            menu = ctk.CTkOptionMenu(cf, values=["—"], width=130)
            menu.grid(row=1, column=i * 2 + 1, padx=5, pady=5, sticky="w")
            setattr(self, attr, menu)

        self._enter_hint(parent, "Presioná Enter para generar la figura")

        opts = ctk.CTkScrollableFrame(parent, height=130, label_text="Opciones del Gráfico")
        opts.pack(pady=5, padx=10, fill="x")
        opts.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="col")

        tr = ctk.CTkFrame(opts, fg_color="transparent")
        tr.grid(row=0, column=0, columnspan=4, pady=2)
        ctk.CTkLabel(tr, text="Título:").pack(side="left", padx=5)
        self.lissajous_title_entry = ctk.CTkEntry(tr, width=200, placeholder_text="Nombre del gráfico...")
        self.lissajous_title_entry.insert(0, "Figura de Lissajous")
        self.lissajous_title_entry.pack(side="left", padx=5)

        self.lissajous_show_cursors_var = ctk.BooleanVar(value=True)
        self.lissajous_equal_aspect_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts, text="Ver Cursores", variable=self.lissajous_show_cursors_var).grid(
            row=1, column=1, padx=5, pady=4)
        ctk.CTkCheckBox(opts, text="Aspecto 1:1", variable=self.lissajous_equal_aspect_var).grid(
            row=1, column=2, padx=5, pady=4)

        cf2 = ctk.CTkFrame(opts, fg_color="transparent")
        cf2.grid(row=1, column=3, padx=5, pady=4)
        ctk.CTkLabel(cf2, text="Color:").pack(side="left")
        self.lissajous_color_menu = self._make_color_menu(cf2)
        self.lissajous_color_menu.pack(side="left", padx=5)

        ur = ctk.CTkFrame(opts, fg_color="transparent")
        ur.grid(row=2, column=0, columnspan=4, pady=4)
        for lbl, attr, default in [("Unidad X:", "lissajous_unit_x", "mV"),
                                    ("Unidad Y:", "lissajous_unit_y", "mV")]:
            ctk.CTkLabel(ur, text=lbl).pack(side="left", padx=3)
            menu = ctk.CTkOptionMenu(ur, values=["V", "mV", "µV", "nV"], width=75)
            menu.set(default)
            menu.pack(side="left", padx=3)
            setattr(self, attr, menu)
        ctk.CTkLabel(ur, text="  Grosor señal:").pack(side="left", padx=3)
        self.lissajous_signal_width_entry = ctk.CTkEntry(ur, width=50)
        self.lissajous_signal_width_entry.insert(0, "1.2")
        self.lissajous_signal_width_entry.pack(side="left", padx=3)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_enter(self, event):
        if not self.tabview.winfo_ismapped():
            return
        tab = self.tabview.get()
        if tab == "Respuesta en Tiempo" and self.time_file_path:
            self.plot_data()
        elif tab == "Respuesta en Frecuencia" and self.freq_file_path:
            self.plot_freq_data()
        elif tab == "Figuras de Lissajous" and self.lissajous_file_path:
            self.plot_lissajous()

    def select_mode(self, mode):
        tab_map = {"Tiempo": "Respuesta en Tiempo",
                   "Frecuencia": "Respuesta en Frecuencia",
                   "Lissajous": "Figuras de Lissajous"}
        self.selection_frame.pack_forget()
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabview.set(tab_map[mode])

    def handle_drop(self, event):
        path = event.data.strip('{}')
        if path.lower().endswith('.csv'):
            self.load_csv(path)
        else:
            messagebox.showerror("Error", "El archivo debe ser un .csv")

    def browse_file(self):
        path = filedialog.askopenfilename(title="Seleccionar CSV",
                                          filetypes=[("CSV Files", "*.csv")])
        if path:
            self.load_csv(path)

    def load_csv(self, path):
        tab = self.tabview.get()
        short = os.path.basename(path)
        if tab == "Respuesta en Tiempo":
            self.time_file_path = path
            self.time_path_label.configure(text=f"Cargado: {short}", text_color="black")
            self.setup_dynamic_inputs()
        elif tab == "Figuras de Lissajous":
            self.lissajous_file_path = path
            self.lissajous_path_label.configure(text=f"Cargado: {short}", text_color="black")
            self._populate_lissajous_columns(path)
        else:
            self.freq_file_path = path
            self.freq_path_label.configure(text=f"Cargado: {short}", text_color="black")
            self.setup_dynamic_inputs()

    # ── Signal config panels ──────────────────────────────────────────────────

    def setup_dynamic_inputs(self):
        is_time = self.tabview.get() == "Respuesta en Tiempo"
        scroll_frame = self.time_scroll_frame if is_time else self.freq_scroll_frame
        inputs_list = self.time_signal_inputs if is_time else self.freq_signal_inputs
        inputs_list.clear()

        for w in scroll_frame.winfo_children():
            w.destroy()

        try:
            if is_time:
                cols = pd.read_csv(self.time_file_path, skiprows=[1], nrows=0).columns[1:]
                ctk.CTkLabel(scroll_frame,
                             text="Índices de columna con base 0  (col. 0 = tiempo)",
                             font=("Arial", 10, "italic"), text_color="gray").pack(pady=(4, 0))
            else:
                cols = ["Ganancia", "Fase"]

            for i, col in enumerate(cols):
                frame = ctk.CTkFrame(scroll_frame)
                frame.pack(pady=5, fill="x", padx=5)
                frame.grid_columnconfigure((0, 1), weight=1, uniform="col")

                ctk.CTkLabel(frame, text=f"Señal: {col}" if is_time else col,
                             font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=2)

                enabled_var = ctk.BooleanVar(value=True)
                col_idx_entry = s_entry = d_entry = None
                row = 1

                if is_time:
                    ctk.CTkCheckBox(frame, text="Incluir", variable=enabled_var).grid(
                        row=row, column=0, columnspan=2, pady=2)
                    row += 1

                ctk.CTkLabel(frame, text="Nombre:").grid(row=row, column=0, padx=5, sticky="e")
                n_entry = ctk.CTkEntry(frame, width=120)
                n_entry.insert(0, col)
                n_entry.grid(row=row, column=1, pady=2, sticky="w")
                row += 1

                if is_time:
                    for lbl, default in [("Columna (idx):", str(1 + i)),
                                         ("Escala:", "1"),
                                         ("Despl. (V):", "0")]:
                        ctk.CTkLabel(frame, text=lbl).grid(row=row, column=0, padx=5, sticky="e")
                        e = ctk.CTkEntry(frame, width=80)
                        e.insert(0, default)
                        e.grid(row=row, column=1, pady=2, sticky="w")
                        if col_idx_entry is None:
                            col_idx_entry = e
                        elif s_entry is None:
                            s_entry = e
                        else:
                            d_entry = e
                        row += 1

                ctk.CTkLabel(frame, text="Color:").grid(row=row, column=0, padx=5, sticky="e")
                color_menu = self._make_color_menu(frame, default=COLORS[i % len(COLORS)])
                color_menu.grid(row=row, column=1, pady=2, sticky="w")

                inputs_list.append({
                    "name": col, "alias": n_entry, "scale": s_entry,
                    "disp": d_entry, "color": color_menu, "col_idx": col_idx_entry,
                    "enabled": enabled_var,
                })
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer columnas: {e}")

    # ── Plotting ──────────────────────────────────────────────────────────────

    def plot_data(self):
        try:
            df = pd.read_csv(self.time_file_path, skiprows=[1])
            if df.empty or len(df.columns) < 2:
                messagebox.showerror("Error", "El CSV debe tener al menos 2 columnas y no estar vacío.")
                return

            u_x = self.unit_x_menu.get()
            u_y = self.unit_y_menu.get()
            x_data = df.iloc[:, 0] * UNIT_MULTIPLIERS[u_x]

            base_div = self._try_float(self.grid_spacing_y_entry)
            g_width = self._try_float(self.grid_width_entry, 0.6)
            s_width = self._try_float(self.time_signal_width_entry, 1.5)
            x_spacing = self._try_float(self.grid_spacing_x_entry)

            def resolve_div(scale, y_min, y_max):
                if base_div is not None and scale > 0:
                    return base_div * scale
                y_range = max(y_max - y_min, 1e-9)
                return min(NICE_STEPS_TIME, key=lambda s: abs(s - y_range / 6))

            def parse_sig(sig):
                scale = self._try_float(sig["scale"], 1.0)
                disp = self._try_float(sig["disp"], 0.0)
                col_idx = int(sig["col_idx"].get()) if sig["col_idx"] else None
                y = df.iloc[:, col_idx] if col_idx is not None else df[sig["name"]]
                return scale, (y * UNIT_MULTIPLIERS[u_y] + disp) * scale

            def mark_peaks(ax, y_data, sig, scale):
                color, alias = sig["color"].get(), sig["alias"].get()
                max_idx, min_idx = y_data.idxmax(), y_data.idxmin()
                ax.plot(
                    [x_data[max_idx], x_data[min_idx]],
                    [y_data[max_idx], y_data[min_idx]],
                    'o', markerfacecolor='white', markeredgecolor=color,
                    markeredgewidth=2, markersize=8, zorder=5,
                )
                return (f"{alias} Máx: {y_data[max_idx]/scale:.3g} {u_y}  @  {x_data[max_idx]:.4g} {u_x}\n"
                        f"{alias} Mín:  {y_data[min_idx]/scale:.3g} {u_y}  @  {x_data[min_idx]:.4g} {u_x}")

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
                sig2 = scale2 = y2 = None
                same_scale = True

                if len(pair) == 2:
                    sig2 = pair[1]
                    scale2, y2 = parse_sig(sig2)
                    same_scale = abs(scale1 - scale2) < 1e-9

                if same_scale:
                    all_min = float(y1.min()) if y2 is None else float(min(y1.min(), y2.min()))
                    all_max = float(y1.max()) if y2 is None else float(max(y1.max(), y2.max()))
                    div = resolve_div(scale1, all_min, all_max)
                    nb, na = _n_bounds(all_min, all_max, div)
                    ticks = _build_ticks(div, nb, na)

                    line1, = ax1.plot(x_data, y1, color=sig1["color"].get(),
                                      linewidth=s_width, label=sig1["alias"].get())
                    lines = [line1]
                    if sig2 is not None:
                        line2, = ax1.plot(x_data, y2, color=sig2["color"].get(),
                                          linewidth=s_width, label=sig2["alias"].get())
                        lines.append(line2)

                    ax1.set_ylabel(f'Voltaje ({u_y})')
                    ax1.set_xlabel(f'Tiempo ({u_x})')
                    ax1.set_yticks(ticks)
                    ax1.set_ylim(ticks[0] - div * 0.5, ticks[-1] + div * 0.5)
                    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _, s=scale1: f'{v/s:g}'))
                    ax1.grid(True, linestyle='--', alpha=0.6, linewidth=g_width)

                    if self.show_peaks_var.get():
                        peak_lines = [mark_peaks(ax1, y1, sig1, scale1)]
                        if sig2 is not None:
                            peak_lines.append(mark_peaks(ax1, y2, sig2, scale2))
                        ax1.text(0.02, 0.02, "\n".join(peak_lines), transform=ax1.transAxes,
                                 fontsize=9, verticalalignment='bottom', fontfamily='monospace',
                                 bbox=PEAK_BOX)
                else:
                    comb_min = float(min(y1.min(), y2.min()))
                    comb_max = float(max(y1.max(), y2.max()))
                    div = resolve_div(1, comb_min, comb_max)
                    nb, na = _n_bounds(comb_min, comb_max, div)
                    ticks = _build_ticks(div, nb, na)

                    line1, = ax1.plot(x_data, y1, color=sig1["color"].get(),
                                      linewidth=s_width, label=sig1["alias"].get())
                    ax1.set_ylabel(f'{sig1["alias"].get()} ({u_y})', color=sig1["color"].get())
                    ax1.tick_params(axis='y', labelcolor=sig1["color"].get())
                    ax1.set_xlabel(f'Tiempo ({u_x})')
                    ax1.set_yticks(ticks)
                    ax1.set_ylim(ticks[0] - div * 0.5, ticks[-1] + div * 0.5)
                    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _, s=scale1: f'{v/s:g}'))
                    ax1.grid(True, linestyle='--', alpha=0.6, linewidth=g_width)
                    lines = [line1]

                    ax2 = ax1.twinx()
                    line2, = ax2.plot(x_data, y2, color=sig2["color"].get(),
                                      linewidth=s_width, label=sig2["alias"].get())
                    ax2.set_ylabel(f'{sig2["alias"].get()} ({u_y})', color=sig2["color"].get())
                    ax2.tick_params(axis='y', labelcolor=sig2["color"].get())
                    ax2.set_yticks(ticks)
                    ax2.set_ylim(ticks[0] - div * 0.5, ticks[-1] + div * 0.5)
                    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _, s=scale2: f'{v/s:g}'))
                    lines.append(line2)

                    if self.show_peaks_var.get():
                        peak_lines = [mark_peaks(ax1, y1, sig1, scale1), mark_peaks(ax2, y2, sig2, scale2)]
                        ax1.text(0.02, 0.02, "\n".join(peak_lines), transform=ax1.transAxes,
                                 fontsize=9, verticalalignment='bottom', fontfamily='monospace',
                                 bbox=PEAK_BOX)

                if x_spacing:
                    ax1.xaxis.set_major_locator(ticker.MultipleLocator(x_spacing))
                if self.log_x_var.get():
                    ax1.set_xscale('symlog')
                if self.log_y_var.get():
                    ax1.set_yscale('symlog')
                    if ax2:
                        ax2.set_yscale('symlog')
                if self.show_cursors_var.get():
                    mplcursors.cursor(lines, hover=mplcursors.HoverMode.Transient)

                ax1.legend(lines, [l.get_label() for l in lines], loc='best')
                plt.tight_layout()

            plt.show()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo graficar.\nDetalle: {e}")

    def plot_freq_data(self):
        try:
            f_idx = int(self.freq_col_idx.get())
            g_idx = int(self.gain_col_idx.get())
            p_idx = int(self.phase_col_idx.get())

            col_names = pd.read_csv(self.freq_file_path, skiprows=[1], nrows=0,
                                    encoding='latin1').columns
            df = pd.read_csv(self.freq_file_path, skiprows=[1], encoding='latin1',
                             usecols=[f_idx, g_idx, p_idx])
            if df.empty:
                return

            f_data = df[col_names[f_idx]]
            g_data = df[col_names[g_idx]]
            p_data = df[col_names[p_idx]]

            g_config = self.freq_signal_inputs[0]
            p_config = self.freq_signal_inputs[1]
            g_color = g_config["color"].get()
            p_color = p_config["color"].get()

            fg_width = self._try_float(self.freq_grid_width_entry, 0.6)
            fs_width = self._try_float(self.freq_signal_width_entry, 1.5)

            fig, ax1 = plt.subplots(figsize=(10, 6))
            ax2 = ax1.twinx()

            line_g, = ax1.semilogx(f_data, g_data, color=g_color, linewidth=fs_width,
                                    label=g_config["alias"].get())
            ax1.set_ylabel(f'{g_config["alias"].get()} (dB)', color=g_color)
            ax1.tick_params(axis='y', labelcolor=g_color)
            ax1.grid(True, which='both', linestyle='--', alpha=0.6, linewidth=fg_width)

            line_p, = ax2.semilogx(f_data, p_data, color=p_color, linewidth=fs_width,
                                    label=p_config["alias"].get())
            ax2.set_ylabel(f'{p_config["alias"].get()} (grados)', color=p_color)
            ax2.tick_params(axis='y', labelcolor=p_color)
            ax1.set_xlabel('Frecuencia (Hz)')

            step_p = 15
            p_min, p_max = float(p_data.min()), float(p_data.max())
            p_range = max(p_max - p_min, 1.0)
            p_lo, p_hi = p_min - p_range * 0.05, p_max + p_range * 0.05

            phase_ticks = []
            t = math.floor(p_lo / step_p) * step_p
            while t <= p_hi + 1e-9:
                phase_ticks.append(round(t, 6))
                t += step_p
            n = len(phase_ticks)

            g_min, g_max = float(g_data.min()), float(g_data.max())
            g_range = max(g_max - g_min, 1.0)
            g_lo, g_hi = g_min - g_range * 0.05, g_max + g_range * 0.05
            gain_step = min(NICE_STEPS_FREQ, key=lambda s: abs(s - (g_hi - g_lo) / max(n - 1, 1)))
            first_g = math.floor(g_lo / gain_step) * gain_step
            gain_ticks = [first_g + i * gain_step for i in range(n)]

            while gain_ticks[-1] < g_hi - 1e-9:
                gain_ticks.append(round(gain_ticks[-1] + gain_step, 10))
                phase_ticks.append(round(phase_ticks[-1] + step_p, 6))

            ax1.set_ylim(gain_ticks[0] - gain_step * 0.5, gain_ticks[-1] + gain_step * 0.5)
            ax1.set_yticks(gain_ticks)
            ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g'))
            ax2.set_ylim(phase_ticks[0] - step_p * 0.5, phase_ticks[-1] + step_p * 0.5)
            ax2.set_yticks(phase_ticks)
            ax2.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g'))

            if self.freq_show_peaks_var.get():
                idx_max_g, idx_min_g = g_data.idxmax(), g_data.idxmin()
                idx_max_p, idx_min_p = p_data.idxmax(), p_data.idxmin()

                for ax, idxs, ys, color in [
                    (ax1, [idx_max_g, idx_min_g], g_data, g_color),
                    (ax2, [idx_max_p, idx_min_p], p_data, p_color),
                ]:
                    ax.plot(f_data[idxs], ys[idxs], 'o', markerfacecolor='white',
                            markeredgecolor=color, markeredgewidth=2, markersize=8, zorder=5)

                info = (
                    f"Gan Máx: {g_data[idx_max_g]:.2g} dB  @  {f_data[idx_max_g]:.4g} Hz\n"
                    f"Gan Mín:  {g_data[idx_min_g]:.2g} dB  @  {f_data[idx_min_g]:.4g} Hz\n"
                    f"Fase Máx: {p_data[idx_max_p]:.1f}°  @  {f_data[idx_max_p]:.4g} Hz\n"
                    f"Fase Mín:  {p_data[idx_min_p]:.1f}°  @  {f_data[idx_min_p]:.4g} Hz"
                )
                ax1.text(0.02, 0.02, info, transform=ax1.transAxes,
                         fontsize=9, verticalalignment='bottom', fontfamily='monospace',
                         bbox=PEAK_BOX)

            if self.freq_show_cursors_var.get():
                mplcursors.cursor([line_g, line_p], hover=mplcursors.HoverMode.Transient)

            lines = [line_g, line_p]
            ax1.legend(lines, [l.get_label() for l in lines], loc='best')
            fig.suptitle(self.freq_title_entry.get() or "Respuesta en Frecuencia")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Error", f"Error al graficar respuesta en frecuencia: {e}")

    def plot_lissajous(self):
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

            u_x = self.lissajous_unit_x.get()
            u_y = self.lissajous_unit_y.get()
            x_data = df[x_col] * UNIT_MULTIPLIERS[u_x]
            y_data = df[y_col] * UNIT_MULTIPLIERS[u_y]
            ls_width = self._try_float(self.lissajous_signal_width_entry, 1.2)

            fig, ax = plt.subplots(figsize=(7, 7))
            line, = ax.plot(x_data, y_data, color=self.lissajous_color_menu.get(), linewidth=ls_width)
            ax.set_xlabel(f"{x_col} ({u_x})")
            ax.set_ylabel(f"{y_col} ({u_y})")
            ax.set_title(self.lissajous_title_entry.get() or "Figura de Lissajous")
            ax.grid(True, linestyle='--', alpha=0.6)
            if self.lissajous_equal_aspect_var.get():
                ax.set_aspect('equal', adjustable='box')
            if self.lissajous_show_cursors_var.get():
                mplcursors.cursor(line, hover=mplcursors.HoverMode.Transient)

            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar figura de Lissajous:\n{e}")

    def _populate_lissajous_columns(self, path):
        cols = None
        for kwargs in [{"skiprows": [1]}, {}]:
            try:
                cols = list(pd.read_csv(path, nrows=0, encoding='latin1', **kwargs).columns)
                break
            except Exception:
                pass
        if not cols:
            messagebox.showerror("Error", "No se pudieron leer columnas del archivo.")
            return

        self.lissajous_x_menu.configure(values=cols)
        self.lissajous_y_menu.configure(values=cols)
        self.lissajous_x_menu.set(cols[1] if len(cols) > 1 else cols[0])
        self.lissajous_y_menu.set(cols[2] if len(cols) > 2 else cols[-1])


if __name__ == "__main__":
    app = CSVPlotterApp()
    app.mainloop()
