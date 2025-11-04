import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import cast

import click
import pytest

from dmlx.experiment import Experiment

original_cwd = os.getcwd()


def test_experiment_path() -> None:
    now = datetime(2002, 1, 2, 3, 4, 5, 6)
    name_template_variables = Experiment.get_name_template_variables(now)
    expected_name = "2002/01/02/030405-" + name_template_variables["hex"]
    experiment = Experiment(name_template_variables=name_template_variables)
    assert experiment.name == expected_name
    assert experiment.path == Experiment.BASE_DIR / expected_name


def test_experiment_before_main() -> None:
    experiment = Experiment()

    @experiment.before_main()
    def before_main(**args) -> None:
        experiment.name += "_" + args["tag"]

    @experiment.main()
    @click.option("--tag")
    def main(**args) -> None:
        assert experiment.name.endswith("_blah")
        assert experiment.path.name.endswith("_blah")

    assert experiment.command is not None
    experiment.command.main(["--tag=blah"], standalone_mode=False)


def test_experiment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    sys.path.append(str(Path(__file__).parent.parent.resolve()))

    experiment = Experiment()

    with experiment.context():
        from test_module.trainer import Trainer

        class TestClass:
            test_value = cast(
                int, experiment.option("--test-value", type=int, default=0)
            )

    with pytest.raises(RuntimeError):
        experiment.run()
    with pytest.raises(RuntimeError):
        experiment.args
    with pytest.raises(
        RuntimeError,
        match="Params cannot be accessed before experiment run or loading!",
    ):
        TestClass().test_value

    main_finished = False

    @experiment.main()
    def main(**args) -> None:
        nonlocal main_finished

        assert experiment.args == args
        assert args == {
            "model_locator": "baz?dx=0.5",
            "dataset": "blah:BlahDataset",
            "dataset_size": 5,
            "epochs": 8,
            "test_value": 0,
            "flag": False,
        }

        with pytest.raises(RuntimeError):
            experiment.option("--should-fail")

        experiment.init()

        with pytest.raises(RuntimeError):
            experiment.name = "blah"
        with pytest.raises(RuntimeError):
            experiment.meta_file_path = "blah"

        trainer = Trainer()
        assert trainer.dataset_size == 5
        assert trainer.epochs == 8

        from test_module.model.baz import Model

        assert isinstance(trainer.model, Model)
        assert trainer.model.dx == 0.5

        from test_module.dataset.blah import BlahDataset

        assert isinstance(trainer.dataset, BlahDataset)
        assert trainer.dataset.offset == 0.0

        assert trainer.run() == {
            "x": [0.0, 1.0, 2.0, 3.0, 4.0],
            "y": [0.5, 1.5, 2.5, 3.5, 4.5],
            "epochs": 8,
        }

        main_finished = True

    with pytest.raises(ValueError):

        @experiment.main()
        def should_fail(**args) -> None: ...

    experiment.option("--flag", is_flag=True)

    assert experiment.command is not None
    cli_args = ["baz?dx=0.5", "--dataset", "blah:BlahDataset", "-e", "8", "-s", "5"]
    experiment.command.main(cli_args, standalone_mode=False)

    assert main_finished

    with pytest.raises(RuntimeError):
        experiment.command.main(cli_args, standalone_mode=False)
    with pytest.raises(RuntimeError):
        experiment.run()
    with pytest.raises(RuntimeError):
        experiment.load()

    assert experiment.path.exists()
    assert experiment.path.is_dir()
    assert (experiment.path / experiment.meta_file_path).exists()
    assert (experiment.path / experiment.meta_file_path).is_file()

    with (experiment.path / experiment.meta_file_path).open("r") as meta_file:
        meta = cast(Experiment.Meta, json.load(meta_file))
    assert meta["name"] == experiment.name
    assert meta["birth"] == str(experiment.birth)
    assert meta["birth_timestamp"] == experiment.birth.timestamp()
    assert meta["args"] == experiment.args


def test_experiment_cli_and_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess

    base_dir = str(tmp_path.resolve())
    cli_process = subprocess.run(
        ["python", "test_module", "--base-dir", base_dir],
        capture_output=True,
        text=True,
    )
    assert cli_process.returncode == 0, cli_process.stderr
    assert cli_process.stdout == ""
    assert cli_process.stderr == ""

    experiment_name = "test"
    meta_file_path = "info.json"

    experiment_dir = tmp_path / "experiments" / experiment_name
    assert experiment_dir.exists()
    assert experiment_dir.is_dir()

    assert (experiment_dir / meta_file_path).exists()
    assert (experiment_dir / meta_file_path).is_file()
    with (experiment_dir / meta_file_path).open("r") as meta_file:
        loaded_meta = cast(Experiment.Meta, json.load(meta_file))

    monkeypatch.chdir(tmp_path)
    experiment = Experiment(meta_file_path=meta_file_path)
    experiment.name = experiment_name
    experiment.load()
    assert experiment.meta == loaded_meta

    with pytest.raises(RuntimeError):
        experiment.name = "not_allowed"
    with pytest.raises(RuntimeError):
        experiment.load()
