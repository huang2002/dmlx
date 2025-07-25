class Model:
    threshold: float = 0.5

    def predict(self, x: list[float]) -> list[float]:
        return [(1.0 if t >= self.threshold else 0.0) for t in x]
