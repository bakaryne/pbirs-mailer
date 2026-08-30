"""Local Tkinter configuration interface for PBIRS Mailer."""

from __future__ import annotations

import argparse
import copy
import subprocess
import sys
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from . import __version__
from .config import ConfigurationError
from .config_editor import (
    load_config_document,
    save_config_document,
    split_recipients,
    validate_config_document,
)


class ConfiguratorError(ValueError):
    """Raised when a form value cannot be converted to JSON configuration."""


class SubscriptionDialog(tk.Toplevel):
    """Modal editor for one subscription."""

    def __init__(
        self,
        parent: tk.Misc,
        subscription: dict[str, Any] | None = None,
        on_save: Callable[[dict[str, Any]], bool] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(
            "Ajouter une souscription PBIRS Mailer"
            if subscription is None
            else "Modifier une souscription PBIRS Mailer"
        )
        self.geometry("760x650")
        self.minsize(680, 590)
        self.transient(parent)
        self.result: dict[str, Any] | None = None
        self.on_save = on_save
        source = subscription or {}
        page = source.get("page") if isinstance(source.get("page"), dict) else {}

        self.enabled = tk.BooleanVar(value=bool(source.get("enabled", True)))
        self.name = tk.StringVar(value=str(source.get("name", "")))
        self.url = tk.StringVar(value=str(source.get("url", "")))
        self.internal_name = tk.StringVar(value=str(page.get("internal_name") or ""))
        self.display_name = tk.StringVar(value=str(page.get("display_name") or ""))
        self.subject = tk.StringVar(value=str(source.get("subject", "")))
        self.filename = tk.StringVar(value=str(source.get("filename", "")))

        body = ttk.Frame(self, padding=18)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        row = 0
        ttk.Checkbutton(body, text="Souscription activée", variable=self.enabled).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        row += 1
        row = self._entry(body, row, "Nom *", self.name)
        row = self._entry(body, row, "URL du rapport *", self.url)
        row = self._entry(body, row, "Identifiant interne de page", self.internal_name)
        row = self._entry(body, row, "Libellé visible de page", self.display_name)
        row = self._entry(body, row, "Objet de l’email *", self.subject)
        row = self._entry(body, row, "Nom du fichier PNG *", self.filename)

        ttk.Label(body, text="Destinataires").grid(
            row=row, column=0, sticky="nw", padx=(0, 14), pady=7
        )
        self.recipients = tk.Text(body, height=7, wrap="word")
        self.recipients.grid(row=row, column=1, sticky="nsew", pady=7)
        existing_recipients = source.get("recipients", [])
        if isinstance(existing_recipients, list):
            self.recipients.insert("1.0", "\n".join(str(item) for item in existing_recipients))
        body.rowconfigure(row, weight=1)

        ttk.Label(
            body,
            text=(
                "Saisissez une adresse par ligne, ou séparez-les par une virgule. "
                "Les champs marqués * sont obligatoires."
            ),
            foreground="#555555",
        ).grid(row=row + 1, column=1, sticky="w", pady=(0, 12))

        buttons = ttk.Frame(body)
        buttons.grid(row=row + 2, column=0, columnspan=2, sticky="e")
        ttk.Button(buttons, text="Annuler", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(
            buttons,
            text="Enregistrer la souscription",
            command=self._accept,
        ).pack(side="right")

        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.update_idletasks()
        self.lift()
        self.grab_set()
        self.focus_force()
        self.name.focus_set()

    @staticmethod
    def _entry(
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
    ) -> int:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 14), pady=7)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=7)
        return row + 1

    def _accept(self) -> None:
        recipients = split_recipients(self.recipients.get("1.0", "end"))
        required = {
            "Nom": self.name.get(),
            "URL du rapport": self.url.get(),
            "Objet de l’email": self.subject.get(),
            "Nom du fichier PNG": self.filename.get(),
        }
        missing = [label for label, value in required.items() if not value.strip()]
        if missing:
            messagebox.showerror(
                "Souscription incomplète",
                f"Champ obligatoire : {missing[0]}",
                parent=self,
            )
            return
        if not recipients:
            messagebox.showerror(
                "Souscription incomplète",
                "Ajoutez au moins un destinataire.",
                parent=self,
            )
            return

        result = {
            "name": self.name.get().strip(),
            "enabled": self.enabled.get(),
            "url": self.url.get().strip(),
            "page": {
                "internal_name": self.internal_name.get().strip() or None,
                "display_name": self.display_name.get().strip() or None,
            },
            "recipients": recipients,
            "subject": self.subject.get().strip(),
            "filename": self.filename.get().strip(),
        }
        if self.on_save is not None and not self.on_save(result):
            return
        self.result = result
        self.destroy()


