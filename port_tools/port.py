from . import port_defs


class Port(object):
    def __init__(self, **kwargs) -> None:
        self.name: str = kwargs.get(port_defs.NAME_KEY)
        if self.name is None:
            raise ValueError("Provided port has no name")
        self.address: int = int(kwargs.get(port_defs.ADDRESS_KEY), 16)


class IoPort(Port):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.direction: str = kwargs.get(
            port_defs.DIRECTION_KEY, port_defs.ALLOWED_DIRECTIONS[0]
        )
        if self.direction not in port_defs.ALLOWED_DIRECTIONS:
            raise ValueError(
                f"Unknown port direction ('{kwargs[port_defs.DIRECTION_KEY]}') for port {self.name}"
            )

        self.bit_width: int = kwargs.get(port_defs.BIT_WIDTH_KEY, 0)


class ClockPort(Port):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
