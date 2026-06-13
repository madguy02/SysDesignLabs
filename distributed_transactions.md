# Distributed Transactions: 2-Phase Commit vs. Saga Pattern
*Notes for System Design Interview Preparation*

## The Fundamental Problem: ACID vs. Scale
* **The Monolith:** In a single database architecture, transactions provide **ACID guarantees** (Atomicity and Isolation). If a multi-step operation fails, the database automatically rolls everything back invisibly.
* **The Distributed Shift:** As systems scale, monoliths are broken into microservices, or databases are sharded. Data now lives across multiple independent machines.
* **Distributed Transactions:** A single logical operation (e.g., an e-commerce checkout) must now span independent databases that do not know about each other. If step 1 succeeds but step 2 fails, there is no automatic database-level rollback.

## Approach 1: Two-Phase Commit (2PC)
2PC is the classic, academic approach aiming for strong consistency across distributed nodes.

* **Mechanism:** A central "coordinator" manages the transaction across two phases:
    1. **Prepare Phase:** The coordinator asks all participating databases if they can commit. They process the work, lock the affected rows, and vote "Yes" or "No".
    2. **Commit Phase:** If all vote "Yes", the coordinator tells them to make the changes permanent and release locks. If any vote "No", it tells everyone to abort.
* **Why 2PC Fails at Internet Scale:**
    * **It is a Blocking Protocol:** If the coordinator crashes after collecting votes but before sending the commit command, participating nodes are stuck holding locks indefinitely.
    * **Speed:** The entire system moves at the speed of the slowest participant.
* **Production Reality:** 2PC is almost never used across independent microservices. It is only viable *inside* tightly coupled, specialized distributed databases (like Google Spanner or Yugabyte).

## Approach 2: The Saga Pattern
Saga is the industry-standard architecture for distributed transactions, used by companies like Uber, Netflix, and Amazon.

* **Core Concept:** You break the distributed transaction into a chain of independent, local transactions. Each service commits to its own database sequentially.
* **Compensating Actions:** If a downstream service fails, you cannot roll back the upstream databases because they have already committed. Instead, you trigger a "compensating action"—a business-level "undo" (e.g., issuing a refund instead of an abort).
* **The Trade-off:** You trade strong consistency for **Eventual Consistency**. The system might briefly exist in an inconsistent state (a customer sees a charge, then a refund), but it never blocks other transactions and always converges to the correct state.

## Implementing Sagas: Choreography vs. Orchestration

### 1. Choreography (Decentralized)
* **Mechanism:** Services use a Publish/Subscribe (pub/sub) pattern. A service finishes its job, publishes an event (e.g., "Card Charged"), and downstream services react to it independently.
* **Pros:** Great for simple, 2-3 step flows (like basic notification triggers) without central coupling.
* **Cons:** At scale (5+ services), tracking the state of a transaction becomes a nightmare. Finding where a failure occurred requires piecing together distributed logs.

### 2. Orchestration (Centralized)
* **Mechanism:** A dedicated orchestrator service acts as a controller, commanding each microservice one step at a time.
* **Pros:** You have a single source of truth for the transaction state, branching logic, and failure handling. It knows exactly which compensations to run and in what order.
* **Durability:** Tools like AWS Step Functions or Temporal are purpose-built for this. Unlike 2PC coordinators, orchestrators are highly durable; if they crash, they read their state from a database and pick up exactly where they left off without holding row locks.

## Hidden Complexities & Reliability Engineering
* **Imperfect Compensations:** Compensating actions are messy. You can't "un-send" an email. Also, your compensation APIs must be strictly **idempotent** so that if a refund fails and retries 5 times, it only refunds the customer once.
* **The Dual Write Problem:** When a microservice finishes a step, it must save the state to its DB *and* publish an event to the message broker. If the DB write succeeds but the event publish fails, the Saga stalls permanently.
* **Solution - The Transactional Outbox Pattern:** To fix the dual write problem, write both the state change and the outbound event into the *same* database in a single local transaction (the event goes to an "outbox" table). A background process (like Change Data Capture) safely pulls from the outbox table and guarantees the message is published.

## Architectural Decision Framework
When designing a system, follow this hierarchy:
1. **Can you avoid it entirely?** Local database transactions are infinitely faster and safer. Always try to define your microservice boundaries so that data updated together lives in the same database.
2. **If you must distribute, accept eventual consistency.** Use the Saga pattern.
3. **Keep it simple first.** Use Choreography for straightforward 2-3 step flows.
4. **Scale with Orchestration.** When logic involves complex branching or you need deep operational visibility, use an orchestrator.
