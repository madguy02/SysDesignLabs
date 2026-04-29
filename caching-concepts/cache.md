  

# Learnings on Caching

  

### What is a Cache

  

A short term memory for your system. In computer science, we call it a high speed data-storage layer that stores a subset of data as compared to your primary storage, and this is beneficial because it can serve data faster than the primary storage because this subset is stored in a RAM.

  

### Caching Strategies

  

Here are the primary caching strategies:

  

    1) **Cache-Aside (Lazy-Loading)** : This is a very common one, all
    of us use it at the very basic level. When an application sends a
    request to fetch data, first it goes to the cache, if it's a "cache
    hit", then it returns the data, else if it's a cache miss, it goes
    to the primary storage (postgres/sql etc etc.), searches for the
    data and then returns to the application.
    
      
    
	    Best for: Read-heavy workloads, where data does not change
	    constantly (what can we do in case of data changing frequently? lets
	    discuss later in this document)
	    
	      
	    
	    Trade-off: The first request is always slow(cold start)
    
      
      
    
    2) **Read-Through:** The app treats the cache as the main database,
    it only talks to the cache, which means if data is not present in
    the cache, it pulls data from the primary storage and updates the
    cache, the application has no knowledge of it.
    
      
    
	    Best for: Keeping application code clean, the app does not need to
	    know about database logic
	    
	      
	    
	    Trade-off: the first request where the data is not found in cache
	    faces a double penalty, here the request moves from application to
	    cache and then cache to primary storage, which causes a lot of
	    delay. Also there is stale data risk, if an external job updates the
	    primary storage, the cache has no idea about it, hence the data
	    could be out of sync.
    
      
      
    
    3) **Write-Through:** Here the cache and the primary storage are
    updated in harmony, everytime it writes data to primary storage, it
    also updates the secondary storage.
    
      
    
	    Best for: Here the data is never stale.
	    
	      
	    
	    Trade-off: For write-heavy cases, it will introduce a lot of
	    latency.
    
      
      
    
    4) **Write-Back:** The application write data only to the cache, the
    cache then asynchronously updates primary storage with some delay.
    The write is acknowledged immediately and response is returned, but
    then later the cache flushes the changes to primary storage
    
      
    
	    Best for: Write workloads, like counter, live comments etc.
	    
	      
	    
	    Trade off: If the cache crashes before the sync, data is lost
	    forever.
    
      
      
    
    5) **Write-Around:** Data is written directly to the primary
    storage, only read operations populate the cache.
    
      
    
	    Best for: Data that is written once and rarely read again such as
	    logs archived records etc. Which means, if a youtube video with 10
	    views have 10 comments, then the data directly goes to the primary
	    storage, because it is highly unlikely many people will check those
	    comments, but suddenly the video gets 100,000 views and people are
	    checking comments, then for the first few users the data is pulled
	    from primary storage and then cached just to avoid "cache
	    pollution", as a result first few requests will be slow


### Eviction Strategies

Common strategies used for cache eviction:

	1) **LRU (Least Recently Used):** It removes the data that has least amount 
	of usage and is least likely to be ever used again

		How it works: It maintains an order based on their access time inside the cache
		When the cache is full, it simply evicts the data at the very end of the list

		Best for: General purpose caching.
	

	2) **LFU (Least Frequently Used):** It looks at the popularity of the data rather than timing

		How it works: Everytime a piece of data is accessed, a counter is incremented.When the cache is full
		it evicts the data with least counter value

		Trade-off: An item that could be extremely popular an hour ago, might stay in the cache for too long even
		if the popularity is dead.
	
	
	3) **FIFO (First In First out):** This is the simplest cache eviction policy
		
		How it works: It evicts the data exactly the same way it is inserted, regardless of how many times 
		it was accessed

		Best-for: where the data has a predictable life-cyle or we want to reduce CPU overhead of tracking access time

	
	4) **Random Replacement:** This is as the name say, it randomly evicts a key

		The Pro: It requires almost 0 CPU or memory to track metadata like counters or time etc.

		The Con: It can very well delete the hottest key in the cache

	
	5) **TTL:** Here we attach a time-to-live value to the key, so it expires as the time is reached 
	its expiration and not eviction

