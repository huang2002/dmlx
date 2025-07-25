from typing import cast

import click

from dmlx.component import Component
from dmlx.context import argument, option, param


class ModelComponent(Component):
    model_locator = cast(str, argument("model_locator"))

    def __init__(self) -> None:
        super().__init__()
        self.default_factory_name = "Model"
        self.module_base = "test_module.model"

    def __call__(self) -> object:
        return self.load(self.model_locator)


model_component = ModelComponent()


class DatasetComponent(Component):
    dataset_locator = cast(str, option("--dataset"))

    def __init__(self) -> None:
        super().__init__()
        self.default_factory_name = "Dataset"
        self.module_base = "test_module.dataset"

    def __call__(self) -> object:
        return self.load(self.dataset_locator)


dataset_component = DatasetComponent()


class Trainer:
    dataset_size = cast(int, option("-s", "--dataset-size", type=int))
    epochs = cast(int, param(click.Option, "-e", "--epochs", type=int))

    def __init__(self) -> None:
        self.model = model_component()
        self.dataset = dataset_component()

    def run(self) -> dict:
        x = cast(list[float], self.dataset(self.dataset_size))  # type: ignore
        y = cast(list[float], self.model.forward(x))  # type: ignore
        return {"x": x, "y": y, "epochs": self.epochs}
