import asyncio
from collections import deque

class ResourceLock:
    """
    通用独占资源锁：只有一个统一的排队队列。
    reserve 只是提前在队列中占位，acquire 则是正式开始等待直到轮到自己。
    用法： 
      await lock.reserve(agent_id)  # 提前占位（非阻塞），会在队列中让自己提前排队。
      await lock.acquire(agent_id)  # 相当于一个等待函数，如果自己在队列中的第一位就会直接跳过这一行，如果不在的话就会阻塞等待直到轮到自己。
      await lock.release(agent_id)  # 归还令牌，释放资源给下一位。
    """
    
    def __init__(self):
        self.queue = deque()
        self.condition = asyncio.Condition()
        self.current_holder = None

    async def reserve(self, agent_id):
        """
        提前在队列中占位（非阻塞）。
        如果agent_id不在队列中，将其添加到队列末尾。
        """
        async with self.condition:
            if agent_id not in self.queue:
                self.queue.append(agent_id)

    async def acquire(self, agent_id):
        """
        等待直到轮到自己。
        如果agent_id不在队列中，先添加到队列末尾。
        如果agent_id是队列的第一个且当前没有持有者，则立即获取锁。
        否则，阻塞等待。
        """
        async with self.condition:
            if agent_id not in self.queue:
                self.queue.append(agent_id)
            while self.queue[0] != agent_id:
                await self.condition.wait()
            self.current_holder = agent_id

    async def release(self, agent_id):
        """
        归还令牌，释放资源给下一位。
        只有当前持有者才能释放。
        """
        async with self.condition:
            if self.current_holder == agent_id:
                self.current_holder = None
                if self.queue:
                    self.queue.popleft()
                self.condition.notify_all()

class DummyLock:
    """
    空对象锁：接口与 ResourceLock 一致，但不执行任何实际的锁定逻辑。
    用于在配置文件中关闭锁机制时，保持代码逻辑不变。
    """
    async def reserve(self, agent_id):
        pass

    async def acquire(self, agent_id):
        pass

    async def release(self, agent_id):
        pass