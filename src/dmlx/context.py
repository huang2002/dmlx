from inspect import cleandoc

from .experiment import Experiment


class ExperimentContext:
    _current_experiment: Experiment | None = None

    experiment: Experiment

    def __init__(self, experiment: Experiment) -> None:
        self.experiment = experiment

    def __enter__(self) -> "ExperimentContext":
        if ExperimentContext._current_experiment is not None:
            raise RuntimeError(
                "Experiment contexts cannot be stacked! That is, you cannot enter "
                "an experiment context when another one is active."
            )
        ExperimentContext._current_experiment = self.experiment
        return self

    def __exit__(self, _exception_type, _exception, _traceback) -> None:
        ExperimentContext._current_experiment = None


def get_current_experiment() -> Experiment:
    """Get the currently active experiment."""
    if ExperimentContext._current_experiment is None:
        raise RuntimeError(
            cleandoc(
                """
                Current experiment is unavailable! Typically, it should be available inside an experiment context:

                    ```python
                    with experiment.context():
                        from model import MyModel
                        from dataset import get_dataset
                    ```
                """
            )
        )
    return ExperimentContext._current_experiment
