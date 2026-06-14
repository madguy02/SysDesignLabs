# Distributed Rate Limiter System Design Notes

### Introduction and Scope
The video focuses on designing a request-level rate limiter tailored for a social media platform's API. 
* **Target Scope**: The goal is limiting individual HTTP requests (e.g., fetching timelines, posting tweets, or uploading photos) rather than handling higher-level business operations. 
* **Placement**: A server-side implementation is chosen. While client-side rate limiting can be complementary, server-side control is absolutely essential for system protection and security because clients cannot be trusted to self-regulate.

---

### System Requirements

**Core System Requirements**
* **Low Latency**: The system must introduce minimal overhead, strictly keeping latency below 10ms per request check.
* **High Availability**: The architecture must be highly available. Eventual consistency is perfectly acceptable here, as minor delays in enforcing limits across distributed nodes are a worthwhile tradeoff.
* **Massive Scale**: The rate limiter must be capable of handling 1 million requests per second (RPS) across an estimated 100 million daily active users (DAU).

**Out of Scope (Below the Line)**
To keep the design focused, the following are explicitly excluded:
* Long-term persistence of rate-limiting data.
* Complex analytics or intensive querying on the rate limit data.

---

### Core Entities & API Interface
* **System Interface**: The rate limiter is framed as a core infrastructure component. Other backend microservices call it to verify if an incoming request should be permitted or blocked before processing.
* **HTTP Response Headers**: When rate limits are actively tracked or enforced, the API should return industry-standard headers to inform the client:
    * **`X-RateLimit-Limit`**: The absolute rate limit ceiling for that specific request (e.g., "100").
    * **`X-RateLimit-Remaining`**: The number of allowed requests left in the current time window (e.g., "0").
    * **`X-RateLimit-Reset`**: A Unix timestamp indicating the exact time the user's rate limit window resets (e.g., "1640995200").

---

### Deep Dive: Addressing Core Distributed Challenges

**1. Dealing with Contention (Race Conditions)**
* **The Challenge**: Distributed counters are notoriously prone to race conditions. When multiple threads or concurrent processes attempt to update the same user's resource simultaneously, it leads to lost updates—even if the individual operations themselves are atomic.
* **The Solution**: You must expand the "atomic boundary". Instead of isolating reads and writes, the entire *read-modify-write* sequence needs to be bundled into a single atomic operation to ensure requests are counted perfectly.

**2. Scaling Writes**
* **The Challenge**: At a scale of 1M RPS, the system faces severe write-scaling bottlenecks, requiring millions of individual counter updates every single second.
* **The Solution**: Distribute the load utilizing **Redis Shards**. Every rate limit check triggers an atomic read-modify-write operation that securely updates token buckets or request counters stored across horizontally scaled distributed Redis shards.

---
*Source: [Ex-Meta Staff Engineer breaks down Distributed Rate Limiter System Design](https://www.youtube.com/watch?v=MIJFyUPG4Z4)*


## 4 Core Rate Limiting Algorithms

When designing a rate limiter, you typically choose from one of four foundational algorithms. Each has its own tradeoffs regarding memory usage, burst handling, and implementation complexity.

### 1. Token Bucket
* **How it works:** Imagine a bucket with a maximum capacity of tokens. Tokens are deposited into the bucket at a constant rate. Every incoming request must consume one token to be processed. If the bucket is empty, the request is dropped (HTTP 429 Too Many Requests).
* **Pros:** Highly memory-efficient and allows for bursts of traffic (as long as tokens are available). It's the industry standard used by companies like Amazon and Stripe.
* **Cons:** Tuning the two parameters (bucket capacity and token refill rate) can be challenging depending on the traffic pattern.

### 2. Leaky Bucket
* **How it works:** Similar to a water bucket with a hole in the bottom. Requests are added to the bucket (usually a FIFO queue). The system processes requests at a strict, constant outbound rate. If the bucket (queue) fills up, new incoming requests are dropped.
* **Pros:** Excellent for use cases that require a perfectly smooth, predictable outbound traffic rate.
* **Cons:** Cannot handle bursts well. A sudden spike in legitimate traffic fills up the queue, potentially causing newer requests to be dropped while older ones are processed slowly.

### 3. Fixed Window Counter
* **How it works:** Time is divided into fixed, discrete windows (e.g., 10:00 to 10:01). A counter increments for every request within that window. Once the threshold is reached, subsequent requests are dropped until the next window starts and the counter resets.
* **Pros:** Extremely simple to implement and uses very little memory.
* **Cons:** The "Edge Effect" problem. A burst of traffic occurring exactly at the boundary of two windows (e.g., at 10:00:59 and 10:01:01) can theoretically allow double the intended rate limit to pass through in a very short time span.

### 4. Sliding Window (Log or Counter)
* **How it works:** Solves the edge effect of the Fixed Window by evaluating a continuous rolling timeframe. 
    * *Sliding Window Log:* Keeps a log of exact timestamps for every request (often in Redis sorted sets). Accurate but memory-intensive.
    * *Sliding Window Counter:* A hybrid approach that takes the request count from the previous fixed window and weights it based on the overlap with the current rolling window. 
* **Pros:** Smooths out traffic spikes seamlessly and provides a highly accurate rate limit without the edge vulnerabilities.
* **Cons:** The Log version is generally too memory-heavy for high-scale systems. The Counter version is highly optimized but involves more complex math and logic to implement.