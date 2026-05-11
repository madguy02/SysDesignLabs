
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