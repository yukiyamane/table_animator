from __future__ import annotations
from typing import Optional
from dataclasses import dataclass
from table_animator.shared.util.yamane_prepare import *
from table_animator.shared.util.yamane_state_machine import StateMachine, StateContext
from table_animator.graphics.hud import HUD

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from table_animator.main import MyApp


class Animator:
    def __init__(self, base: MyApp):
        self.__base = base

        self.__state_machine = StateMachine(self)
        self.__state_machine.set_next_state(self.__prepare)

        self.__base.accept("g", self.__accept_battle_start)

    def __accept_battle_start(self):
        self.__state_machine.set_next_state(self.__allocate)

    @property
    def marble_list(self):
        return self.__marble_list

    def update(self, current_raw_time: float, dt: float):
        self.__state_machine.update(current_raw_time, dt)

    def __prepare(self, ctx: StateContext):
        if ctx.is_first:
            self.__hud = HUD(self.__base)
            self.__state_machine.set_next_state(self.__idle)

    def __idle(self, ctx: StateContext):
        self.__hud.update()

    def __allocate(self, ctx: StateContext):
        if ctx.is_first:
            self.__hud.start()
        self.__hud.update()
