from typing import Any, Coroutine

class ABCMonitor:
    def __new__(cls, *args, **kwargs):
        inst = None
        
        if inst is None:
            inst = object.__new__(cls)
        
        return inst

    def _get_value(self) -> Any:
        raise NotImplementedError
    
    async def _save_value(self) -> Coroutine[Any, Any, None]:
        raise NotImplementedError
    
    async def run(self) -> Coroutine[Any, Any, None]:
        raise NotImplementedError


class ABCDataBaseObjectFabric:
    def create(self) -> Any:
        raise NotImplementedError