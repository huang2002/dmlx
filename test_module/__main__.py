import os

import click

from dmlx.experiment import Experiment

experiment = Experiment("test")
experiment.meta_file_path = "info.json"


@experiment.main()
@click.option("--base-dir")
def main(**args) -> None:
    os.chdir(args["base_dir"])
    experiment.init()


experiment.run()
