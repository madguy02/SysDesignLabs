# 📖 DNS (Domain Name System) Mastery

## 1. The Lookup Chain
1. **Recursive Resolver:** The "Librarian" (ISP/Google) that hunts for the IP.
2. **Root Server:** Directs the resolver to the correct TLD (.com, .org).
3. **TLD Server:** Directs the resolver to the Authoritative Nameserver.
4. **Authoritative Server:** The final source of truth containing the A-Record.

## 2. Record Types to Know
* **A / AAAA:** Maps Name -> IPv4 / IPv6.
* **CNAME:** Maps Name -> Name (Alias).
* **MX:** Mail Exchange (Email routing).
* **TXT:** Metadata (Security/Verification like SPF/DKIM).
* **NS:** Lists the servers that are authoritative for the zone.

## 3. Performance & Security
* **TTL (Time To Live):** Controls how long a record is cached. Low TTL = fast changes; High TTL = better performance.
* **Anycast DNS:** Using BGP to route users to the geographically closest DNS server.
* **DNSSEC:** Cryptographically signing records to prevent DNS Cache Poisoning.