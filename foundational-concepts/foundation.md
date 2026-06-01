
# CAP & PACELC

## What is CAP:
    CAP stands for Consistency, Availability and Partition.
    During a Partition you must choose either consistency or Availablity.

    The partition that we are talking about is not done on purpose, it happens to us.
    Lets say, a service A and service B both are up, but Service A can't communicate with Service B. Hence it fails.
    Or an availability zone goes dark due to power loss, at this point in time we will have to choose from CAP. Partition is a trigger here

    Scenario: A user wants to update their password.
    If you choose Consistency (CP): The system sees that Node A and Node B can't sync. It tells the user: "Error: System unavailable." You refuse to update the password because you can't guarantee both nodes will have the same one.

    If you choose Availability (AP): The system allows the update on Node A. It tells the user: "Success!" Even though Node B still has the old password. You prioritize the user's ability to use the app over perfect data symmetry.

    ** Consistency: Deny request to ensure no stale data is read. (CP)
    ** Availability: Serve stale data to ensure systems are up, and as the sync is done, start serving new data.

    The "Post-Partition" Phase: Reconciliation
      Once the network cable is plugged back in and the partition ends, the system must "heal."

      In CP systems: This is easy, as no data was changed during the split.

      In AP systems: This is hard. You now have "conflicting" data. Node A says the password is "Red," and Node B says it's "Blue." You must use a Conflict Resolution strategy, such as:

      Last Write Wins (LWW): Use the timestamp.

      Vector Clocks: A more complex way of tracking the history of changes.

      CRDTs (Conflict-free Replicated Data Types): Math-based data structures that automatically merge.


## What is PACELC:
    
    Partitioned...
    Availability or Consistency; 
    Else (normally)...
    Latency or Consistency.

    CAP is for catastrophic failure situations, but for the rest 99.9% of the time, we adhere to PACELC

    PACELC happens all the time. It splits your system's life into two phases:

    Phase 1: The "P" (Partition) — Same as CAP
    When: The network is broken.
    The Choice: Do you stay online but serve old data (PA), or do you shut down to stay accurate (PC)?

    Phase 2: The "E" (Else / Normal Operation) — The New Part
    When: The network is healthy. No wires are cut. Everything is fine.
    The Choice: Even when things are working, you have a speed limit (the speed of light). You must choose:
 
    Latency (L): Send the data to one node and tell the user "Done!" immediately. Let the other nodes sync later in the background. (High speed, lower consistency).

    Consistency (C): Make the user wait until every single node confirms they have the data. (Low speed, perfect consistency).


