> [!NOTE]  
> This program assumes you are using Packet Tracer 8.X where you have access to the `span cost` command. 

# What Is This?
A small program to help you do Comp. Networks Lab 4. The program runs a simplified STP simulation and brute forces a bunch of costs until it stumbles upon the desired blocked ports configuration. Despite using a naive brute force approach, this program should run pretty fast actually since we're only trying 3 different possible costs (4,16,32).

# How to Use?
1. Make sure you have Python 3.XX installed.
2. Download input.txt, main.py, and stp_simulation.py
3. Configure input.txt to match your topology (i've already configured it for term 2430's lab test)
4. Configure the blocked ports in input.txt to match your question. The order matters here. "S6 (blocked) -> S4" means the port connected to S6 is blocked.

> [!NOTE]  
> The numbering of the switches in the PDF starts from 1. However, the numbering starts from 0 in Packet Tracer. I've decided to start from 0 instead of 1 because then you won't have to do much mental gymnastics when configuring. Just keep in mind that if S6->S4 is blocked in the PDF, you must type "S5 (blocked) -> S3" in input.txt.

5. Run main.py
6. You will be prompted to select the root bridge. If you leave this blank, it will follow the switch with the lowest number (S0). Use this for questions where the root bridge is S2 or something.

## It couldn't find a solution
If you're 100% sure you typed in the topology and blocked ports correctly, then it's almost certain that the blocked port configuration is impossible.

## It found a solution!
Great. Notice that the program gives you priorities as well as costs. You **must** configure each switch to follow the priorities listed. After you're done with that, you may configure the costs. Note that `cost=4` is the default cost for a link in term 2430's topology. So, if everything is `cost=4` but one is `cost=16` then you only have to change the cost of that one link to 16.

> [!NOTE]  
> The script runs a simplified STP where link costs are symmetrical. However, this is not the case for real STP where the link costs are applied per switch. Therefore, if the script says the cost of S4 <-> S6 should be 32, you may need to try setting the cost for S4 and S6. As a general heuristic, **apply the cost to the switch *with* the blocked port.**

# Example
![image](https://github.com/user-attachments/assets/8e45b41b-7b2e-433e-9390-2d795aa027fa)

The corresponding `input.txt` for this configuration would be:
```
Topology:
S0 -> S1
S0 -> S2
S1 -> S2
S1 -> S3
S2 -> S4
S3 -> S4
S3 -> S5
S4 -> S6
S5 -> S6

Desired Blocked Ports:
S1 (blocked) -> S2
S1 (blocked) -> S3
S3 (blocked) -> S5
```

# Useful Commands
Here are some commands that may help you.

`en -> conf t -> span vlan 1 prio {PRIORITY}` - for configuring priority

`en -> conf t -> int {PORT_NUM} -> span cost {COST}` - for setting the costs
