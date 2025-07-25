import json
from collections.abc import Callable
from datetime import datetime
from functools import cache, wraps
from pathlib import Path
from secrets import token_hex
from sys import orig_argv
from typing import TYPE_CHECKING, Any, TypedDict, cast

import click

from .docs import COMMAND_DEFINING_DOC, META_FROZEN_DOC

if TYPE_CHECKING:  # pragma: no cover
    from .context import ExperimentContext


class Experiment:
    BASE_DIR: Path = Path("./experiments")
    DEFAULT_NAME_TEMPLATE: str = (
        "{year}/{month:02}/{day:02}/{hour:02}{minute:02}{second:02}-{hex}"
    )
    DEFAULT_META_FILE_PATH: Path | str = "meta.json"
    DEFAULT_META_JSON_OPTIONS: dict[str, Any] = dict(indent=4)

    class NameTemplateVariables(TypedDict):
        year: int
        month: int
        day: int
        hour: int
        minute: int
        second: int
        microsecond: int
        hex: str

    @staticmethod
    def get_name_template_variables(now: datetime) -> NameTemplateVariables:
        return Experiment.NameTemplateVariables(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            second=now.second,
            microsecond=now.microsecond,
            hex=token_hex(4),
        )

    class Meta(TypedDict):
        name: str
        birth: str
        birth_timestamp: float
        orig_argv: list[str]
        args: dict[str, object]

    command: click.Command | None

    __birth: datetime
    __name: str
    __meta_file_path: Path
    __args: dict[str, object] | None
    __meta_frozen: bool
    __meta: Meta | None

    def __init__(
        self,
        name_template: str | None = None,
        *,
        name_template_variables: NameTemplateVariables | None = None,
        meta_file_path: Path | str | None = None,
    ) -> None:
        self.command = None
        self.__birth = datetime.now()
        self.__meta_file_path = Path(meta_file_path or self.DEFAULT_META_FILE_PATH)
        self.__args = None
        self.__meta_frozen = False
        self.__meta = None

        if name_template is None:
            name_template = self.DEFAULT_NAME_TEMPLATE
        if name_template_variables is None:
            name_template_variables = self.get_name_template_variables(self.__birth)
        self.__name = name_template.format_map(name_template_variables)

    @property
    def birth(self) -> datetime:
        """The creation time of the experiment object."""
        return self.__birth

    @property
    def name(self) -> str:
        """Experiment name."""
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        assert not self.__meta_frozen, (
            "Cannot update experiment name now! " + META_FROZEN_DOC
        )
        self.__name = name

    @property
    def meta_file_path(self) -> Path:
        """Path to the meta file, relative to the experiment directory."""
        return Path(self.__meta_file_path)

    @meta_file_path.setter
    def meta_file_path(self, path: Path | str) -> None:
        assert not self.__meta_frozen, (
            "Cannot update meta file path now! " + META_FROZEN_DOC
        )
        self.__meta_file_path = Path(path)

    @property
    def args(self) -> dict[str, object]:
        """Parsed command args."""
        assert self.__args is not None, (
            "Args are unavailable before experiment run or loading! If you are "
            "conducting a new experiment, make sure that command args are only "
            "used after calling `experiment.run()`. If you are loading an existing "
            "experiment, access command args after `experiment.load()`."
        )
        return self.__args

    @property
    @cache
    def path(self) -> Path:
        """Path to the experiment directory."""
        self.__meta_frozen = True
        return self.BASE_DIR / self.__name

    @property
    def meta(self) -> Meta:
        if self.__meta is None:
            self.__meta = self.Meta(
                name=self.__name,
                birth=str(self.__birth),
                birth_timestamp=self.__birth.timestamp(),
                orig_argv=orig_argv,
                args=self.args,
            )
        self.__meta_frozen = True
        return self.__meta

    def dump_meta(self, **json_options: Any) -> Meta:
        """Dump experiment meta to JSON file.

        Returns:
            meta (Experiment.Meta): The dumped meta.
        """
        for key, value in self.DEFAULT_META_JSON_OPTIONS.items():
            json_options.setdefault(key, value)

        with (self.path / self.meta_file_path).open("w") as file:
            json.dump(self.meta, file, **json_options)

        return self.meta

    def init(
        self,
        meta_json_options: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the experiment directory."""
        path = self.path
        path.mkdir(parents=True, exist_ok=False)

        self.dump_meta(**(meta_json_options or {}))

    def main(
        self, *command_args, **command_kwargs
    ) -> Callable[[Callable], click.Command]:
        """Creates the click command and use the decorated function as callback.
        (Additional command arguments and options can be declared with corresponding
        click functions.)

        Returns:
            decorator (Callable[[Callable], click.Command]):
                The decorator for the callback.
        """

        def decorator(callback: Callable) -> click.Command:
            @wraps(callback)
            def wrapper(*args, **kwargs) -> Any:
                assert self.__args is None, "The experiment has been run or loaded!"
                self.__args = kwargs
                return callback(*args, **kwargs)

            click_decorator = click.command(*command_args, **command_kwargs)
            self.command = cast(click.Command, click_decorator(wrapper))
            return self.command

        return decorator

    def param(self, cls: type[click.Parameter], *args, **kwargs) -> property:
        """Create a param property that is to be read from the experiment command.
        (All arguments will be forwarded to the constructor.)

        Returns:
            param (click.Parameter): The created param.
        """

        assert self.command is not None, (
            "Params must be declared after the defining the command! "
            + COMMAND_DEFINING_DOC
        )
        assert self.__args is None, (
            "Params must be declared before experiment run or loading!"
        )
        param = cls(args, **kwargs)
        self.command.params.append(param)

        def getter(_self: Any) -> Any:
            assert self.args is not None, (
                "Params cannot be accessed before experiment run or loading! "
                "If you are conducting a new experiment, make sure that the "
                "params(command arguments or options) are only accessed after "
                "calling `experiment.run()`. If you are loading an existing "
                "experiment, access the params after `experiment.load()`."
            )
            assert param.name is not None, "The param name is unavailable!"
            return self.args[param.name]

        return property(getter)

    def argument(self, *args, **kwargs) -> property:
        """Create an argument property that is to be read from the experiment command.
        (All arguments will be forwarded to `click.Argument()`.)

        Returns:
            argument (click.Argument): The created argument.
        """
        return self.param(click.Argument, *args, **kwargs)

    def option(self, *args, **kwargs) -> property:
        """Create an option property that is to be read from the experiment command.
        (All arguments will be forwarded to `click.Option()`.)

        Returns:
            option (click.Option): The created option.
        """
        return self.param(click.Option, *args, **kwargs)

    def context(self) -> "ExperimentContext":
        """Get an experiment context for the experiment."""
        from .context import ExperimentContext

        return ExperimentContext(self)

    def run(self, *args, **kwargs) -> object:
        """Run experiment command. (All arguments will be passed to the command.)

        Returns:
            return_value (object): The value returned by the command.
        """
        assert self.command is not None, (
            "The experiment command has not been defined!" + COMMAND_DEFINING_DOC
        )

        self.__meta_frozen = True

        with self.context():
            return self.command(*args, **kwargs)

    def load(self, **json_options: Any) -> None:
        """Load the experiment from an existing archive."""
        assert self.__args is None, "The experiment has already been run or loaded!"

        with (self.path / self.meta_file_path).open("r") as file:
            meta = cast(Experiment.Meta, json.load(file, **json_options))

        self.__meta = meta
        self.__birth = datetime.fromtimestamp(meta["birth_timestamp"])
        self.__args = meta["args"]
