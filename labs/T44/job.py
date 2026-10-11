"""pyATS job file: `pyats run job job.py --testbed-file testbed.yaml`."""
import os

from pyats.easypy import run

HERE = os.path.dirname(os.path.abspath(__file__))


def main(runtime):
    # runtime.testbed is the --testbed-file, already loaded
    run(testscript=os.path.join(HERE, "interface_check.py"),
        runtime=runtime, taskid="interface_check", testbed=runtime.testbed)
