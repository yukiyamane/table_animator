from __future__ import annotations
from table_animator.core.animator import Animator
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from table_animator.main import MyApp


class CoreSystem:
    def __init__(self, base: MyApp):
        self.__animator = Animator(base)

    def update(self, frame_time: float, dt: float):
        self.__animator.update(frame_time, dt)

    
