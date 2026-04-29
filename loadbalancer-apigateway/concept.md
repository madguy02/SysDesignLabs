
### What is Load Balancer

A Load Balancer sits infront of a server farm, and based on different algorithms (Round Robin or Least Connections) it chooses a server
and forwards the request

It ensures no server is overwhelmed with too many requests while other sit idle. It usually operates at Layer 4 (TCP) or Layer 7 (HTTP)

The functions it performs are:

Health Checks: LB detects which server went down and which are up and based on that it sends out traffic
SSL Termination: It decrypts the incoming HTTPS traffic so that backend servers don't have to waste cycles
Redundancy: It provides a single entry point for a service that might be spread across 100 servers


### What is API Gateway

While Load Balancers manage the traffic, the API Gateway manages the API itself, it inspects the requests and perform complex logic to decide where it should do, it oftern talks to different services to fulfil a single request

Strictly operates at Layer 7 (application layer)

The functions it performs are:

Request Routing: it can route /users request to Users service and /orders request to Orders service
Authentication & Authorization: it checks if the user is logged in or not
Rate limiting: stop spamming with requests
