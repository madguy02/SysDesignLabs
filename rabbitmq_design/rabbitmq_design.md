# System Design: Distributed Message Broker (Like RabbitMQ)

This document outlines the end-to-end system design for a distributed message queue/broker similar to RabbitMQ. It follows a structured approach: Functional and Non-Functional Requirements, Back-of-the-envelope calculations, High-Level Design, and an Architectural Deep Dive.

---

## 1. Introduction

A distributed message broker enables asynchronous communication between decoupled services. It acts as a middleman that receives messages from **Producers** and routes them to **Consumers**. Unlike log-based brokers (like Apache Kafka) which act as immutable event streams, RabbitMQ is traditionally an **Advanced Message Queuing Protocol (AMQP)** broker. It excels at complex routing, per-message acknowledgments, and push-based delivery.

### Key Terminologies:
* **Producer:** Applications that send messages to the broker.
* **Consumer:** Applications that read/receive messages from the broker.
* **Exchange:** The routing entity that receives messages from producers and distributes them to queues based on rules (bindings).
* **Queue:** A buffer that stores messages until they are safely consumed.
* **Binding:** A link between a queue and an exchange.

---

## 2. Requirements Gathering

### Functional Requirements
* **Publish:** Producers should be able to send messages to the broker.
* **Consume:** Consumers should be able to receive messages from the broker.
* **Routing:** The system must support flexible routing (Direct, Fanout, Topic, Headers).
* **Acknowledgments:** The system must support message acknowledgments (ACK/NACK). If a consumer fails to process a message, it should be redelivered.
* **Message Durability:** Messages can be marked as transient (in-memory) or persistent (written to disk).
* **Dead Lettering:** Messages that repeatedly fail processing or expire should be routed to a Dead Letter Queue (DLQ).

### Non-Functional Requirements
* **High Availability (HA):** The broker must survive node failures without data loss.
* **Low Latency:** Message routing and delivery should happen in sub-milliseconds for transient messages.
* **Scalability:** The system must handle an increasing number of queues, connections, and message throughput.
* **Fault Tolerance:** Guaranteed at-least-once delivery for persistent messages.
* **Reliability:** Strict ordering within a single queue (FIFO).

---

## 3. Back-of-the-Envelope Estimation

Let's design for a moderately high-scale enterprise deployment.

**Assumptions:**
* **Message Throughput:** 10,000 messages published per second.
* **Read/Write Ratio:** 1:2 (Assuming average fanout where 1 message is copied to 2 queues).
    * Write IOPS: 10,000 writes/sec.
    * Read IOPS: 20,000 reads/sec.
* **Average Message Size:** 2 KB.
* **Retention Period:** Unlike Kafka (which keeps messages for days), RabbitMQ usually deletes messages once acknowledged. We'll assume a backlog of up to 1 day due to consumer outages.

**Bandwidth Calculations:**
* **Ingress Network:** $10,000 \text{ msgs/sec} \times 2 \text{ KB} = 20 \text{ MB/sec}$.
* **Egress Network:** $20,000 \text{ msgs/sec} \times 2 \text{ KB} = 40 \text{ MB/sec}$.

**Storage Calculations:**
* **Daily Message Volume:** $10,000 \text{ msgs/sec} \times 86,400 \text{ seconds} \approx 864 \text{ million messages/day}$.
* **Disk Storage for 1 day of Backlog:** $864,000,000 \times 2 \text{ KB} \approx 1.7 \text{ TB}$.
* *(Note: Fast SSDs are recommended to handle the high IOPS for persistent queues).*

---

## 4. High-Level System Design

The architecture is divided into the networking layer, the routing layer, and the storage layer.

### System Components:

1.  **Connection Manager:** Handles millions of persistent TCP connections from producers and consumers. Multiplexes logical channels over single TCP connections (AMQP Channels).
2.  **Exchange/Router:** The stateless routing engine. Evaluates the routing key of incoming messages and duplicates/forwards them to bound queues.
3.  **Metadata Store (Distributed Consensus):** Stores queue configurations, exchange topologies, bindings, and user permissions. Uses a consensus algorithm (like Raft) to ensure configuration consistency across the cluster.
4.  **Queue Manager & Storage Engine:** Manages the actual queues. Handles keeping messages in memory for fast access and writing them to disk (Append-Only Files) for durability.
5.  **State Machine / HA Manager:** Replicates queue data across multiple nodes to ensure high availability.

