import pytest

from dmlx.component import Component


def test_parse_locator() -> None:
    path, kwargs = Component.parse_locator('a.b:c?x=0;#y="1";z = "2"')
    assert path == "a.b:c"
    assert kwargs == {"x": 0, "z": "2"}


def test_parse_locator_wo_params() -> None:
    path, kwargs = Component.parse_locator("blah")
    assert path == "blah"
    assert kwargs == {}


def test_parse_locator_with_empty_params() -> None:
    path, kwargs = Component.parse_locator("blah?")
    assert path == "blah"
    assert kwargs == {}


def test_parse_locator_multiline() -> None:
    path, kwargs = Component.parse_locator(
        """
        a.b:c?
            # x = 0;
            y = "1";
            z = [2.0, true];
        """
    )
    assert path == "a.b:c"
    assert kwargs == {"y": "1", "z": [2.0, True]}


def test_load_simple() -> None:
    from test_module.model.foo import Model

    model_component = Component()

    with pytest.raises(RuntimeError):
        model_component.load("test_module.model.foo?threshold=5")

    model = model_component.load("test_module.model.foo:Model?threshold=5")
    assert isinstance(model, Model)
    assert model.threshold == 5
    assert model.predict([4, 5, 6]) == [0.0, 1.0, 1.0]


def test_load_complex() -> None:
    from test_module.model.bar import Model

    model_component = Component(
        module_base="test_module.model",
        default_factory_name="Model",
    )

    @model_component.set_postprocessor
    def postprocess(model: Model) -> Model:
        assert model.threshold == 0.5
        new_model = Model()
        new_model.threshold = 1.0
        return new_model

    model = model_component.load("bar")
    assert isinstance(model, Model)
    assert model.predict([0.1, 1.0, 10.0]) == [0.0, 1.0, 1.0]