## Quorums:

 Quorum is the mechanical dial that a Staff Engineer turns to actually implement the theoretical choices of PACELC. While PACELC describes the strategy, Quorum is the execution.To understand the connection, think of PACELC as the policy and Quorum ($N, W, R$) as the configuration settings.

 1. Connecting to the "P" (Partition)PACELC says: Partitioned, Availability or Consistency.
 The Quorum math ($W + R > N$) dictates what happens when nodes disappear.If you choose a Majority Quorum ($W=2, R=2$ for $N=3$): You have chosen Consistency (PC). 
 If two nodes can't talk to each other, the one left alone cannot reach a majority. It will stop accepting requests to prevent data divergence.If you choose $W=1, R=1$: You have chosen Availability (PA). Even if a node is completely isolated from the rest of the cluster, it will keep accepting writes and serving reads.

 2. Connecting to the "E" (Else / Normal Operation)This is where Quorum shines. PACELC says: Else, Latency or Consistency.The "L" (Latency) Choice
 If you want low latency (EL), you reduce the number of nodes you wait for.Configuration: $W=1$.Connection: As soon as the local node saves the data, it tells the user "Success!" and replicates to others in the background. The user experiences almost zero network latency beyond the first hop.

 The "C" (Consistency) ChoiceIf you want strict consistency (EC), you increase the requirement.Configuration: $W=All$ (or $W=Quorum$).Connection: The user must wait until the data is safely stored on multiple disks across the network. The Latency is higher (it’s limited by the slowest node in the quorum), but the Consistency is perfect.

 All in All:

 The PACELC-Quorum Bridge:
 PACELC defines the SLA (Service Level Agreement).
 Quorum defines the N-W-R math to meet that SLA.
 To achieve Consistency (C) in either state, you must ensure $W + R > N$.To achieve Latency (L) or Availability (A), you intentionally break that inequality (e.g., $W=1$).

 ## What is Latency

 Latency is the time it takes for a single unit of data to travel from point A to point B. It is a measurement of delay.

 Metric: Time (ms, seconds).

 If you send a message from Tezpur to a server in Mumbai, and it takes 40ms to get a response, your latency is 40ms.

 Focus: Individual user experience. High latency makes an app feel "laggy."

 ## What is throughput
 Throughput is the amount of data or the number of requests a system can process in a given period of time.

 Metric: Requests Per Second (RPS), Bits per second (bps), or Transactions Per Second (TPS).

 Example: Imagine a highway. Latency is how fast one car can drive from one end to the other. Throughput is how many cars can pass through the toll booth every hour.

 Focus: System capacity. High throughput means the system can handle many users simultaneously.

 ## What is performance
 Performance is a broad, qualitative term that encompasses both Latency and Throughput, along with Resource Utilization (CPU, RAM).

 The Relationship: A system has "good performance" if it maintains low latency while handling high throughput without exhausting its resources.

 The Staff Perspective: You don't just ask "Is it fast?" You ask "How does the latency scale as throughput increases?"

 ## The Inverse Relationship
 In distributed systems, these three often fight each other. This is known as the Saturation Point.

 Low Load: Throughput is low, and Latency is at its minimum (the "speed of light" limit).

 Increasing Load: As you add more users (increasing Throughput), Latency stays stable for a while.

 The Knee (Saturation): Once the CPU or Disk reaches its limit, Throughput plateaus. Any additional requests have to wait in a "queue."

 High Load: Throughput stays flat, but Latency spikes exponentially because requests are sitting in line for a long time.

 ## Reliability and Fault tolerance

 1. The Core Definition
   Reliability: The probability that a system will perform its intended function without failure for a specified period of time. It is measured by MTBF (Mean Time Between Failures).

   Fault Tolerance: The ability of a system to continue operating properly in the event of the failure of one or more of its components.

   The Difference: A reliable system might rarely break, but when it does, it goes down. A fault-tolerant system is designed to "keep the lights on" even when parts of it are literally on fire.

 2. Redundancy (The "Backup" Strategy)Redundancy is the practice of including extra components that are not strictly necessary for the system to function but are there to take over if something fails.Active-Passive (Warm/Cold): A standby server waits for the primary to fail. There is a "switch-over" time where the system is briefly unavailable.Active-Active (Hot): All nodes handle traffic simultaneously. If one fails, the load balancer simply stops sending traffic to it. This is superior for Availability.N+1 Redundancy: If your system needs 3 nodes to handle peak load, you deploy 4 ($N+1$). This allows you to lose any single node without impacting performance.

 3. Failover (The "Hand-off" Process)
   Failover is the automatic switching to a redundant or standby computer server, system, hardware component, or network upon the failure or abnormal termination of the previously active application.

   Health Checks: The "Watchman." A load balancer or service mesh constantly pings an endpoint (e.g., /health). If the service doesn't respond with a 200 OK within 2 seconds, it is marked as "Unhealthy."

   VIP (Virtual IP) Swapping: In traditional networking, the IP address itself is moved from a dead server to a living one.

   DNS Failover: Updating DNS records to point to a different region. (Note: This is slow due to TTL/Caching issues).


 4. Self-Healing
   Self-healing goes beyond just "switching to a backup." It is a system's ability to detect, diagnose, and fix its own issues without human intervention.

   Auto-Scaling Groups (ASG): If a node crashes, the infrastructure (like AWS EC2 or Kubernetes) detects the missing heartbeat and automatically spins up a brand-new instance to replace it.

  Circuit Breakers: If a downstream service (like a payment gateway) is failing, the "Circuit Breaker" trips. Instead of letting the whole app hang, it returns a cached response or an error instantly. This prevents Cascading Failures.

  Restart Strategies: In Kubernetes, a pod that is "OOMKilled" (Out of Memory) is automatically restarted with a clean slate.