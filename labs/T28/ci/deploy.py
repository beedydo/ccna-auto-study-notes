"""Deploy stage (simulated): copy the artifact into an environment, then run a post-deploy check."""
import argparse
import pathlib
import shutil
import subprocess
import sys

p = argparse.ArgumentParser(description="Deploy netinv.pyz to one environment")
p.add_argument("--env", required=True, choices=["dev", "staging", "prod"])
p.add_argument("--artifact", required=True)
p.add_argument("--out", required=True)
args = p.parse_args()

target = pathlib.Path(args.out, "envs", args.env)
target.mkdir(parents=True, exist_ok=True)
shutil.copy2(args.artifact, target / "netinv.pyz")   # the SAME artifact goes to every env
print(f"  deployed dist/netinv.pyz -> envs/{args.env}/netinv.pyz")

run = subprocess.run([sys.executable, str(target / "netinv.pyz")], capture_output=True, text=True)
if run.returncode != 0 or "3 devices" not in run.stdout:   # post-deploy smoke check
    print(f"  post-deploy check FAILED in {args.env}")
    sys.exit(1)
print(f"  post-deploy check OK in {args.env}: " + run.stdout.splitlines()[4].strip())
