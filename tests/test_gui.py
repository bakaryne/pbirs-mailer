from typing import Any

import pbirs_mailer.gui as gui_module
from pbirs_mailer.gui import ConfiguratorApp


class FakeStatus:
    def __init__(self) -> None:
        self.value = ""

    def set(self, value: str) -> None:
        self.value = value


class FakeTree:
    def __init__(self) -> None:
        self.selected: str | None = None
        self.visible: str | None = None

    def selection_set(self, item: str) -> None:
        self.selected = item

    def selection(self) -> tuple[str, ...]:
        return (self.selected,) if self.selected is not None else ()

    def focus(self, item: str) -> None:
        self.selected = item

    def see(self, item: str) -> None:
        self.visible = item


class FakeRoot:
    def __init__(self) -> None:
        self.destroyed = False

    def wait_window(self, _dialog: object) -> None:
        return

    def destroy(self) -> None:
        self.destroyed = True


def build_app(subscriptions: list[dict[str, Any]]) -> ConfiguratorApp:
    app = object.__new__(ConfiguratorApp)
    app.subscriptions = subscriptions
    app.status = FakeStatus()
    app.tree = FakeTree()
    app.root = FakeRoot()
    app._refresh_subscriptions = lambda: None
    return app


def test_subscription_change_is_kept_after_successful_save() -> None:
    app = build_app([{"name": "New report"}])
    app._save = lambda *, show_success: True

    saved = app._commit_subscription_change(
        [{"name": "Example report"}],
        "Souscription modifiée et enregistrée.",
        selected_index=0,
    )

    assert app.subscriptions == [{"name": "New report"}]
    assert saved is True
    assert app.status.value == "Souscription modifiée et enregistrée."
    assert app.tree.selected == "0"


def test_subscription_change_is_rolled_back_when_save_fails() -> None:
    app = build_app([{"name": "New report"}])
    app._save = lambda *, show_success: False

    saved = app._commit_subscription_change([{"name": "Example report"}], "unused")

    assert app.subscriptions == [{"name": "Example report"}]
    assert saved is False
    assert app.status.value == "Modification annulée : config.json n’a pas été remplacé."


def test_only_subscription_is_selected_automatically() -> None:
    app = build_app([{"name": "Example report"}])

    assert app._selected_index() == 0
    assert app.tree.selected == "0"


def test_edit_subscription_passes_dialog_result_directly_to_save(monkeypatch) -> None:
    updated = {"name": "Real report", "url": "https://pbirs.example.org/real"}

    class FakeDialog:
        def __init__(self, _parent, _subscription, on_save) -> None:
            assert on_save(updated) is True
            self.result = updated

    app = build_app([{"name": "Example report", "url": "http://old.example.org"}])
    app.tree.selected = "0"
    app._commit_subscription_change = lambda *_args, **_kwargs: True
    monkeypatch.setattr(gui_module, "SubscriptionDialog", FakeDialog)

    app._edit_subscription()

    assert app.subscriptions == [updated]


def test_save_does_not_create_backup_when_document_is_unchanged(monkeypatch) -> None:
    app = build_app([])
    app.document = {"version": 1}
    app.dirty = True
    app._build_document = lambda: {"version": 1}

    def unexpected_save(*_args, **_kwargs) -> None:
        raise AssertionError("save_config_document ne doit pas être appelé")

    monkeypatch.setattr(gui_module, "save_config_document", unexpected_save)

    assert app._save(show_success=False) is True
    assert app.dirty is False
    assert app.status.value == "Aucune modification à enregistrer."


def test_close_without_pending_change_destroys_window() -> None:
    app = build_app([])
    app.running = False
    app.dirty = False

    app._on_close()

    assert app.root.destroyed is True
