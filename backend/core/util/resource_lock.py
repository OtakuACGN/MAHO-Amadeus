import asyncio
import logging
import time
from collections import deque


class ResourceLock:
    """通用独占资源锁，持有者超30秒自动清理"""

    def __init__(self, timeout: float = 30.0):
        self.queue = deque()
        self.condition = asyncio.Condition()
        self.holder = None
        self.holder_since = 0
        self.timeout = timeout
        asyncio.create_task(self._watchdog())

    async def _watchdog(self):
        """每秒检查持有者是否超时"""
        while True:
            await asyncio.sleep(1)
            async with self.condition:
                if self.holder and time.time() - self.holder_since > self.timeout:
                    logging.warning(f"[ResourceLock] {self.holder} 超时，强制清理")
                    self._clear_first()

    def _clear_first(self):
        """强制清理队首"""
        if self.queue:
            removed = self.queue.popleft()
            self.holder = None
            self.condition.notify_all()
            logging.info(f"[ResourceLock] 已清理: {removed}, 剩余: {list(self.queue)}")

    async def reserve(self, agent_id):
        async with self.condition:
            if agent_id not in self.queue:
                self.queue.append(agent_id)

    async def acquire(self, agent_id):
        async with self.condition:
            if agent_id not in self.queue:
                self.queue.append(agent_id)
            while self.queue[0] != agent_id:
                await self.condition.wait()
            self.holder = agent_id
            self.holder_since = time.time()

    async def release(self, agent_id):
        async with self.condition:
            if self.holder == agent_id:
                self.queue.popleft()
                self.holder = None
                self.condition.notify_all()

    async def force_release(self, agent_id):
        async with self.condition:
            if agent_id == self.holder or agent_id in self.queue:
                self.queue = deque([a for a in self.queue if a != agent_id])
                if self.holder == agent_id:
                    self.holder = None
                    self.condition.notify_all()
                return True
            return False


class DummyLock:
    async def reserve(self, agent_id): pass
    async def acquire(self, agent_id): pass
    async def release(self, agent_id): pass
    async def force_release(self, agent_id): return True
