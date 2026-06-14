# Kafka System Design Deep Dive

*Notes from the "Kafka System Design Deep Dive w/ an Ex-Meta Staff Engineer" video by Hello Interview.*

## 1. What is Kafka?
At a high level, Apache Kafka is an **event streaming platform**. It is primarily used in two ways within system design:
1. As a **Message Queue**
2. As a **Stream Processing System**

## 2. Core Concepts & Terminology (The Motivating Example)
Imagine a live sports website tracking events (goals, substitutions). 

* **Producer:** The server or process that places events onto the queue (e.g., a person logging a goal at a match).
* **Consumer:** The server that reads events off the queue and updates the website.
* **Partition (The Queue):** An ordered, immutable sequence of messages on disk (an append-only log file). This is how data scales.
* **Topic:** A logical grouping of partitions. (e.g., a `soccer` topic vs. a `basketball` topic).
* **Consumer Group:** A grouping of consumers. Each event in a partition is guaranteed to only be processed by **one** consumer within a given consumer group, preventing duplicate processing when horizontally scaling consumers.
* **Broker:** A single server within a Kafka cluster that is responsible for holding the partitions.

### Topic vs. Partition
* A **Topic** is a logical grouping that exists in code (how you organize data).
* A **Partition** is a physical grouping that exists on disk (how you scale data).

## 3. The Lifecycle of a Message (Under the Hood)
A message (or "record") in Kafka consists of:
1. **Key** (Optional, determines partitioning)
2. **Value** (The actual data payload)
3. **Timestamp** (For ordering)
4. **Headers** (Key-value metadata)

### The Write Path (Producer)
1. Producer publishes a message.
2. **Routing:** If a Key is provided, Kafka hashes the key (using MurmurHash) and takes the modulo over the number of partitions. This ensures messages with the same key always go to the same partition (guaranteeing order for that key). If no Key is provided, messages are distributed via Round Robin.
3. The cluster looks up which Broker holds that partition and appends the message to the append-only log on disk.
4. Each message gets a sequential ID called an **Offset** (0, 1, 2, 3...).

### The Read Path (Consumer)
1. Consumers specify which Topic to read from.
2. They keep track of their local **Offset** (the last message they successfully read).
3. Periodically, consumers commit their offset back to Kafka. If a consumer crashes, it uses this committed offset to pick up exactly where it left off.

### Replication
To ensure high availability and durability, partitions have replicas:
* **Leader Replica:** Handles all read and write requests for that partition.
* **Follower Replicas:** Passively replicate data from the leader to serve as backups.

## 4. When to Use Kafka in an Interview
### A. As a Message Queue
* **Asynchronous Processing:** e.g., YouTube video uploading. User uploads a video (synchronous fast response), then the video ID and S3 URL are put on Kafka for a transcoder to process into 480p, 720p, etc., in the background.
* **In-Order Processing:** e.g., Ticketmaster waiting queues. You place users in a Kafka queue to guarantee they are processed in the exact order they arrived.
* **Decoupling Producer and Consumer:** e.g., Leetcode code execution. If 100,000 users submit code at once, scale the web servers to handle requests and push them to Kafka. The expensive code-execution worker nodes can read from Kafka at their own pace without needing to be massively scaled.

### B. As a Stream
* **Real-time Data Processing:** e.g., Ad click aggregation. A continuous, massive stream of clicks is pushed to Kafka and consumed rapidly by a tool like Flink to update advertiser dashboards in real-time.
* **Pub/Sub (Multiple Consumers):** e.g., Facebook Live comments. One comment is published to a stream, and multiple consumer services connected to viewing clients pull the same comment simultaneously.

## 5. System Design Deep Dive Follow-Ups

### A. Scalability
* **Message Size Limit:** Highly advised to keep messages **under 1 MB**. *Anti-pattern:* Putting a video blob on Kafka. *Correct pattern:* Store the video in S3, and put the short S3 URL on Kafka.
* **Broker Limits:** A good hardware baseline estimate is that one broker can store ~1 TB of data and handle ~10,000 messages per second.
* **Handling Hot Partitions:** If you partition by `ad_id` and a specific ad goes viral, one partition gets overwhelmed.
    1. *Remove Key:* Distribute randomly (if ordering doesn't matter).
    2. *Compound Key:* Append a random number (e.g., `ad_id:random(1-10)`) to split the hot key across multiple partitions.

### B. Fault Tolerance & Durability
* **`acks` Configuration:** * `acks=all`: Max durability. The leader waits for all followers to acknowledge receipt before confirming to the producer.
    * `acks=1` or `acks=0`: Faster performance, but risks data loss if the leader crashes before replication.
* **`replication.factor`**: Typically defaults to 3.
* **Consumer Commit Timing:** Crucial rule—only commit the consumer offset *after* the logical work is fully completed (e.g., parsed HTML is saved to DB). If you commit early and crash, the message is effectively lost.

### C. Errors & Retries
* **Producer Retries:** Configured via the producer SDK. Be sure to enable the **idempotent producer** setting so that network retries don't result in duplicate messages on the queue.
* **Consumer Retries:** Kafka does *not* support native consumer retries (unlike AWS SQS). 
    * *Standard Pattern:* If a message fails, push it to a dedicated **Retry Topic**. After $N$ failed retries, push it to a **Dead Letter Queue (DLQ) Topic** for human/manual debugging.

### D. Performance Optimization (Throughput)
* **Batching:** Producers can configure `batch.size` and `linger.ms` to group messages together, sending fewer network requests.
* **Compression:** Producers can compress messages (e.g., using `gzip`) before sending, saving network bandwidth.
* **Keys:** Optimizing your partition key to ensure perfectly even distribution across the cluster is the #1 way to increase parallel throughput.

### E. Retention Policies
Dictates how long messages stay on disk before being purged. Handled per-topic.
* **`retention.ms`:** Default is 7 days.
* **`retention.bytes`:** Default is 1 GB per partition.
* Whichever limit is hit first triggers deletion. Storing messages longer requires scaling disk space and impacts cost.