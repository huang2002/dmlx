from inspect import cleandoc

import click

from .experiment import Experiment


class ExperimentContext:
    _current_experiment: Experiment | None = None

    experiment: Experiment

    def __init__(self, experiment: Experiment) -> None:
        self.experiment = experiment

    def __enter__(self) -> "ExperimentContext":
        assert ExperimentContext._current_experiment is None, (
            "Experiment contexts cannot be stacked! That is, you cannot enter "
            "an experiment context when another one is active."
        )
        ExperimentContext._current_experiment = self.experiment
        return self

    def __exit__(self, _exception_type, _exception, _traceback) -> None:
        ExperimentContext._current_experiment = None


def get_current_experiment() -> Experiment:
    """Get the currently active experiment."""
    assert ExperimentContext._current_experiment is not None, cleandoc(
        """
        Current experiment is unavailable! Typically, it should be available inside an experiment context:

            ```python
            with experiment.context():
                from model import MyModel
                from dataset import get_dataset
            ```
        """
    )
    return ExperimentContext._current_experiment


def param(cls: type[click.Parameter], *args, **kwargs) -> property:
    """Create a param property that is to be read from the experiment command.
    (This is a helper function that invokes `experiment.param()` on the
    active experiment in current context.)

    Returns:
        param (click.Parameter): The created param.
    """
    return get_current_experiment().param(cls, *args, **kwargs)


def argument(*args, **kwargs) -> property:
    """Create an argument property that is to be read from the experiment command.
    (This is a helper function that invokes `experiment.argument()` on the
    active experiment in current context.)

    Returns:
        argument (click.Argument): The created argument.
    """
    return get_current_experiment().argument(*args, **kwargs)


def option(*args, **kwargs) -> property:
    """Create an option property that is to be read from the experiment command.
    (This is a helper function that invokes `experiment.option()` on the
    active experiment in current context.)

    Returns:
        option (click.Option): The created option.
    """
    return get_current_experiment().option(*args, **kwargs)
