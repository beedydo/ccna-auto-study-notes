"""AEtest script: every interface with an IP address must be up/up.

Run it through the job file:  pyats run job job.py --testbed-file testbed.yaml
"""
import logging

from pyats import aetest

log = logging.getLogger(__name__)


class CommonSetup(aetest.CommonSetup):

    @aetest.subsection
    def connect(self, testbed):
        dev = testbed.devices["csr1"]
        dev.connect(log_stdout=False, learn_hostname=True)
        self.parent.parameters["dev"] = dev          # share with the testcases


class InterfacesUp(aetest.Testcase):

    @aetest.setup
    def collect(self, dev):
        self.brief = dev.parse("show ip interface brief")["interface"]

    @aetest.test
    def addressed_interfaces_up(self):
        bad = [name for name, i in self.brief.items()
               if i["ip_address"] != "unassigned" and i["protocol"] != "up"]
        if bad:
            self.failed(f"down with an IP: {bad}")
        self.passed("every addressed interface is up")

    @aetest.test
    def no_admin_down(self):
        shut = [n for n, i in self.brief.items() if i["status"] == "administratively down"]
        if shut:
            self.failed(f"shutdown: {shut}")

    @aetest.cleanup
    def done(self):
        log.info("checked %d interfaces", len(self.brief))


class DefaultRoute(aetest.Testcase):

    @aetest.test
    def has_default(self, dev):
        routes = dev.learn("routing").info["vrf"]["default"]["address_family"]["ipv4"]["routes"]
        assert "0.0.0.0/0" in routes, "no default route"


class CommonCleanup(aetest.CommonCleanup):

    @aetest.subsection
    def disconnect(self, dev):
        dev.disconnect()


if __name__ == "__main__":                             # standalone: python interface_check.py
    from genie.testbed import load
    aetest.main(testbed=load("testbed.yaml"))
