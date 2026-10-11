from pyats import aetest


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect(self):
        raise ConnectionError("csr1 unreachable")     # not an assert -> ERRORED


class InterfacesUp(aetest.Testcase):
    @aetest.test
    def check(self):
        assert True


class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def disconnect(self):
        pass


if __name__ == "__main__":
    aetest.main()
