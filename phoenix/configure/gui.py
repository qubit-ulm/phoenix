"""Tk-based GUI frontends for Phoenix configuration."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .service import ConfigurationService, parse_value


def _create_scrollable_table(root: tk.Tk | tk.Toplevel):
    frame = ttk.Frame(root, padding=12)
    frame.grid(row=0, column=0, sticky="nsew")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    canvas = tk.Canvas(frame, highlightthickness=0)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    table = ttk.Frame(canvas)

    table.bind(
        "<Configure>",
        lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.create_window((0, 0), window=table, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    return frame, table


def launch_settings_gui(
    service: ConfigurationService | None = None,
    *,
    scope: str | None = None,
) -> None:
    """Open the flattened settings editor GUI."""
    service = ConfigurationService() if service is None else service
    root = tk.Tk()
    root.title("Phoenix Configuration")
    root.geometry("1100x720")
    _, table = _create_scrollable_table(root)

    rows = service.flattened_rows(scope=scope)
    vars_by_path: dict[str, tk.StringVar] = {}

    ttk.Label(table, text="Parameter").grid(row=0, column=0, sticky="w", padx=4, pady=4)
    ttk.Label(table, text="Value").grid(row=0, column=1, sticky="w", padx=4, pady=4)
    ttk.Label(table, text="Default").grid(row=0, column=2, sticky="w", padx=4, pady=4)

    for row_num, row in enumerate(rows, start=1):
        variable = tk.StringVar(value=row["value"])
        vars_by_path[row["path"]] = variable
        ttk.Label(table, text=row["path"]).grid(
            row=row_num,
            column=0,
            sticky="w",
            padx=4,
            pady=2,
        )
        ttk.Entry(table, textvariable=variable, width=60).grid(
            row=row_num,
            column=1,
            sticky="ew",
            padx=4,
            pady=2,
        )
        ttk.Label(table, text=row["default"]).grid(
            row=row_num,
            column=2,
            sticky="w",
            padx=4,
            pady=2,
        )

    button_row = len(rows) + 1

    def save():
        try:
            for path, variable in vars_by_path.items():
                service.set_value(path, parse_value(variable.get()))
        except Exception as exc:
            messagebox.showerror("Phoenix Configuration", str(exc))
            return
        messagebox.showinfo("Phoenix Configuration", "Configuration saved.")
        root.destroy()

    ttk.Button(table, text="Save", command=save).grid(
        row=button_row,
        column=1,
        sticky="e",
        padx=4,
        pady=12,
    )
    ttk.Button(table, text="Abort", command=root.destroy).grid(
        row=button_row,
        column=2,
        sticky="w",
        padx=4,
        pady=12,
    )

    root.mainloop()


def launch_initialization_gui(service: ConfigurationService | None = None) -> None:
    """Open the backend-initialization GUI."""
    service = ConfigurationService() if service is None else service
    root = tk.Tk()
    root.title("Phoenix Backend Initialization")
    root.geometry("720x420")

    frame = ttk.Frame(root, padding=12)
    frame.grid(row=0, column=0, sticky="nsew")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    ttk.Label(frame, text="Enable backends").grid(row=0, column=0, sticky="w", padx=4, pady=4)
    ttk.Label(frame, text="Detected").grid(row=0, column=1, sticky="w", padx=4, pady=4)
    ttk.Label(frame, text="Current state").grid(row=0, column=2, sticky="w", padx=4, pady=4)

    recommended = service.recommended_backend_selection()
    status_rows = {row["backend"]: row for row in service.backend_status_rows()}
    variables: dict[str, tk.BooleanVar] = {}

    for row_num, backend in enumerate(service.backend_names, start=1):
        variables[backend] = tk.BooleanVar(value=recommended[backend])
        ttk.Checkbutton(frame, text=backend, variable=variables[backend]).grid(
            row=row_num,
            column=0,
            sticky="w",
            padx=4,
            pady=3,
        )
        ttk.Label(frame, text=status_rows[backend]["detected"]).grid(
            row=row_num,
            column=1,
            sticky="w",
            padx=4,
            pady=3,
        )
        ttk.Label(frame, text=status_rows[backend]["state"]).grid(
            row=row_num,
            column=2,
            sticky="w",
            padx=4,
            pady=3,
        )

    def save():
        try:
            selection = {
                backend: variable.get()
                for backend, variable in variables.items()
            }
            service.initialize_backends(selection)
        except Exception as exc:
            messagebox.showerror("Phoenix Backend Initialization", str(exc))
            return
        messagebox.showinfo("Phoenix Backend Initialization", "Backend configuration written.")
        root.destroy()

    ttk.Button(frame, text="Save", command=save).grid(
        row=len(service.backend_names) + 1,
        column=1,
        sticky="e",
        padx=4,
        pady=12,
    )
    ttk.Button(frame, text="Abort", command=root.destroy).grid(
        row=len(service.backend_names) + 1,
        column=2,
        sticky="w",
        padx=4,
        pady=12,
    )

    root.mainloop()


__all__ = ["launch_settings_gui", "launch_initialization_gui"]
