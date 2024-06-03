from hashlib import sha3_256
from typing import Dict

from _321CQU.tools.Singleton import Singleton


__all__ = ['AuthIdManager']


class AuthIdManager(metaclass=Singleton):
    """
    提供了用户唯一标识生成、标识缓存的管理类
    """
    _uids: Dict[str, bytes] = {}
    _ttl: float = 86400  # Time-to-live for cache

    def __init__(self):
    """
    设置锁机制和启动一个后台线程来定期清理过期的缓存条目
    """
        self._lock = threading.Lock()
        self._cleanup_thread = threading.Thread(target=self._cleanup, daemon=True)
        self._cleanup_thread.start()

    def add_uid(self, auth: str, sid: str, name: str) -> bytes:
        with self._lock:
            if sid in self._uids.keys():
                return self.get_uid(sid)

            sh = sha3_256()
            sh.update((auth + name + sid).encode('utf-8'))
            result = sh.digest()
            self._uids[sid] = (result,time.time())
            return result

    def get_uid(self, sid: str) -> bytes:
        with self._lock:
            entry = self._uids.get(sid)
        if entry:
            uid,timestamp = entry
            if time.time() - timestamp < self._ttl:
                return uid
            else:
                del self._uids[sid]

        return None

    def _cleanup(self):
        while True:
            time.sleep(self._ttl)
            with self._lock:
                now = time.time()
                expired_keys = [sid for sid,(uid,timestamp) in self._uids.items() if now - timestamp >= self._ttl]
                for key in expired_keys:
                    del self._uids[key]