### High-Level Flow:

1.  **Publish Flow:** Producer opens a TCP connection -> creates a Channel -> sends Message to an Exchange. The Exchange looks up Bindings in the Metadata Store and pushes the message to appropriate Queue(s).
2.  **Consume Flow:** Consumer opens connection/channel -> subscribes to a Queue. The Queue Manager **pushes** messages to the consumer up to a configured "Prefetch" limit. 
3.  **ACK Flow:** Consumer processes the message -> sends an ACK back to the broker. The Queue Manager deletes the message from memory/disk.

---

## 5. Architectural Deep Dive

### 5.1 Push vs. Pull Model
Unlike Kafka (pull-based), RabbitMQ uses a **Push Model**. The broker proactively sends messages to connected consumers. 
* *Problem:* A fast producer could overwhelm a slow consumer.
* *Solution:* **Prefetch Count**. The broker only pushes a specific number of unacknowledged messages (e.g., 50) to a consumer. It stops pushing until the consumer sends ACKs, creating natural backpressure.

### 5.2 Storage Engine & Memory Management
RabbitMQ optimizes for "empty queues are fast queues."
* **Transient Messages:** Stored only in RAM. If RAM fills up (hitting the memory watermark), the broker starts paging them out to disk to prevent OOM errors, causing a severe drop in performance.
* **Persistent Messages:** Appended to a commit log on disk immediately AND kept in RAM for fast delivery.
* **Garbage Collection:** As messages are ACKed, they are marked as deleted. Compaction runs periodically to merge disk segments and reclaim space.

### 5.3 Exchanges and Routing Topologies
The separation of Exchanges and Queues allows for complex topologies:
1.  **Direct Exchange:** Exact match on the `routing_key`. (e.g., `payment.success` -> Payment Queue).
2.  **Topic Exchange:** Wildcard matching. (e.g., `logs.*.error` matches `logs.auth.error` and `logs.db.error`).
3.  **Fanout Exchange:** Ignores routing keys and broadcasts the message to ALL bound queues (Pub/Sub pattern).
4.  **Headers Exchange:** Routes based on message header attributes instead of the routing key.

### 5.4 High Availability & Replication (Quorum Queues)
In modern distributed brokers, queues must survive node failures.
* **Classic Mirrored Queues (Deprecated):** Mirrored messages across nodes. Suffered from network partition issues ("split-brain").
* **Quorum Queues (Modern Approach):** Based on the **Raft Consensus Algorithm**. 
    * A cluster of nodes (e.g., 3, 5, or 7 nodes).
    * One node acts as the **Leader** for a specific queue, handling all writes and reads.
    * Follower nodes passively replicate the Write-Ahead Log (WAL).
    * A message is only confirmed to the producer when a **quorum** (majority) of nodes have written it to disk.
    * If the Leader node crashes, an election takes place, and a Follower becomes the new Leader seamlessly.

### 5.5 Handling Message Failures
* **Time-To-Live (TTL):** Messages can have an expiration time. If not consumed within the TTL, they are discarded.
* **Dead Letter Exchanges (DLX):** If a message expires, is explicitly rejected (NACK with `requeue=false`), or a queue reaches its length limit, the message is routed to a DLX. From there, it is routed to a Dead Letter Queue where engineers can inspect why it failed.

### 5.6 Scalability Challenges
* A single queue in RabbitMQ (even if replicated) is bound by the throughput of the Leader node. You cannot split a single queue across multiple servers.
* **Solution:** To scale beyond a single node's capacity, you must manually partition/shard your data by creating multiple queues (e.g., `orders_01`, `orders_02`, `orders_03`) and routing messages using a Consistent Hashing Exchange plugin.

---

## 6. Conclusion & Trade-offs (RabbitMQ vs Kafka)

When designing this system, it's vital to understand why you would choose this AMQP architecture over a log-based one like Kafka.

* **Smart Broker / Dumb Consumer (RabbitMQ):** The broker does the heavy lifting (routing, tracking ACKs per message, managing DLQs). Great for complex business logic, microservices communication, and task queues (e.g., Celery).
* **Dumb Broker / Smart Consumer (Kafka):** The broker just appends bytes to a log. The consumer tracks its own offset. Great for massive data pipelines, event sourcing, and streaming analytics (millions of messages/sec).

In summary, this design prioritizes **flexibility, complex routing, and precise, per-message delivery guarantees** over raw append-only throughput.