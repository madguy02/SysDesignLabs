
# 🕸️ Subnets, NAT, and CIDR Mastery

## 1. Subnets (Logical Isolation)
A subnet is a partition of an IP network that improves efficiency and security.

*   **Broadcast Control:** Prevents "noise" from one department (e.g., Guest Wi-Fi) from slowing down another (e.g., Database).
*   **Security (Public vs. Private):** sensitive data (Patient Records) stays in Private Subnets with no Public IPs, while Load Balancers stay in Public Subnets.

## 2. NAT (Network Address Translation)
NAT allows multiple devices with **Private IPs** to share a single **Public IP** to access the internet.

*   **NAT Gateway:** Lives in the **Public Subnet**. It translates internal requests so private servers can download updates without being exposed to inbound attacks.
*   **Port Exhaustion:** A Staff-level concern where a NAT runs out of the 65k available ports due to high-volume microservice traffic.

## 3. CIDR Notation (Sizing the Room)
CIDR determines how many IPs are available in a subnet. The formula is $2^{(32 - n)}$, where $n$ is the CIDR number.

| CIDR | Host Bits | Total IPs | Usable IPs | Subnet Mask |
| :--- | :--- | :--- | :--- | :--- |
| **/32** | 0 | 1 | 1 | 255.255.255.255 |
| **/26** | 6 | 64 | 62 | 255.255.255.192 |
| **/24** | 8 | 256 | 254 | 255.255.255.0 |
| **/16** | 16 | 65,536 | 65,534 | 255.255.0.0 |

> **Staff Tip:** Always subtract 2 from the total IPs to account for the **Network Address** (the first IP) and the **Broadcast Address** (the last IP).