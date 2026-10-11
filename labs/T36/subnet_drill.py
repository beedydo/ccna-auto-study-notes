"""T36 subnetting drill: random interface addresses, work out the answers, then check.

python3 subnet_drill.py            # 5 questions, answers hidden until you press Enter
python3 subnet_drill.py --seed 36 --count 3 --show   # repeatable set, answers printed straight away
"""
import argparse
import ipaddress as ip
import random


def make_question(rng):
    prefix = rng.randint(17, 30)
    first = rng.choice([10, 172, 192])
    second = {10: rng.randint(0, 255), 172: rng.randint(16, 31), 192: 168}[first]
    addr = ip.ip_address(f"{first}.{second}.{rng.randint(0, 255)}.{rng.randint(1, 254)}")
    return ip.ip_interface(f"{addr}/{prefix}")


def answer(iface):
    net = iface.network
    return (f"network {net.network_address}  broadcast {net.broadcast_address}  "
            f"mask {net.netmask}  usable {2 ** (32 - net.prefixlen) - 2}  "
            f"range {net.network_address + 1} - {net.broadcast_address - 1}")


def main():
    parser = argparse.ArgumentParser(description="Subnetting drill for T36")
    parser.add_argument("--count", type=int, default=5, help="number of questions")
    parser.add_argument("--seed", type=int, default=None, help="seed for a repeatable set")
    parser.add_argument("--show", action="store_true", help="print answers without pausing")
    args = parser.parse_args()
    rng = random.Random(args.seed)
    for n in range(1, args.count + 1):
        iface = make_question(rng)
        print(f"Q{n}. {iface}  -> network? broadcast? mask? usable hosts? first/last?")
        if not args.show:
            input("   (Enter to reveal) ")
        print("   " + answer(iface))


if __name__ == "__main__":
    main()
