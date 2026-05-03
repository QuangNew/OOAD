from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ScrollableDialogLayout:
    def __init__(
        self,
        parent: tk.Misc,
        top: tk.Toplevel,
        *,
        width: int,
        height: int,
        min_width: int,
        min_height: int,
        bg: str,
    ) -> None:
        self.top = top
        self._body_bg = bg

        screen_width = top.winfo_screenwidth()
        screen_height = top.winfo_screenheight()
        width = min(width, max(min_width, screen_width - 80))
        height = min(height, max(min_height, screen_height - 120))

        self.top.configure(bg=bg)
        self.top.resizable(True, True)
        self.top.minsize(min_width, min_height)
        self._center_over_parent(parent, width, height)

        shell = tk.Frame(top, bg=bg)
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(2, weight=1)

        self.header = tk.Frame(shell, bg=bg)
        self.header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 4))

        self.header_separator = ttk.Separator(shell, orient="horizontal")
        self.header_separator.grid(row=1, column=0, sticky="ew", padx=24, pady=(4, 16))

        body_host = tk.Frame(shell, bg=bg)
        body_host.grid(row=2, column=0, sticky="nsew", padx=24)
        body_host.grid_rowconfigure(0, weight=1)
        body_host.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            body_host,
            bg=bg,
            bd=0,
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(body_host, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self._scrollbar_visible = True

        self.body = tk.Frame(self.canvas, bg=bg)
        self._body_window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")

        self.body.bind("<Configure>", self._sync_scrollregion)
        self.canvas.bind("<Configure>", self._sync_body_width)
        self.body.bind("<Enter>", self._bind_mousewheel)
        self.body.bind("<Leave>", self._unbind_mousewheel)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self.top.bind("<Destroy>", self._handle_destroy, add="+")

        self.footer_separator = ttk.Separator(shell, orient="horizontal")
        self.footer_separator.grid(row=3, column=0, sticky="ew", padx=24, pady=(12, 0))

        self.footer = tk.Frame(shell, bg=bg)
        self.footer.grid(row=4, column=0, sticky="ew", padx=24, pady=(12, 20))

    def _center_over_parent(self, parent: tk.Misc, width: int, height: int) -> None:
        parent.update_idletasks()
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()

        x = px + (pw - width) // 2
        y = py + (ph - height) // 2
        x = max(20, min(x, screen_width - width - 20))
        y = max(20, min(y, screen_height - height - 60))
        self.top.geometry(f"{width}x{height}+{x}+{y}")

    def _sync_scrollregion(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.top.after_idle(self._update_scrollbar_visibility)

    def _sync_body_width(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self._body_window, width=event.width)
        self.top.after_idle(self._update_scrollbar_visibility)

    def _bind_mousewheel(self, _event: tk.Event) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event: tk.Event | None = None) -> None:
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _handle_destroy(self, event: tk.Event) -> None:
        if event.widget is self.top:
            self._unbind_mousewheel()

    def _on_mousewheel(self, event: tk.Event) -> None:
        if getattr(event, "num", None) == 4:
            self.canvas.yview_scroll(-1, "units")
            return
        if getattr(event, "num", None) == 5:
            self.canvas.yview_scroll(1, "units")
            return

        delta = getattr(event, "delta", 0)
        if delta:
            self.canvas.yview_scroll(-int(delta / 120), "units")

    def _update_scrollbar_visibility(self) -> None:
        bbox = self.canvas.bbox("all")
        if bbox is None:
            return

        needs_scrollbar = (bbox[3] - bbox[1]) > self.canvas.winfo_height() + 1
        if needs_scrollbar and not self._scrollbar_visible:
            self.scrollbar.grid()
            self._scrollbar_visible = True
            return

        if not needs_scrollbar and self._scrollbar_visible:
            self.scrollbar.grid_remove()
            self._scrollbar_visible = False