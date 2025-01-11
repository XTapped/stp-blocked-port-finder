import re
import sys
from typing import List, Tuple, Optional
from stp_simulation import (
    Topology,
    STPSimulator,
    find_solution_with_cost_assignments,
    check_blocked_ports_match,
)

PRIORITY_INCREMENT = 4096


def parse_input_file(filepath: str) -> Tuple[Topology, List[Tuple[str, str]]]:
    topo = Topology()
    desired_blocked = []

    with open(filepath, "r") as f:
        lines = f.readlines()

    lines = [line.strip() for line in lines if line.strip()]

    mode = None

    for line in lines:
        if line.startswith("Topology:"):
            mode = "topology"
            continue
        elif line.startswith("Desired Blocked Ports:"):
            mode = "blocked"
            continue

        if mode == "topology":
            match = re.match(r"(S\d+)\s*->\s*(S\d+)", line)
            if match:
                s1, s2 = match.groups()
                topo.add_link(s1, s2)

        elif mode == "blocked":
            match = re.match(r"(S\d+)\s*\(blocked\)\s*->\s*(S\d+)", line)
            if match:
                s1, s2 = match.groups()
                desired_blocked.append((s1, s2))

    return topo, desired_blocked


def assign_priorities(topo: Topology, forced_root: Optional[str] = None) -> None:
    switch_names = list(topo.switches.keys())
    switch_names.sort(key=lambda name: int(name.replace("S", "")))

    if forced_root and forced_root in topo.switches:
        switch_names.remove(forced_root)
        ordered = [forced_root] + switch_names
    else:
        ordered = switch_names

    for i, sw_name in enumerate(ordered):
        topo.switches[sw_name].priority = i * PRIORITY_INCREMENT

    print("\nAssigned Switch Priorities:")
    for sw_name in sorted(
        topo.switches.keys(), key=lambda name: int(name.replace("S", ""))
    ):
        print(f"{sw_name} => {topo.switches[sw_name].priority}")


def main():
    input_path = "input.txt"
    topology, desired_blocked_list = parse_input_file(input_path)

    forced_root = (
        input("Enter the root switch (e.g., S2) or leave blank for default: ").strip()
        or None
    )

    assign_priorities(topology, forced_root)

    stp = STPSimulator(topology)
    stp.run_stp()
    actual_blocked = stp.get_blocked_ports()

    if check_blocked_ports_match(actual_blocked, desired_blocked_list):
        print(
            "\nSolution found with default cost=4 on all links (and the assigned priorities)!"
        )
        print("Blocked ports:")
        for b in actual_blocked:
            print(f"  {b[0]} (blocked) -> {b[1]}")
    else:
        solution_costs = find_solution_with_cost_assignments(
            topology, desired_blocked_list
        )

        if solution_costs is not None:
            print("\nA solution was found!\n")
            for (sw1, sw2), cost in solution_costs.items():
                print(f"Link {sw1} <-> {sw2}: cost={cost}")
            topology.set_link_costs(solution_costs)
            stp = STPSimulator(topology)
            stp.run_stp()
        else:
            print(
                "No solution found. The blocked port configuration is most likely impossible."
            )


if __name__ == "__main__":
    main()
