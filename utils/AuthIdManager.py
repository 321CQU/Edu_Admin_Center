from hashlib import sha3_256
from typing import Dict

from _321CQU.tools.Singleton import Singleton


__all__ = ['AuthIdManager']


class AuthIdManager(metaclass=Singleton):
    """
    提供了用户唯一标识生成、标识缓存的管理类
    """
    _uids: Dict[str, bytes] = {}

    def add_uid(self, auth: str, sid: str, name: str) -> bytes:
        if sid in self._uids.keys():
            return self.get_uid(sid)

        sh = sha3_256()
        sh.update((auth + name + sid).encode('utf-8'))
        result = sh.digest()
        self._uids[sid] = result
        return result

    def get_uid(self, sid: str) -> bytes:
        return self._uids.get(sid)