class ConfiguratorApp:
    """Tkinter application that edits one existing V1 configuration."""

    def __init__(self, root: tk.Tk, config_path: Path) -> None:
        self.root = root
        self.config_path = config_path.resolve()
        self.document = load_config_document(self.config_path)
        self.subscriptions = copy.deepcopy(self.document.get("subscriptions", []))
        self.entries: dict[str, tk.StringVar] = {}
        self.booleans: dict[str, tk.BooleanVar] = {}
        self.subscription_buttons: list[ttk.Button] = []
        self.running = False
        self.dirty = False
        self._tracking_changes = False

        self.root.title(f"PBIRS Mailer Configurator {__version__}")
        self.root.geometry("1040x720")
        self.root.minsize(900, 620)
        self._configure_style()
        self._build_ui()
        self._load_form_values()
        self._refresh_subscriptions()
        self._attach_change_tracking()
        self._tracking_changes = True
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", foreground="#53657d")

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="PBIRS Mailer Configurator", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text=f"Fichier actif : {self.config_path}",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 14))

        notebook = ttk.Notebook(outer)
        notebook.pack(fill="both", expand=True)
        self._build_general_tab(notebook)
        self._build_smtp_tab(notebook)
        self._build_subscriptions_tab(notebook)

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(14, 0))
        self.status = tk.StringVar(value="Configuration chargée.")
        ttk.Label(footer, textvariable=self.status).pack(side="left", fill="x", expand=True)

        self.capture_button = ttk.Button(
            footer,
            text="Capturer sans envoyer",
            command=lambda: self._run_command("--no-send"),
        )
        self.capture_button.pack(side="right", padx=(8, 0))
        self.validate_button = ttk.Button(
            footer,
            text="Vérifier la configuration",
            command=self._validate,
        )
        self.validate_button.pack(side="right", padx=(8, 0))
        self.save_button = ttk.Button(
            footer,
            text="Enregistrer",
            command=self._save,
        )
        self.save_button.pack(side="right")

    def _build_general_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=18)
        notebook.add(tab, text="Navigateur et dossiers")
        tab.columnconfigure(1, weight=1)
        tab.columnconfigure(3, weight=1)

        ttk.Label(tab, text="Microsoft Edge", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
        )
        row = 1
        self._add_entry(tab, row, 0, "Canal", "browser.channel")
        self._add_entry(tab, row, 2, "Largeur", "browser.viewport_width")
        row += 1
        self._add_entry(tab, row, 0, "Hauteur", "browser.viewport_height")
        self._add_check(tab, row, 2, "Mode silencieux", "browser.headless")
        row += 1
        self._add_entry(tab, row, 0, "Timeout page (s)", "browser.page_timeout_seconds")
        self._add_entry(tab, row, 2, "Timeout frame (s)", "browser.frame_timeout_seconds")
        row += 1
        self._add_entry(tab, row, 0, "Timeout rendu (s)", "browser.render_timeout_seconds")
        self._add_entry(tab, row, 2, "Calme réseau (s)", "browser.render_quiet_seconds")
        row += 1
        self._add_entry(tab, row, 0, "Stabilité visuelle (s)", "browser.render_stable_seconds")

        ttk.Label(
            tab,
            text=(
                "Conseil pour les rapports SSAS : conservez 120 s de délai maximal, "
                "5 s de calme réseau et 3 s de stabilité visuelle."
            ),
            foreground="#53657d",
            wraplength=820,
        ).grid(row=row + 1, column=0, columnspan=4, sticky="w", pady=(12, 0))

        ttk.Separator(tab).grid(row=row + 2, column=0, columnspan=4, sticky="ew", pady=18)
        ttk.Label(tab, text="Dossiers locaux", font=("Segoe UI", 11, "bold")).grid(
            row=row + 3, column=0, columnspan=4, sticky="w", pady=(0, 8)
        )
        self._add_entry(tab, row + 4, 0, "Captures", "paths.captures", columnspan=3)
        self._add_entry(tab, row + 5, 0, "Journaux", "paths.logs", columnspan=3)

    def _build_smtp_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=18)
        notebook.add(tab, text="Serveur SMTP")
        tab.columnconfigure(1, weight=1)

        row = 0
        self._add_check(tab, row, 0, "Activer l’envoi SMTP", "smtp.enabled", columnspan=2)
        row += 1
        self._add_entry(tab, row, 0, "Serveur", "smtp.server")
        row += 1
        self._add_entry(tab, row, 0, "Port", "smtp.port")
        row += 1
        self._add_entry(tab, row, 0, "Expéditeur", "smtp.sender")
        row += 1
        self._add_entry(tab, row, 0, "Timeout (s)", "smtp.timeout_seconds")
        row += 1
        self._add_check(tab, row, 0, "Utiliser STARTTLS", "smtp.starttls", columnspan=2)

        ttk.Label(
            tab,
            text=(
                "PBIRS Mailer ne stocke aucun mot de passe dans config.json. "
                "Commencez avec l’envoi désactivé."
            ),
            foreground="#53657d",
            wraplength=700,
        ).grid(row=row + 1, column=0, columnspan=2, sticky="w", pady=(22, 0))

    def _build_subscriptions_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=14)
        notebook.add(tab, text="Souscriptions")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        columns = ("enabled", "name", "url", "page", "recipients", "filename")
        self.tree = ttk.Treeview(tab, columns=columns, show="headings", selectmode="browse")
        headings = {
            "enabled": "Active",
            "name": "Nom",
            "url": "URL du rapport",
            "page": "Page",
            "recipients": "Destinataires",
            "filename": "Fichier",
        }
        widths = {
            "enabled": 70,
            "name": 180,
            "url": 360,
            "page": 150,
            "recipients": 110,
            "filename": 180,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda _event: self._edit_subscription())

        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        horizontal = ttk.Scrollbar(tab, orient="horizontal", command=self.tree.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=horizontal.set)

        buttons = ttk.Frame(tab)
        buttons.grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 0))
        actions = (
            ("Ajouter", self._add_subscription),
            ("Modifier", self._edit_subscription),
            ("Dupliquer", self._duplicate_subscription),
            ("Activer / désactiver", self._toggle_subscription),
            ("Supprimer", self._remove_subscription),
        )
        for index, (label, command) in enumerate(actions):
            button = ttk.Button(buttons, text=label, command=command)
            button.pack(side="left", padx=(8 if index else 0, 0))
            self.subscription_buttons.append(button)

    def _attach_change_tracking(self) -> None:
        for variable in (*self.entries.values(), *self.booleans.values()):
            variable.trace_add("write", self._mark_dirty)

    def _mark_dirty(self, *_args: str) -> None:
        if not self._tracking_changes or self.running:
            return
        self.dirty = True
        self.status.set("Modifications non enregistrées.")

    def _on_close(self) -> None:
        if self.running:
            messagebox.showwarning(
                "Test en cours",
                "Attendez la fin du test avant de fermer le Configurator.",
                parent=self.root,
            )
            return
        if not self.dirty:
            self.root.destroy()
            return

        answer = messagebox.askyesnocancel(
            "Modifications non enregistrées",
            "Voulez-vous enregistrer les modifications avant de fermer ?",
            parent=self.root,
        )
        if answer is None:
            return
        if answer and not self._save(show_success=False):
            return
        self.root.destroy()

    def _add_entry(
        self,
        parent: ttk.Frame,
        row: int,
        column: int,
        label: str,
        key: str,
        *,
        columnspan: int = 1,
    ) -> None:
        variable = tk.StringVar()
        self.entries[key] = variable
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=(0, 10), pady=7)
        ttk.Entry(parent, textvariable=variable).grid(
            row=row,
            column=column + 1,
            columnspan=columnspan,
            sticky="ew",
            padx=(0, 20),
            pady=7,
        )

    def _add_check(
        self,
        parent: ttk.Frame,
        row: int,
        column: int,
        label: str,
        key: str,
        *,
        columnspan: int = 1,
    ) -> None:
        variable = tk.BooleanVar()
        self.booleans[key] = variable
        ttk.Checkbutton(parent, text=label, variable=variable).grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="w",
            pady=7,
        )

    def _load_form_values(self) -> None:
        browser = self.document.get("browser", {})
        smtp = self.document.get("smtp", {})
        paths = self.document.get("paths", {})
        sources = {"browser": browser, "smtp": smtp, "paths": paths}
        for key, variable in self.entries.items():
            section, field = key.split(".", 1)
            variable.set(str(sources.get(section, {}).get(field, "")))
        for key, variable in self.booleans.items():
            section, field = key.split(".", 1)
            variable.set(bool(sources.get(section, {}).get(field, False)))

    def _refresh_subscriptions(self) -> None:
        selected_before = self.tree.selection()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, subscription in enumerate(self.subscriptions):
            page = subscription.get("page") or {}
            page_name = page.get("display_name") or page.get("internal_name") or "—"
            recipients = subscription.get("recipients") or []
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    "Oui" if subscription.get("enabled", True) else "Non",
                    subscription.get("name", ""),
                    subscription.get("url", ""),
                    page_name,
                    len(recipients),
                    subscription.get("filename", ""),
                ),
            )

        if selected_before and self.tree.exists(selected_before[0]):
            selected = selected_before[0]
        elif len(self.subscriptions) == 1:
            selected = "0"
        else:
            return
        self.tree.selection_set(selected)
        self.tree.focus(selected)
        self.tree.see(selected)

    def _selected_index(self) -> int | None:
        selected = self.tree.selection()
        if not selected and len(self.subscriptions) == 1:
            self.tree.selection_set("0")
            self.tree.focus("0")
            return 0
        if not selected:
            messagebox.showinfo(
                "Souscriptions",
                "Sélectionnez d’abord une souscription dans le tableau.",
                parent=self.root,
            )
            return None
        return int(selected[0])

    def _add_subscription(self) -> None:
        previous = copy.deepcopy(self.subscriptions)

        def save(result: dict[str, Any]) -> bool:
            self.subscriptions.append(result)
            return self._commit_subscription_change(
                previous,
                "Souscription ajoutée et enregistrée.",
                selected_index=len(self.subscriptions) - 1,
            )

        dialog = SubscriptionDialog(self.root, on_save=save)
        self.root.wait_window(dialog)
        if dialog.result is None:
            self.status.set("Ajout annulé : config.json n’a pas été modifié.")

    def _edit_subscription(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        previous = copy.deepcopy(self.subscriptions)

        def save(result: dict[str, Any]) -> bool:
            self.subscriptions[index] = result
            return self._commit_subscription_change(
                previous,
                f"Souscription « {result['name']} » modifiée et enregistrée.",
                selected_index=index,
            )

        dialog = SubscriptionDialog(
            self.root,
            self.subscriptions[index],
            on_save=save,
        )
        self.root.wait_window(dialog)
        if dialog.result is None:
            self.status.set("Modification annulée : config.json n’a pas été modifié.")

    def _duplicate_subscription(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        duplicate = copy.deepcopy(self.subscriptions[index])
        duplicate["name"] = f"{duplicate.get('name', 'Souscription')} - copie"
        filename = str(duplicate.get("filename", "capture.png"))
        file_path = Path(filename)
        duplicate["filename"] = f"{file_path.stem}-copie{file_path.suffix or '.png'}"
        previous = copy.deepcopy(self.subscriptions)

        def save(result: dict[str, Any]) -> bool:
            self.subscriptions.append(result)
            return self._commit_subscription_change(
                previous,
                "Souscription dupliquée et enregistrée.",
                selected_index=len(self.subscriptions) - 1,
            )

        dialog = SubscriptionDialog(self.root, duplicate, on_save=save)
        self.root.wait_window(dialog)
        if dialog.result is None:
            self.status.set("Duplication annulée : config.json n’a pas été modifié.")

    def _toggle_subscription(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        previous = copy.deepcopy(self.subscriptions)
        current = bool(self.subscriptions[index].get("enabled", True))
        self.subscriptions[index]["enabled"] = not current
        self._commit_subscription_change(
            previous,
            "État de la souscription modifié et enregistré.",
            selected_index=index,
        )

    def _remove_subscription(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        if len(self.subscriptions) == 1:
            messagebox.showwarning(
                "Suppression impossible",
                (
                    "La configuration doit contenir au moins une souscription.\n\n"
                    "Ajoutez d’abord une autre souscription, ou désactivez celle-ci."
                ),
                parent=self.root,
            )
            return
        name = self.subscriptions[index].get("name", "cette souscription")
        if not messagebox.askyesno(
            "Supprimer la souscription",
            f"Supprimer « {name} » de la configuration ?",
            parent=self.root,
        ):
            return
        previous = copy.deepcopy(self.subscriptions)
        del self.subscriptions[index]
        self._commit_subscription_change(
            previous,
            "Souscription supprimée et configuration enregistrée.",
        )

    def _commit_subscription_change(
        self,
        previous: list[dict[str, Any]],
        success_message: str,
        *,
        selected_index: int | None = None,
    ) -> bool:
        """Persist a subscription edit immediately, or restore the previous state."""
        if not self._save(show_success=False):
            self.subscriptions = previous
            self._refresh_subscriptions()
            self.status.set("Modification annulée : config.json n’a pas été remplacé.")
            return False

        self._refresh_subscriptions()
        if selected_index is not None and selected_index < len(self.subscriptions):
            self.tree.selection_set(str(selected_index))
            self.tree.see(str(selected_index))
        self.status.set(success_message)
        return True

    def _build_document(self) -> dict[str, Any]:
        document = copy.deepcopy(self.document)
        browser = document.setdefault("browser", {})
        smtp = document.setdefault("smtp", {})
        paths = document.setdefault("paths", {})

        browser.update(
            {
                "channel": self.entries["browser.channel"].get().strip(),
                "headless": self.booleans["browser.headless"].get(),
                "viewport_width": self._integer("browser.viewport_width", "Largeur"),
                "viewport_height": self._integer("browser.viewport_height", "Hauteur"),
                "page_timeout_seconds": self._number(
                    "browser.page_timeout_seconds", "Timeout page"
                ),
                "frame_timeout_seconds": self._number(
                    "browser.frame_timeout_seconds", "Timeout frame"
                ),
                "render_timeout_seconds": self._number(
                    "browser.render_timeout_seconds", "Timeout rendu"
                ),
                "render_quiet_seconds": self._number(
                    "browser.render_quiet_seconds", "Calme réseau"
                ),
                "render_stable_seconds": self._number(
                    "browser.render_stable_seconds", "Stabilité visuelle"
                ),
            }
        )
        smtp.update(
            {
                "enabled": self.booleans["smtp.enabled"].get(),
                "server": self.entries["smtp.server"].get().strip(),
                "port": self._integer("smtp.port", "Port SMTP"),
                "sender": self.entries["smtp.sender"].get().strip(),
                "timeout_seconds": self._number("smtp.timeout_seconds", "Timeout SMTP"),
                "starttls": self.booleans["smtp.starttls"].get(),
            }
        )
        paths.update(
            {
                "captures": self.entries["paths.captures"].get().strip(),
                "logs": self.entries["paths.logs"].get().strip(),
            }
        )
        document["subscriptions"] = copy.deepcopy(self.subscriptions)
        return document

    def _integer(self, key: str, label: str) -> int:
        value = self.entries[key].get().strip()
        try:
            return int(value)
        except ValueError as exc:
            raise ConfiguratorError(f"{label} doit être un nombre entier.") from exc

    def _number(self, key: str, label: str) -> int | float:
        value = self.entries[key].get().strip()
        try:
            number = float(value)
        except ValueError as exc:
            raise ConfiguratorError(f"{label} doit être un nombre.") from exc
        return int(number) if number.is_integer() else number

    def _validate(self) -> None:
        try:
            document = self._build_document()
            validate_config_document(document, self.config_path.parent)
        except (ConfigurationError, ConfiguratorError, OSError) as exc:
            messagebox.showerror("Configuration invalide", str(exc))
            self.status.set("La configuration contient une erreur.")
            return
        messagebox.showinfo("Configuration valide", "La configuration est valide.")
        self.status.set("Configuration valide.")

    def _save(self, *, show_success: bool = True) -> bool:
        try:
            document = self._build_document()
            if document == self.document:
                self.dirty = False
                self.status.set("Aucune modification à enregistrer.")
                if show_success:
                    messagebox.showinfo(
                        "PBIRS Mailer",
                        "La configuration est déjà à jour.",
                        parent=self.root,
                    )
                return True
            backup = save_config_document(self.config_path, document)
        except (ConfigurationError, ConfiguratorError, OSError) as exc:
            messagebox.showerror("Enregistrement impossible", str(exc))
            self.status.set("La configuration n’a pas été enregistrée.")
            return False

        self.document = document
        self.dirty = False
        self.status.set("Configuration enregistrée.")
        if show_success:
            details = f"Configuration active enregistrée :\n{self.config_path.name}"
            if backup is not None:
                details += f"\n\nAncienne configuration sauvegardée :\n{backup.name}"
            messagebox.showinfo("PBIRS Mailer", details, parent=self.root)
        return True

    def _run_command(self, mode: str) -> None:
        if self.running or not self._save(show_success=False):
            return
        self.running = True
        self._set_run_buttons("disabled")
        self.status.set("Exécution du test en cours…")

        thread = threading.Thread(target=self._execute_worker, args=(mode,), daemon=True)
        thread.start()

    def _execute_worker(self, mode: str) -> None:
        command = [
            sys.executable,
            "-m",
            "pbirs_mailer",
            "--config",
            str(self.config_path),
            mode,
            "--verbose",
        ]
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            result = subprocess.run(
                command,
                cwd=self.config_path.parent,
                capture_output=True,
                text=True,
                check=False,
                creationflags=creation_flags,
            )
            output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
            return_code = result.returncode
        except OSError as exc:
            output = f"Impossible de lancer PBIRS Mailer : {exc}"
            return_code = 2
        self.root.after(0, self._show_command_result, return_code, output)

    def _show_command_result(self, return_code: int, output: str) -> None:
        self.running = False
        self._set_run_buttons("normal")
        dialog = tk.Toplevel(self.root)
        dialog.title("Résultat du test PBIRS Mailer")
        dialog.geometry("900x520")
        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill="both", expand=True)
        text_widget = tk.Text(frame, wrap="word", font=("Consolas", 10))
        text_widget.pack(fill="both", expand=True)
        details = (
            f"Configuration utilisée : {self.config_path}\n\n{output or 'Aucun message retourné.'}"
        )
        text_widget.insert("1.0", details)
        text_widget.configure(state="disabled")
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(10, 0))

        def copy_diagnostic() -> None:
            self.root.clipboard_clear()
            self.root.clipboard_append(details)
            self.status.set("Diagnostic copié dans le presse-papiers.")

        ttk.Button(buttons, text="Copier le diagnostic", command=copy_diagnostic).pack(side="left")
        ttk.Button(buttons, text="Fermer", command=dialog.destroy).pack(side="right")
        dialog.transient(self.root)
        dialog.lift()
        if return_code == 0:
            self.status.set("Test terminé avec succès.")
        else:
            self.status.set(f"Test terminé avec le code d’erreur {return_code}.")

    def _set_run_buttons(self, state: str) -> None:
        self.capture_button.configure(state=state)
        self.validate_button.configure(state=state)
        self.save_button.configure(state=state)
        for button in self.subscription_buttons:
            button.configure(state=state)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Configure PBIRS Mailer avec une interface locale."
    )
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = tk.Tk()
        ConfiguratorApp(root, args.config)
    except (ConfigurationError, OSError, tk.TclError) as exc:
        try:
            messagebox.showerror("PBIRS Mailer Configurator", str(exc))
        except tk.TclError:
            print(f"Erreur du Configurator : {exc}", file=sys.stderr)
        return 2
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
