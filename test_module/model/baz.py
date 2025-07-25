class Model:
    dx: float

    def __init__(self, dx: float) -> None:
        self.dx = dx

    def forward(self, x: list[float]) -> list[float]:
        dx = self.dx
        return [t + dx for t in x]
