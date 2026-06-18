# System Design Document: Massive-Scale Push Notification Service

## 1. Problem Statement & Scope
This document outlines the architecture for a robust, highly available push notification system capable of serving 20 million Daily Active Users (DAU). 

**Key Responsibilities:**
* Accept internal notification triggers (promotional, transactional, system alerts).
* Resolve a logical `user_id` to a physical device.
* Deliver the payload to Apple Push Notification Service (APNS) and Firebase Cloud Messaging (FCM).
* Ensure idempotency (no duplicate deliveries).
* Protect downstream systems from traffic spikes caused by mass marketing blasts.

---

## 2. Capacity & Scale Assumptions
* **Users:** 20 Million DAU.
* **Daily Volume:** 200 Million notifications (~10 per user).
* **Throughput:** * Average QPS: ~2,500 requests/sec.
    * Peak QPS (Spikes/Promos): ~25,000 requests/sec.
* **Storage (Device Registry):** 20M users * ~250 bytes per record = ~5 GB (easily fits in memory/cache).
* **Storage (Logs):** 200M logs/day * 1 KB = 200 GB/day.

---

## 3. Core Architecture: End-to-End Flow

The architecture is strictly decoupled using an event-driven pub/sub model to survive massive traffic spikes.

### Step-by-Step Journey of a Notification
1.  **The Trigger:** A microservice (e.g., Marketing Service) wants to send a promo. It sends a POST request to our **Notification API Gateway**.
2.  **Ingestion:** The Gateway performs basic validation and immediately drops the message into **Kafka**. It returns a `202 Accepted` to the internal service.
3.  **Consumption:** A fleet of **Delivery Workers** (Kafka Consumers) constantly poll the Kafka topics.
4.  **Identity Resolution:** The worker reads the `user_id` from the message and queries the **Device Registry** to find out what phone the user has.
5.  **Idempotency Check:** The worker checks **Redis** to ensure this exact notification hasn't been sent to this user recently.
6.  **Dispatch:** The worker transforms the payload into Apple/Google's specific format and fires an HTTP/2 request to APNS or FCM.
7.  **Persistence:** The worker asynchronously logs the success/failure to a high-write database (Cassandra).

---

## 4. Deep Dive: Kafka Internals (Building Topics & Routing)

A common mistake is creating a Kafka topic per user. Kafka is not designed for millions of topics; it is designed for a few topics with high throughput.

### 4.1 Topic Design
We categorize topics by **Priority** and **Event Type**, not by user. 
* `topic_urgent`: OTPs, Account Security Alerts.
* `topic_transactional`: "Your ride is arriving", "Payment successful".
* `topic_promotional`: "50% off sale today!"

*Why?* If Marketing blasts 10 million promos, it will flood `topic_promotional`. Because `topic_urgent` is completely separate, a user trying to log in will still receive their OTP instantly without waiting behind 10 million promotional messages.

### 4.2 Partitions and Ordering
Each topic is divided into **Partitions** (e.g., 64 partitions per topic). Kafka guarantees ordered delivery *only within a single partition*. 
* We use the `user_id` as the **Kafka Message Key**.
* When the API Gateway publishes to Kafka, Kafka runs a hash function: `Hash(user_id) % 64`.
* This ensures that every message intended for User 123 *always* goes to Partition 5. 
* Therefore, User 123 will never receive "Ride Finished" before "Ride Started", because the messages are processed sequentially by the same worker reading Partition 5.

### 4.3 Consumer Groups
Our Delivery Workers operate in a **Consumer Group**. If we have 64 partitions, we can scale up to 64 Delivery Workers. Kafka automatically assigns one partition to one worker, ensuring no two workers process the same message simultaneously.

---

## 5. Deep Dive: Identity & Resolution (Who gets what?)

The internal system only knows `user_id = "user_789"`. Apple and Google have no idea who "user_789" is. They only understand cryptographic hardware strings called **Device Tokens**.

### 5.1 The Device Registry
When a user installs our app and accepts the "Allow Notifications" prompt, the iOS/Android OS generates a unique token. The mobile app sends an API call to our backend to register it.

**Database Schema: `user_devices` (PostgreSQL / Redis Cache)**
* `user_id` (UUID, Indexed)
* `device_token` (String, Primary Key)
* `platform` (Enum: `APNS` or `FCM`)
* `app_version` (String)
* `timezone` (String) - *Useful for not sending promos at 3 AM.*

### 5.2 The Worker's Job
When the Delivery Worker pulls the message:
```json
{"user_id": "user_789", "msg": "Sale Live!"}
```
It queries the Device Registry Cache (`GET device:user_789`). It gets back:
```json
{"platform": "APNS", "token": "a1b2c3d4e5..."}
```
Now the worker knows exactly *where* and *how* to send the packet.

---

## 6. Deep Dive: Delivery & Idempotency

At 20,000 QPS, workers will crash. Network connections will drop. Kafka will re-deliver batches of messages to new workers. We must prevent users from receiving duplicate push notifications.

### 6.1 Redis Pipeline Deduplication
Before calling Apple/Google, the Delivery Worker checks a Redis cluster using an atomic `SETNX` (Set if Not Exists) command.

* **Key Format:** `push_sent:{campaign_id}:{user_id}`
* **Execution:** The worker pulls a batch of 100 messages from Kafka. It uses a **Redis Pipeline** to send 100 `SETNX` commands in a single network trip.
* **Result:** If Redis returns `1`, it's the first time we've seen this message -> Send to Apple. If Redis returns `0`, another worker already sent it -> Skip it.
* **TTL:** Keys are given a 48-hour Time-To-Live so Redis memory doesn't grow infinitely.

### 6.2 Provider Integration (APNS/FCM)
The worker transforms the internal JSON into the provider's specific schema.
* It opens a long-lived **HTTP/2 multiplexed connection** to APNS/FCM. (Crucial: Do not open a new TCP connection for every push, this will exhaust server ports immediately).
* It sends the payload over the wire.

---

## 7. Reliability, Throttling & Feedback Loops

### 7.1 Throttling (Protecting our own systems)
If we successfully push 10 million notifications, and 2 million users click it instantly, those 2 million users will open the app and accidentally DDoS our own backend servers. 
* **Solution:** The API Gateway enforces a **Token Bucket Rate Limiter** specifically for `topic_promotional`. It shapes the traffic, trickling the 10 million messages into Kafka over a 2-hour window (e.g., 1,500 per second maximum).

### 7.2 The Feedback Loop (Handling App Uninstalls)
If User 123 uninstalls the app, their `device_token` becomes invalid. If we keep trying to send pushes to it, Apple/Google will rate-limit or ban our servers.
* **Solution:** When the Delivery Worker calls APNS/FCM, the provider will return an HTTP `410 Gone` if the token is dead.
* The worker takes this `410` response and drops a message into a `dead_tokens` Kafka topic.
* A background cleanup service consumes this topic and deletes the token from the `Device Registry` database, keeping our registry clean and efficient.

### 7.3 Observability
* **Prometheus/Grafana Metrics:**
    * `kafka.consumer_lag`: Alerts us if Delivery Workers are falling behind the influx of messages.
    * `apns.delivery_latency`: Tracks how fast Apple is accepting our requests.
    * `notification.success_rate`: Ratio of successful 200 OKs vs 410/500 errors.