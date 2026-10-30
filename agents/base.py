"""
Agent Protocol and Base Class for Raksha AI.
Every agent in `agents/<name>/` implements this contract.
"""
from typing import Any, Generic, List, Protocol, TypeVar, runtime_checkable

InT = TypeVar("InT")
OutT = TypeVar("OutT")


@runtime_checkable
class Agent(Protocol[InT, OutT]):
    """
    Standard interface for all Raksha AI agents.
    Allows pipeline runners, evaluation harnesses, and API stubs to invoke
    any agent with predictable typed inputs and outputs.
    """
    name: str
    version: str

    def run(self, input_data: InT) -> OutT:
        """Execute single-item agent inference."""
        ...

    def run_batch(self, batch: List[InT]) -> List[OutT]:
        """Execute batch inference."""
        ...


class BaseAgent(Generic[InT, OutT]):
    """
    Convenience base class providing default batch execution over single run().
    """
    name: str = "base_agent"
    version: str = "0.1.0"

    def run(self, input_data: InT) -> OutT:
        raise NotImplementedError("Agent subclasses must implement run()")

    def run_batch(self, batch: List[InT]) -> List[OutT]:
        return [self.run(item) for item in batch]
