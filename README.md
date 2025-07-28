# dmlx

> Declarative Machine Learning eXperiments

## Introduction

`dmlx` is a declarative framework for machine learning (ML) experiments.
Typically, ML codebases use the standard python library `argparse` to parse
parameters from command line, and pass these parameters deep into the models and
other components. `dmlx` standardizes this process and provides an elegant
framework for experiment declaration and basic management, including the
following main features:

- **Declarative Experiment Components:** Declarative interfaces are presented
    for defining resusable and reproducible experiment components and
    hyperparameters, such as model path, dataset getter and random seed.
- **`click`-powered Command Line Interface:**
    [`click`](https://click.palletsprojects.com/) is integrated to provide
    powerful command line functionalities, including parameter properties.
- **Automatic Parameter Collection:** Parameter properties will be wired with
    command line inputs and collected for experiment reproducibility.
- **Experiment Archive Management:** Archive directories will be automatically
    created to hold experiment data for further analysis.
- **ML Framework Independent:** `dmlx` is independent from ML frameworks so you
    can use whatever ML framework you like (PyTorch/TensorFlow/ScikitLearn/...).

## Example

An example ML codebase using `dmlx` is illustrated below:

- `my_innovative_approach/`
    - `model/`
        - `baseline.py`
        - `ours.py`
    - `dataset/`
        - `dataset_foo.py`
        - `dataset_bar.py`
    - `experiments/`
        - ...
    - `approach.py`
    - `train.py`
    - `analyze.py`

1. Firstly, models are defined as submodules of the `model` module, and dataset
    loaders are defined as submodules of the `dataset` module. These components
    should expect normal Python arguments, and the component factories defined
    later using `component()` will parse command line parameters and pass the
    arguments to real components.

    ```python
    # model/xxx.py

    class Model:
        def __init__(self, alpha: float, beta: float, ...) -> None: ...
    ```

    ``` python
    # dataset/dataset_yyy.py

    def get_dataset_yyy(...): ...
    ```

2. Secondly, the components (models/datasets) and other parameters can be
    declared as properties on a composed approach using `dmlx`. The parameter
    properties, declared by `argument()` and `option()`, will define
    corresponding command line parameters and store them as instance attributes.
    The component properties, declared by `component()`, will create the actual
    component objects and store them as instance attributes.

    ```python
    # approach.py

    from dmlx.context import argument, option, component


    class Approach:
        model = component(
            argument("model_locator", default="ours"),  # click argument
            "model",  # module base
            "Model",  # default factory name
        )
        dataset = component(
            option("dataset_locator", "-d", "--dataset"),  # click option
            "dataset",  # module base
        )
        epochs = option("-e", "--epochs", type=int, default=800)  # click option

        def run(self):
            for epoch in range(self.epochs):
                for x, y_true in self.dataset:
                    y_pred = self.model(x)
                    yield x, y_true, y_pred
    ```

3. Thirdly, `dmlx.experiment.Experiment` can be used to declare your experiment.
    The experiment object will create an underlying `click` command, and the
    experiment context will collect the parameters(`model_locator`,
    `dataset_locater` and `epochs`) and wire them with command line inputs.

    ```python
    # train.py

    from dmlx.experiment import Experiment

    experiment = Experiment()

    with experiment.context():
        from approach import Approach

    @experiment.main
    def main(**args):
        experiment.init()

        approach = Approach()
        with (experiment.path / "train.log").open("w") as log_file:
            for x, y_true, y_pred in approach.run():
                metrics = compute_metrics(y_pred, y_true)
                log_file.write(repr(metrics) + "\n")

        approach.model.save(experiment.path / "model.bin")

    experiment.run()
    ```

4. Finally, you can invoke `train.py` in the command line to actually conduct
    the experiment, where component params accept string locators in the form
    of `path.to.module[:factory_name][?[k_0=v_0][;k_n=v_n...]]` with values
    parsed by `json.loads`.

    ```shell
    python train.py 'ours?alpha=0.1' \
        --dataset 'dataset_foo:get_dataset_foo?
            version = "2.0";
            shots = 5;
            # ...
        ' \
        --epochs 500
    ```

5. After calling `experiment.init()`, an experiment directory will be created in
    `experiments/`, to which `experiment.path` will point, and the experiment
    meta will be dumped into `meta.json` in that directory. Extra data can also
    be saved to the experiment directory, as shown in `train.py`, where a log
    file `train.log` holding epoch metrics and a model archive `model.bin` are
    created. This experiment archive can then be loaded to perform extensive
    inspections, such as visualization and further statistical analysis, where
    properties defined on `Approach` will be automatically restored:

    ```python
    # analyze.py

    from dmlx.experiment import Experiment

    experiment = Experiment()

    with experiment.context():
        from approach import Approach


    @experiment.main
    def main(**args):
        print("Loaded args:", args)
        print("Loaded meta:", experiment.meta)

        approach = Approach()
        approach.model.load(experiment.path / "model.bin")

        # Now, `args`, `approach.model`, `approach.dataset` and other properties
        # are all restored, ready for extensive inspections.


    experiment.load("/path/to/the/experiment")
    ```

## Links

- [Repository](https://github.com/huang2002/dmlx)
- [API Reference](https://github.com/huang2002/dmlx/wiki)
- [License (ISC)](https://github.com/huang2002/dmlx/blob/main/LICENSE)
