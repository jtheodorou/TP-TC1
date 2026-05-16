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
        self.geometry("450x200")
        
        self.file_path = ""
        
        # --- UI Elements ---
        self.label = ctk.CTkLabel(self, text="Selecciona un archivo CSV", font=("Arial", 16, "bold"))
        self.label.pack(pady=20)
        
        # Button to browse for file
        self.browse_btn = ctk.CTkButton(self, text="Buscar CSV", command=self.browse_file)
        self.browse_btn.pack(pady=10)
        
        # Label to show selected file path
        self.path_label = ctk.CTkLabel(self, text="No fue seleccionado ningún archivo", font=("Arial", 10, "italic"), text_color="gray")
        self.path_label.pack(pady=5)
        
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
            
            y_displacement = 0
            y_scale = 1

            df.iloc[:, 1:] = df.iloc[:, 1:]*y_scale + y_displacement

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