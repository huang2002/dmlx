from functools import cache

import click

from .context import get_current_experiment


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


def component(locator_source: property | str, *args, **kwargs) -> property:
    """Create a component property that acts as a component factory.
    (The extra args are passed to `Component` to create the underlying factory.)
    """
    from .component import Component

    component_factory = Component(*args, **kwargs)

    @cache
    def component_getter(self) -> object:
        if isinstance(locator_source, property):
            assert locator_source.fget is not None, (
                "Cannot get the component locator from the given property."
            )
            locator = locator_source.fget(self)
        else:
            locator = getattr(self, locator_source)
        return component_factory(locator)

    return property(component_getter)
