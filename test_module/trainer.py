from typing import cast

import click

from dmlx.context import argument, component, option, param


class Trainer:
    dataset_size = cast(int, option("-s", "--dataset-size", type=int))
    epochs = cast(int, param(click.Option, "-e", "--epochs", type=int))
    dataset_locator = option("-d", "--dataset")
    model = component(argument("model_locator"), "test_module.model", "Model")
    dataset = component("dataset_locator", "test_module.dataset", "Dataset")

    def run(self) -> dict:
        x = cast(list[float], self.dataset(self.dataset_size))
        y = cast(list[float], self.model.forward(x))
        return {"x": x, "y": y, "epochs": self.epochs}
