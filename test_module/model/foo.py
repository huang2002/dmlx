class Model:
    threshold: float

    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    def predict(self, x: list[float]) -> list[float]:
        return [(1.0 if t >= self.threshold else 0.0) for t in x]
