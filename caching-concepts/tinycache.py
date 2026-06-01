import threading
import time

class TinyCache:
    def __init__(self):
        self._storage = {}
        self._expiry = {}

        self._evictor = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._evictor.start()
    

    def set(self, key, value, ttl=None):
        self._storage[key] = value

        if ttl:
            self._expiry[key] = time.time() + ttl
        
        print(f"[SET] {key} = {value} (TTL: {ttl}s)")

    
    def _delete(self, key):
        self._storage.pop(key, None)
        self._expiry.pop(key, None)

    

    def get(self, key):
        if key in self._expiry and self._expiry[key] > time.time():
            print(self._storage.get(key, None))
            return self._storage.get(key, None)
        else:
            self._delete(key)
            return None
    
    def _cleanup_loop(self):
        while True:
            now = time.time()
            expired_keys = [k for k, t in self._expiry.items() if now > t]

            for k in expired_keys:
                self._delete(k)
            
            time.sleep(3)

tinyCache = TinyCache()
# tinyCache.set(1, "Manish", ttl=3)
# tinyCache.set(2, "Manashi", ttl=2)
# tinyCache.set(3, "Bogi", ttl=1)

tinyCache.get(2)
tinyCache.get(3)
tinyCache.get(1)


    
    