from typing import Dict, List, Tuple, Optional
import itertools

# WARNING: Don't touch. Putting more cost options will blow up the search space exponentially!!!
COST_OPTIONS = [4, 16, 32]


class Link:
    def __init__(self, switch1: str, switch2: str, cost: int = 4) -> None:
        self.switch1 = switch1
        self.switch2 = switch2
        self.cost = cost

    def involves_switch(self, sw: str) -> bool:
        return (self.switch1 == sw) or (self.switch2 == sw)


class Switch:
    def __init__(self, name: str, priority: int = 99999) -> None:
        self.name = name
        self.priority = priority

        self.root_port: Optional[Link] = None
        self.designated_ports: List[Link] = []
        self.blocked_ports: List[Link] = []


class Topology:
    def __init__(self) -> None:
        self.switches: Dict[str, Switch] = {}
        self.links: List[Link] = []

    def add_link(self, switch1: str, switch2: str) -> None:
        if switch1 not in self.switches:
            self.switches[switch1] = Switch(switch1)
        if switch2 not in self.switches:
            self.switches[switch2] = Switch(switch2)

        self.links.append(Link(switch1, switch2, cost=4))

    def set_link_costs(self, cost_assignments: Dict[Tuple[str, str], int]) -> None:
        for link in self.links:
            pair_direct = (link.switch1, link.switch2)
            pair_inverse = (link.switch2, link.switch1)
            if pair_direct in cost_assignments:
                link.cost = cost_assignments[pair_direct]
            elif pair_inverse in cost_assignments:
                link.cost = cost_assignments[pair_inverse]

    def get_links_for_switch(self, sw_name: str) -> List[Link]:
        return [link for link in self.links if link.involves_switch(sw_name)]

    def get_other_side(self, link: Link, sw_name: str) -> str:
        return link.switch2 if link.switch1 == sw_name else link.switch1


class STPSimulator:
    """
    Simulates a simplified STP:
    1. Elect root bridge (lowest priority) unless user forced a root.
    2. Each non-root switch picks root port (lowest cost path to root).
       Tie-breaker: switch with lower priority on the path.
    3. Pair root ports with designated ports.
    4. For remaining 'naked' links, choose designated side by comparing root-port cost,
       tie-breaker is lower priority.
    5. All other ports are blocked.
    """

    def __init__(self, topology: Topology) -> None:
        self.topology = topology
        self.root_switch: Optional[Switch] = None

    def run_stp(self) -> None:
        for sw in self.topology.switches.values():
            sw.root_port = None
            sw.designated_ports = []
            sw.blocked_ports = []

        self._elect_root_bridge()

        self._determine_root_ports()

        self._assign_designated_ports_for_root_ports()

        self._assign_designated_ports_for_naked_links()

        self._block_remaining_ports()

    def _elect_root_bridge(self) -> None:
        all_switches = list(self.topology.switches.values())
        self.root_switch = min(all_switches, key=lambda sw: sw.priority)

    def _determine_root_ports(self) -> None:
        if not self.root_switch:
            return

        root_name = self.root_switch.name
        distances = self._calculate_distances_to_root(root_name)

        for sw_name, switch in self.topology.switches.items():
            if sw_name == root_name:
                continue
            possible_root_ports = []
            for link in self.topology.get_links_for_switch(sw_name):
                other_side = self.topology.get_other_side(link, sw_name)
                cost_via_link = distances[other_side] + link.cost
                possible_root_ports.append((link, cost_via_link, other_side))

            possible_root_ports.sort(
                key=lambda x: (x[1], self.topology.switches[x[2]].priority)
            )
            best_link = possible_root_ports[0][0]
            switch.root_port = best_link

    def _calculate_distances_to_root(self, root_name: str) -> Dict[str, int]:
        # Dijkstra's algorithm to calculate the shortest path to root
        unvisited = set(self.topology.switches.keys())
        dist = {sw: float("inf") for sw in unvisited}
        dist[root_name] = 0

        while unvisited:
            current_sw = min(unvisited, key=lambda x: dist[x])
            unvisited.remove(current_sw)

            for link in self.topology.get_links_for_switch(current_sw):
                neighbor = self.topology.get_other_side(link, current_sw)
                if neighbor in unvisited:
                    alt = dist[current_sw] + link.cost
                    if alt < dist[neighbor]:
                        dist[neighbor] = alt
        return dist

    def _assign_designated_ports_for_root_ports(self) -> None:
        for sw_name, switch in self.topology.switches.items():
            if switch.root_port is not None:
                other_side = self.topology.get_other_side(switch.root_port, sw_name)
                other_sw = self.topology.switches[other_side]
                if switch.root_port not in other_sw.designated_ports:
                    other_sw.designated_ports.append(switch.root_port)

    def _assign_designated_ports_for_naked_links(self) -> None:
        for link in self.topology.links:
            link_in_use_by = [
                sw.name
                for sw in self.topology.switches.values()
                if sw.root_port == link
            ]
            designated_by = [
                sw_name
                for sw_name, sw in self.topology.switches.items()
                if link in sw.designated_ports
            ]

            if not link_in_use_by and not designated_by:
                sw1 = self.topology.switches[link.switch1]
                sw2 = self.topology.switches[link.switch2]
                dist = self._calculate_distances_to_root(self.root_switch.name)
                sw1_cost = dist[sw1.name]
                sw2_cost = dist[sw2.name]
                if sw1_cost < sw2_cost:
                    sw1.designated_ports.append(link)
                elif sw2_cost < sw1_cost:
                    sw2.designated_ports.append(link)
                else:
                    if sw1.priority < sw2.priority:
                        sw1.designated_ports.append(link)
                    else:
                        sw2.designated_ports.append(link)

    def _block_remaining_ports(self) -> None:
        for sw in self.topology.switches.values():
            used_links = []
            if sw.root_port:
                used_links.append(sw.root_port)
            used_links.extend(sw.designated_ports)
            all_links_for_sw = self.topology.get_links_for_switch(sw.name)
            for link in all_links_for_sw:
                if link not in used_links:
                    sw.blocked_ports.append(link)

    def get_blocked_ports(self) -> List[Tuple[str, str]]:
        blocked_list = []
        for sw_name, switch in self.topology.switches.items():
            for link in switch.blocked_ports:
                other_side = self.topology.get_other_side(link, sw_name)
                blocked_list.append((sw_name, other_side))
        return blocked_list


def check_blocked_ports_match(
    actual_blocked: List[Tuple[str, str]], desired_blocked: List[Tuple[str, str]]
) -> bool:
    return actual_blocked == desired_blocked


def find_solution_with_cost_assignments(
    topo: Topology, desired_blocked: List[Tuple[str, str]]
) -> Optional[Dict[Tuple[str, str], int]]:
    link_keys = []
    for link in topo.links:
        key = tuple(sorted((link.switch1, link.switch2)))
        link_keys.append(key)
    link_keys = list(set(link_keys))

    for combo in itertools.product(COST_OPTIONS, repeat=len(link_keys)):
        cost_assignment = {}
        for i, key in enumerate(link_keys):
            cost_assignment[key] = combo[i]

        topo.set_link_costs(cost_assignment)

        stp = STPSimulator(topo)
        stp.run_stp()

        actual_blocked = stp.get_blocked_ports()
        if check_blocked_ports_match(actual_blocked, desired_blocked):
            return cost_assignment

    return None
