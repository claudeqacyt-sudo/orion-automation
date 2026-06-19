#!/usr/bin/env python
"""
run_regression.py
Abre una ventana de dialogo para configurar y ejecutar la regresion de Orion.
Uso: python run_regression.py
"""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox


def crear_dialogo():
    """Muestra el dialogo de configuracion. Retorna dict con valores o None si se cancela."""

    resultado = {}

    root = tk.Tk()
    root.title("Orion Automation — Regresion")
    root.resizable(False, False)

    # Centrar en pantalla
    root.update_idletasks()
    w, h = 440, 400
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)

    row = 0

    # ── Servidor ──────────────────────────────────────────────
    ttk.Label(frame, text="Servidor", font=("", 10, "bold")).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(0, 6)
    )
    row += 1

    ttk.Label(frame, text="URL base *").grid(row=row, column=0, sticky="w", pady=3, padx=(0, 10))
    url_var = tk.StringVar()
    url_entry = ttk.Entry(frame, textvariable=url_var, width=36)
    url_entry.grid(row=row, column=1, sticky="ew", pady=3)
    row += 1

    ttk.Label(frame, text="URL Frameworks").grid(row=row, column=0, sticky="w", pady=3, padx=(0, 10))
    fw_var = tk.StringVar()
    ttk.Entry(frame, textvariable=fw_var, width=36).grid(row=row, column=1, sticky="ew", pady=3)
    row += 1
    ttk.Label(frame, text="Dejar vacío para usar automático (:444)", foreground="gray", font=("", 8)).grid(
        row=row, column=1, sticky="w"
    )
    row += 1

    # ── Admin ─────────────────────────────────────────────────
    ttk.Separator(frame, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=10
    )
    row += 1
    ttk.Label(frame, text="Credenciales Admin", font=("", 10, "bold")).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(0, 6)
    )
    row += 1

    ttk.Label(frame, text="Usuario").grid(row=row, column=0, sticky="w", pady=3, padx=(0, 10))
    admin_user_var = tk.StringVar(value="cyt")
    ttk.Entry(frame, textvariable=admin_user_var, width=36).grid(row=row, column=1, sticky="ew", pady=3)
    row += 1

    ttk.Label(frame, text="Password").grid(row=row, column=0, sticky="w", pady=3, padx=(0, 10))
    admin_pass_var = tk.StringVar(value="Feab4650")
    ttk.Entry(frame, textvariable=admin_pass_var, show="*", width=36).grid(row=row, column=1, sticky="ew", pady=3)
    row += 1

    # ── Agente ────────────────────────────────────────────────
    ttk.Separator(frame, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=10
    )
    row += 1
    ttk.Label(frame, text="Credenciales Agente", font=("", 10, "bold")).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(0, 6)
    )
    row += 1

    ttk.Label(frame, text="Usuario").grid(row=row, column=0, sticky="w", pady=3, padx=(0, 10))
    agent_user_var = tk.StringVar(value="1001")
    ttk.Entry(frame, textvariable=agent_user_var, width=36).grid(row=row, column=1, sticky="ew", pady=3)
    row += 1

    ttk.Label(frame, text="Password").grid(row=row, column=0, sticky="w", pady=3, padx=(0, 10))
    agent_pass_var = tk.StringVar(value="1001")
    ttk.Entry(frame, textvariable=agent_pass_var, show="*", width=36).grid(row=row, column=1, sticky="ew", pady=3)
    row += 1

    # ── Botones ───────────────────────────────────────────────
    ttk.Separator(frame, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=10
    )
    row += 1

    btn_frame = ttk.Frame(frame)
    btn_frame.grid(row=row, column=0, columnspan=2)

    def ejecutar():
        url = url_var.get().strip()
        if not url:
            messagebox.showerror("Campo requerido", "La URL base es obligatoria.")
            url_entry.focus()
            return
        resultado["url"]        = url
        resultado["fw_url"]     = fw_var.get().strip()
        resultado["admin_user"] = admin_user_var.get().strip() or "cyt"
        resultado["admin_pass"] = admin_pass_var.get().strip() or "Feab4650"
        resultado["agent_user"] = agent_user_var.get().strip() or "1001"
        resultado["agent_pass"] = agent_pass_var.get().strip() or "1001"
        root.destroy()

    def cancelar():
        root.destroy()

    ttk.Button(btn_frame, text="Ejecutar", command=ejecutar, width=16).pack(side="left", padx=8)
    ttk.Button(btn_frame, text="Cancelar", command=cancelar, width=16).pack(side="left", padx=8)

    url_entry.focus()
    root.bind("<Return>", lambda e: ejecutar())
    root.bind("<Escape>", lambda e: cancelar())
    root.protocol("WM_DELETE_WINDOW", cancelar)

    root.mainloop()

    return resultado if resultado else None


def main():
    datos = crear_dialogo()

    if not datos:
        print("Regresion cancelada.")
        sys.exit(0)

    print(f"\nEjecutando en  : {datos['url']}")
    if datos["fw_url"]:
        print(f"Frameworks en  : {datos['fw_url']}")
    print(f"Admin          : {datos['admin_user']}")
    print(f"Agente         : {datos['agent_user']}\n")

    env = os.environ.copy()
    env["ORION_BASE_URL"]    = datos["url"]
    env["ADMIN_USERNAME"]    = datos["admin_user"]
    env["ADMIN_PASSWORD"]    = datos["admin_pass"]
    env["AGENT_USERNAME"]    = datos["agent_user"]
    env["AGENT_PASSWORD"]    = datos["agent_pass"]
    if datos["fw_url"]:
        env["FW_BASE_URL"] = datos["fw_url"]
    else:
        env.pop("FW_BASE_URL", None)

    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/regression/", "-m", "regression", "-v"],
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    sys.exit(resultado.returncode)


if __name__ == "__main__":
    main()
