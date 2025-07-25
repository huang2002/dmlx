class BlahDataset:
    offset: float

    def __init__(self, offset: float = 0.0) -> None:
        self.offset = offset

    def __call__(self, size: int) -> list[float]:
        return [float(x) + self.offset for x in range(size)]
