"""Tests for link_monitor.py: the model is tested with no view and no real observer (T03).

Run: python3 -m pytest -q test_link_monitor.py   (or: python3 test_link_monitor.py)
"""
from link_monitor import InterfaceModel


class FakeObserver:
    """Stand-in observer: records events instead of printing or sending them."""

    def __init__(self):
        self.events = []

    def update(self, event):
        self.events.append(event)


def test_change_notifies_observer():
    model, fake = InterfaceModel("sw1"), FakeObserver()
    model.attach(fake)
    model.set_status("Gi1/0/1", "up")
    assert fake.events == [{"host": "sw1", "intf": "Gi1/0/1", "old": None, "new": "up"}]


def test_same_status_does_not_notify():
    model, fake = InterfaceModel("sw1"), FakeObserver()
    model.attach(fake)
    model.set_status("Gi1/0/1", "up")
    model.set_status("Gi1/0/1", "up")
    assert len(fake.events) == 1


def test_detached_observer_gets_nothing():
    model, fake = InterfaceModel("sw1"), FakeObserver()
    model.attach(fake)
    model.detach(fake)
    model.set_status("Gi1/0/1", "down")
    assert fake.events == []


def test_model_rejects_bad_status():
    model = InterfaceModel("sw1")
    try:
        model.set_status("Gi1/0/1", "flapping")
    except ValueError:
        return
    raise AssertionError("ValueError not raised")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
