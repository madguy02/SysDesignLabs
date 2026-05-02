
# ⚡ CDN (Content Delivery Network)

## 1. The Core Purpose
To reduce **latency** by bringing data physically closer to the user.

## 2. Key Mechanics
* **Edge Servers:** Distributed servers that cache content.
* **Cache Hit/Miss:** Whether the content was found at the edge or needed to be fetched from the Origin.
* **Origin Shield:** A secondary cache layer to protect the main server from high traffic.

## 3. Benefits
* **Performance:** Drastically lower TTFB (Time to First Byte).
* **Reliability:** If the Origin is briefly down, the CDN can still serve cached content.
* **Security:** Absorbs DDoS attacks at the network edge.

## 🛠️ Cache Invalidation Strategies
* **TTL (Time-To-Live):** Expiration based on time. Simple but can serve stale data.
* **Versioning (Fingerprinting):** Changing the filename (e.g., `style.hash.css`) to force a "new" fetch. Best for static assets.
* **Purge:** API-driven manual deletion of a specific URL.
* **SWR (Stale-While-Revalidate):** Serve old data while fetching new data in the background. Balances speed and freshness.
* **Request Collapsing:** Merging multiple requests for the same missing file into one call to the Origin to prevent a "Thundering Herd."