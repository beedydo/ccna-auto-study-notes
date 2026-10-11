"""netlib: tiny network-automation package (T02 reference program)."""
from netlib.devices import Device, IOSXE, NXOS  # re-export: lets callers write `from netlib import IOSXE`
