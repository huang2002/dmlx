import pytest

from dmlx.context import ExperimentContext, get_current_experiment
from dmlx.experiment import Experiment


def test_experiment_context() -> None:
    with pytest.raises(RuntimeError):
        get_current_experiment()

    experiment = Experiment()

    with pytest.raises(RuntimeError):
        get_current_experiment()

    with experiment.context() as context:
        assert isinstance(context, ExperimentContext)
        assert get_current_experiment() is experiment
        with pytest.raises(RuntimeError):
            with experiment.context():
                pass  # pragma: no coverage

    with pytest.raises(RuntimeError):
        get_current_experiment()
