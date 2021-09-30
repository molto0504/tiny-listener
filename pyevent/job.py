import re
import asyncio
from typing import Any, Dict, Generator, List


class Job:
    def __init__(self, name: str) -> None:
        self.name = name
        self.trigger = asyncio.Event()

    @property
    def is_done(self) -> bool:
        return self.trigger.is_set()

    def done(self) -> None:
        self.trigger.set()

    async def wait(self) -> Any:
        return await self.trigger.wait()

    def __repr__(self) -> str:
        return "{}(name={}, done={})".format(self.__class__.__name__, self.name, self.is_done)


class Jobs:
    def __init__(self, *names: str) -> None:
        self._jobs: Dict[str, Job] = {}
        self.add(*names)

    def add(self, *names: str) -> None:
        for name in names:
            self._jobs[name] = Job(name)

    def __match(self, pattern: str) -> Generator[Job, None, None]:
        for job in self._jobs.values():
            if re.match(pattern, job.name):
                yield job

    def first(self, pattern: str = ".*") -> Job:
        for job in self.__match(pattern):
            if not job.is_done:
                return job

    def all(self, pattern: str = ".*") -> List[Job]:
        return [job for job in self.__match(pattern) if not job.is_done]

    def get(self, name: str) -> Job:
        if name not in self._jobs:
            raise ValueError(f"job `{name}` does not exist")
        return self._jobs[name]

    def done(self, pattern: str = ".*") -> None:
        for job in self.__match(pattern):
            job.done()

    def is_done(self, pattern: str = ".*") -> bool:
        return all(job.is_done for job in self.__match(pattern))

    def __len__(self) -> int:
        return len(self._jobs)
