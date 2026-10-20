#!/usr/bin/env python3
"""
Fanuc 0M PMC Ladder Tool — GUI
Dark / phosphor styling, status log.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from pathlib import Path
import fanuc_pmc_tool as core

class FanucPmcApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fanuc 0M PMC Ladder Tool")
        self.geometry("720x520")
        self.configure(bg="#0d0d0d")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#0d0d0d", foreground="#33ff33", font=("Consolas", 10))
        style.configure("TButton", font=("Consolas", 10))
        style.configure("TEntry", fieldbackground="#1a1a1a", foreground="#33ff33")
        style.configure("TFrame", background="#0d0d0d")
        style.configure("TNotebook", background="#0d0d0d")
        style.configure("TNotebook.Tab", background="#1a1a1a", foreground="#33ff33")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        combine = ttk.Frame(notebook)
        split = ttk.Frame(notebook)
        notebook.add(combine, text=" Combine ROMs → #EX ")
        notebook.add(split, text=" Split #EX → ROMs ")

        self._build_combine(combine)
        self._build_split(split)

        self.log = scrolledtext.ScrolledText(self, height=8, bg="#0a0a0a", fg="#33ff33",
                                              font=("Consolas", 9), insertbackground="#33ff33")
        self.log.pack(fill="x", padx=8, pady=4)
        self.log.insert("end", "Ready.\n")
        self.log.configure(state="disabled")

    def log_msg(self, msg: str):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _build_combine(self, parent):
        ttk.Label(parent, text="ROM1 (OE1, 32 KB)").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.rom1_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.rom1_var, width=52).grid(row=0, column=1, padx=4)
        ttk.Button(parent, text="Browse", command=lambda: self._browse(self.rom1_var)).grid(row=0, column=2)

        ttk.Label(parent, text="ROM2 (OE2, 32 KB)").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.rom2_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.rom2_var, width=52).grid(row=1, column=1, padx=4)
        ttk.Button(parent, text="Browse", command=lambda: self._browse(self.rom2_var)).grid(row=1, column=2)

        ttk.Label(parent, text="Output #EX").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.ex_out_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.ex_out_var, width=52).grid(row=2, column=1, padx=4)
        ttk.Button(parent, text="Save as", command=lambda: self._saveas(self.ex_out_var, ".#EX")).grid(row=2, column=2)

        ttk.Button(parent, text="Combine", command=self.do_combine).grid(row=3, column=1, pady=12)

    def _build_split(self, parent):
        ttk.Label(parent, text="Input #EX").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.ex_in_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.ex_in_var, width=52).grid(row=0, column=1, padx=4)
        ttk.Button(parent, text="Browse", command=lambda: self._browse(self.ex_in_var)).grid(row=0, column=2)

        ttk.Label(parent, text="Output ROM1").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.out1_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.out1_var, width=52).grid(row=1, column=1, padx=4)
        ttk.Button(parent, text="Save as", command=lambda: self._saveas(self.out1_var, ".BIN")).grid(row=1, column=2)

        ttk.Label(parent, text="Output ROM2").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.out2_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.out2_var, width=52).grid(row=2, column=1, padx=4)
        ttk.Button(parent, text="Save as", command=lambda: self._saveas(self.out2_var, ".BIN")).grid(row=2, column=2)

        ttk.Button(parent, text="Split", command=self.do_split).grid(row=3, column=1, pady=12)

    def _browse(self, var):
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    def _saveas(self, var, ext):
        path = filedialog.asksaveasfilename(defaultextension=ext)
        if path:
            var.set(path)

    def do_combine(self):
        try:
            rom1 = Path(self.rom1_var.get()).read_bytes()
            rom2 = Path(self.rom2_var.get()).read_bytes()
            templates = core.load_templates()
            ex = core.combine_roms(rom1, rom2, templates)
            Path(self.ex_out_var.get()).write_bytes(ex)
            self.log_msg(f"Combine OK — wrote {len(ex)} bytes to {self.ex_out_var.get()}")
        except Exception as e:
            self.log_msg(f"ERROR: {e}")
            messagebox.showerror("Error", str(e))

    def do_split(self):
        try:
            ex = Path(self.ex_in_var.get()).read_bytes()
            rom1, rom2 = core.split_ex(ex)
            Path(self.out1_var.get()).write_bytes(rom1)
            Path(self.out2_var.get()).write_bytes(rom2)
            self.log_msg(f"Split OK — extracted ROM1 ({len(rom1)}) and ROM2 ({len(rom2)})")
        except Exception as e:
            self.log_msg(f"ERROR: {e}")
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = FanucPmcApp()
    app.mainloop()
