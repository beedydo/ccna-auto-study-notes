"""Interface-status monitor: the Observer pattern and an MVC split in one program (T03).

Run: python3 link_monitor.py
"""
import json


# ---------------------------------------------------------------- Observer
class Subject:
    """Observer pattern: keeps a list of observers and notifies each one on change."""

    def __init__(self):
        self._observers = []                       # the subscriber list

    def attach(self, observer):                    # subscribe at run time
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):                    # unsubscribe at run time
        self._observers.remove(observer)

    def notify(self, event):                       # push the change to every observer
        for observer in self._observers:
            observer.update(event)                 # the ONLY thing the subject knows about them


class SyslogObserver:
    """Observer 1: writes an IOS-style syslog line for every change."""

    def update(self, event):
        print(f"  [syslog] %LINK-3-UPDOWN: Interface {event['intf']}, changed state to {event['new']}")


class AlertObserver:
    """Observer 2: only cares about 'down'; would POST to a webhook (here: keeps a list)."""

    def __init__(self):
        self.sent = []

    def update(self, event):
        if event["new"] == "down":
            self.sent.append(event)
            print(f"  [alert]  {event['host']} {event['intf']} DOWN (was {event['old']}) -> webhook")


# ---------------------------------------------------------------- MVC: Model
class InterfaceModel(Subject):
    """Model: interface data + business rules. Knows nothing about display or input."""

    VALID = ("up", "down", "admin-down")

    def __init__(self, hostname):
        super().__init__()
        self.hostname = hostname
        self._status = {}

    def set_status(self, intf, status):
        if status not in self.VALID:               # business rule lives in the model
            raise ValueError(f"invalid status {status!r}, expected one of {self.VALID}")
        old = self._status.get(intf)
        if old == status:
            return                                 # no change -> no notification
        self._status[intf] = status
        self.notify({"host": self.hostname, "intf": intf, "old": old, "new": status})

    def interfaces(self):
        return dict(self._status)                  # a copy: views can't change the model


# ---------------------------------------------------------------- MVC: Views
class TableView:
    """View 1: human-readable table."""

    def render(self, hostname, interfaces):
        print(f"  {hostname:<6}{'Interface':<12}Status")
        for intf, status in sorted(interfaces.items()):
            print(f"  {'':<6}{intf:<12}{status}")


class JsonView:
    """View 2: same model data, rendered for an API client."""

    def render(self, hostname, interfaces):
        print("  " + json.dumps({"host": hostname, "interfaces": interfaces}, sort_keys=True))


# ---------------------------------------------------------------- MVC: Controller
class Controller:
    """Controller: takes user input, updates the model, selects the view."""

    def __init__(self, model, views):
        self.model = model
        self.views = views                         # {"table": TableView(), "json": JsonView()}

    def handle(self, command):
        print(f"> {command}")
        verb, *args = command.split()
        if verb == "set":                          # input -> update the model
            intf, status = args
            try:
                self.model.set_status(intf, status)
            except ValueError as err:
                print(f"  error: {err}")
        elif verb == "show":                       # input -> pick a view, feed it model data
            view = self.views[args[0]]
            view.render(self.model.hostname, self.model.interfaces())
        else:
            print(f"  error: unknown command {verb!r}")


def main():
    model = InterfaceModel("sw1")
    syslog, alerts = SyslogObserver(), AlertObserver()
    model.attach(syslog)                           # two observers subscribe
    model.attach(alerts)

    ctl = Controller(model, {"table": TableView(), "json": JsonView()})
    for cmd in ["set Gi1/0/1 up", "set Gi1/0/2 up", "set Gi1/0/2 down",
                "set Gi1/0/2 down", "set Gi1/0/3 flapping", "show table"]:
        ctl.handle(cmd)

    model.detach(alerts)                           # unsubscribe at run time
    print("(alerts observer detached)")
    for cmd in ["set Gi1/0/1 down", "show json"]:
        ctl.handle(cmd)

    print("Alerts sent:", len(alerts.sent))


if __name__ == "__main__":
    main()
