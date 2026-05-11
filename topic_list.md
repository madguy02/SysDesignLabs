
# Comprehensive System Design Interview Study Guide

This guide covers core fundamentals, advanced distributed systems concepts, and real-world architecture problems frequently asked in technical interviews at top-tier companies (FAANG/MAANG).

---

## 1. Foundational Concepts
* **Scalability**: Vertical vs. Horizontal scaling.
* **Availability**: High availability, SLAs, SLOs, SLIs.
* **Reliability vs. Fault Tolerance**: Redundancy, failover, and self-healing.
* **Performance vs. Latency vs. Throughput**.
* **CAP Theorem**: Consistency, Availability, Partition Tolerance (and the PACELC extension).
* **Consistency Models**: Strong, Eventual, Causal, Read-your-writes, and Monotonic reads.

## 2. Networking & Communication
* **OSI Model**: Deep dive into Layer 4 (TCP/UDP) and Layer 7 (HTTP/HTTPS).
* **Communication Protocols**:
    * REST vs. RPC (gRPC, Thrift).
    * WebSockets vs. Long Polling vs. Server-Sent Events (SSE).
    * QUIC and HTTP/3.
* **Load Balancing**:
    * Algorithms (Round Robin, Least Connections, Weighted).
    * Layer 4 vs. Layer 7 Load Balancers.
    * Consistent Hashing (Mechanism and Virtual Nodes).
* **DNS**: How it works, Anycast routing, and GeoDNS.
* **CDN (Content Delivery Network)**: Push vs. Pull models, Edge computing.

## 3. Data Storage & Management
* **Database Types**:
    * Relational (SQL) vs. Non-relational (NoSQL - Key-Value, Document, Columnar, Graph).
    * NewSQL (e.g., CockroachDB, Spanner).
* **Scaling Databases**:
    * Replication (Leader-Follower, Multi-Leader, Leaderless).
    * Partitioning/Sharding (Horizontal vs. Vertical, Sharding keys).
* **Storage Internals**:
    * B-Trees vs. LSM-Trees.
    * Write-Ahead Log (WAL).
    * Indexes (Clustered vs. Non-clustered).
* **Transactions**: ACID properties, 2PC (Two-Phase Commit), Sagas pattern.

## 4. Caching
* **Caching Levels**: Client, CDN, Load Balancer, Application, Distributed (Redis, Memcached).
* **Strategies**: Write-through, Write-around, Write-back, Refresh-ahead.
* **Eviction Policies**: LRU, LFU, FIFO, RR.
* **Cache Invalidation**: TTL, Stampede prevention, Thundering Herd problem.

## 5. Distributed Messaging & Event-Driven Architecture
* **Message Queues**: RabbitMQ, Kafka, ActiveMQ.
* **Pub/Sub Model**: Topics, Partitions, Consumer Groups.
* **Message Semantics**: At-least-once, At-most-once, Exactly-once processing.
* **Backpressure** and Rate Limiting strategies (Token Bucket, Leaky Bucket).

## 6. Advanced Distributed Systems
* **Consensus Algorithms**: Paxos, Raft.
* **Leader Election**: Bully algorithm, Zookeeper-based election.
* **Distributed IDs**: Snowflake ID, UUID, Database Auto-increment.
* **Gossip Protocols**: Peer-to-peer membership and failure detection.
* **Quorum**: Quorum reads/writes (N, W, R).

## 7. Observability & Security
* **Observability**: Metrics, Logging, Distributed Tracing (Jaeger, Zipkin).
* **Security**: OAuth2, OIDC, JWT, mTLS, Rate Limiting, DDoS protection.

## 8. Common Interview Design Problems
* **Social & Communication**: Messenger/WhatsApp, Twitter/X Newsfeed, Instagram.
* **Storage & Search**: Google Drive/Dropbox, Web Crawler, Typeahead/Autocomplete.
* **Marketplaces & Logistics**: Uber/Lyft (Proximity service), Amazon (E-commerce), Airbnb.
* **Streaming & Content**: Netflix/YouTube (Video streaming), Spotify (Audio).
* **Infrastructure**: Rate Limiter, API Gateway, Distributed Job Scheduler, Distributed Cache.

---
*Generated for GitHub Repository Upload*