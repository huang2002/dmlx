import json
from collections.abc import Callable
from dataclasses import dataclass
from pkgutil import resolve_name
from types import ModuleType
from typing import Any


@dataclass(kw_only=True)
class Component:
    @staticmethod
    def parse_locator(locator: str) -> tuple[str, dict[str, object]]:
        """Parse a component locator string into path and parameters.

        - Format: `<path>?<key_0>=<value_0>;<key_1>=<value_1>;...`
        - Excessive whitespace characters will be ignored
        - Pairs with keys starting with "#" will also be ignored
        - `<key_*>` can be any string
        - `<value_*>` will be converted by `json.loads()`

        Returns:
            A tuple of (path, params).
        """
        path, _, params_str = locator.partition("?")
        path = path.strip()

        params: dict[str, object] = {}
        if params_str:
            for param_str in params_str.split(";"):
                param_str = param_str.strip()
                if not param_str or param_str.startswith("#"):
                    continue
                key, value = param_str.split("=", 1)
                params[key.strip()] = json.loads(value)

        return path, params

    module_base: str = ""
    default_factory_name: str | None = None
    postprocessor: Callable[[Any], object] | None = None

    def load(self, locator: str) -> object:
        """Load the component according to the factory locator. (The locator
        string will be passed to `Component.parse_locator()` to extract factory
        path and parameters.)

        Returns:
            component (object): The return value of the factory.
        """
        factory_path, factory_kwargs = self.parse_locator(locator)
        if self.module_base:
            factory_path = self.module_base + "." + factory_path

        factory = resolve_name(factory_path)
        if isinstance(factory, ModuleType):
            if not self.default_factory_name:
                raise RuntimeError("Factory name is neither provided nor set!")
            factory = getattr(factory, self.default_factory_name)
        component = factory(**factory_kwargs)

        if self.postprocessor:
            return self.postprocessor(component)
        else:
            return component

    def set_postprocessor(
        self, postprocessor: Callable[[Any], object]
    ) -> Callable[[Any], object]:
        """Set `component.postprocessor`.
        (This is a helper method to be used as a decorator.)
        """
        self.postprocessor = postprocessor
        return postprocessor
