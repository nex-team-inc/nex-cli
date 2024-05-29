import asyncio
import socket
from typing import List


class PortChecker:
    @staticmethod
    def check(host: str, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                if sock.connect_ex((host, port)) == 0:
                    return True
        except:
            return False

        return False

    def __init__(self, concurrency: int = 32):
        self._concurrency = concurrency

    def filter(self, hosts: List[str], port: int = 5555) -> List[str]:
        return asyncio.run(self._run(hosts, port, self._concurrency))

    @classmethod
    async def _run(cls, hosts: List[str], port: int, concurrency: int):
        tasks = asyncio.Queue(concurrency)
        results = asyncio.Queue(concurrency)
        workers = [
            asyncio.create_task(cls._checker_worker(port, tasks, results))
            for _ in range(concurrency)
        ]
        ret = await asyncio.gather(
            cls._collector(len(hosts), results),
            cls._assigner(concurrency, hosts, tasks),
            *workers
        )
        return ret[0]

    @staticmethod
    async def _assigner(
        concurrency: int, hosts: List[str], tasks: asyncio.Queue
    ) -> None:
        for host in hosts:
            await tasks.put(host)
        for _ in range(concurrency):
            await tasks.put("")

    @staticmethod
    async def _checker_worker(
        port: int, tasks: asyncio.Queue, results: asyncio.Queue
    ) -> None:
        while True:
            host = await tasks.get()
            if host == "":
                return
            # Check if host is good.
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), timeout=3
                )
                writer.close()
                await writer.wait_closed()
                await results.put((host, True))
            except:
                await results.put((host, False))

    @staticmethod
    async def _collector(count: int, results: asyncio.Queue) -> List[str]:
        ret = []
        for i in range(count):
            host, value = await results.get()
            if value:
                ret.append(host)
        return ret
