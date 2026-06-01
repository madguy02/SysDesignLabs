## Consistency

1. Strong Consistency (The "Checkout" Button)To ensure no double-spending or overselling of inventory, you must use a system that supports Distributed Transactions or Strict Quorums.Implementation: Use a relational database like PostgreSQL or a distributed SQL database like CockroachDB.The Mechanism: Use Synchronous Replication. When the "Checkout" service writes to the database, it waits for a majority quorum ($W=Quorum$) and uses Strict Serializability.Code Level: Wrap the operation in a database transaction (BEGIN...COMMIT). If the database cannot achieve a quorum because of a network partition, the checkout fails—preserving the integrity of the ledger.

2. Read-Your-Writes (The "User Settings" Page)
This doesn't require global strong consistency, but it does require that the Session feels consistent to the individual user.

Implementation: Use a Distributed Cache (Redis) or Sticky Sessions at the Load Balancer (ALB/NGINX).

The Mechanism: * Option A (The Header Trick): When the user saves their settings, the backend returns a version_id or timestamp. The client includes this in the next GET request. The backend ensures it reads from a node that is at least at that version.

Option B (Primary Read): Force all "User Settings" reads to go to the Primary Node of the database, while other traffic goes to Read Replicas. This guarantees the user sees their own update immediately.

Trade-off: You sacrifice some read scalability on the primary node to give the user a seamless experience.

3. Eventual Consistency (The "Recommended Products" Sidebar)This is "fire and forget." It prioritizes low latency and high availability.Implementation: Use a NoSQL database (Cassandra/DynamoDB) or Asynchronous Read Replicas.The Mechanism: Use Asynchronous Replication. When the "Recommendations" engine updates, it writes to its local node and returns a success immediately. The update propagates to global replicas in the background.Code Level: Use a "Weak Read" ($R=1$). If the sidebar shows a product that was actually removed 2 seconds ago, the impact is negligible—the user just gets a "Product Unavailable" message if they happen to click it.