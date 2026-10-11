"""Device classes for the T02 reference program."""

MAX_VLAN = 4094                                   # module-level (global) constant


class Device:
    """Base class for any managed device."""

    vendor = "Cisco"                              # class attribute: one value shared by all instances
    connections = 0                               # class attribute used as a shared counter

    def __init__(self, hostname, mgmt_ip, port=22):
        self.hostname = hostname                  # instance attributes: one set per object
        self.mgmt_ip = mgmt_ip
        self.port = port
        self._token = None                        # leading underscore = internal (encapsulation)

    def connect(self):
        """Instance method: works on one object through self."""
        Device.connections += 1
        self._token = f"tok-{self.hostname}"
        return f"{self.hostname}: SSH {self.mgmt_ip}:{self.port}"

    def is_connected(self):
        """Public way to read the internal _token."""
        return self._token is not None

    @classmethod
    def from_dict(cls, data):
        """Class method: gets the class as cls, so IOSXE.from_dict() builds an IOSXE."""
        return cls(data["hostname"], data["mgmt_ip"])

    @staticmethod
    def is_valid_vlan(vlan_id):
        """Static method: a plain helper that needs neither self nor cls."""
        return 1 <= vlan_id <= MAX_VLAN


class IOSXE(Device):                              # inheritance: an IOSXE is a Device
    def __init__(self, hostname, mgmt_ip, port=443):
        super().__init__(hostname, mgmt_ip, port)  # run Device.__init__ first
        self.api = "RESTCONF"                     # then add what is specific to IOS XE

    def connect(self):                            # override: same name, new behaviour (polymorphism)
        super().connect()                         # reuse the parent's counter and token logic
        return f"{self.hostname}: {self.api} https://{self.mgmt_ip}:{self.port}/restconf"


class NXOS(Device):                               # no __init__ here, so Device.__init__ is used
    def connect(self):
        super().connect()
        return f"{self.hostname}: NX-API https://{self.mgmt_ip}/ins"
