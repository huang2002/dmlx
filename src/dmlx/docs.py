from inspect import cleandoc

COMMAND_DEFINING_DOC = cleandoc(
    """
    Consider defining the experiment command using the `@experiment.main()` decorator:

    ```python
    @experiment.main()
    def main(**args): ...
    ```
    """
)

META_FROZEN_DOC = (
    "The experiment meta has been frozen, which means its path has been accessed, "
    "or its meta has been accessed, or it has started running, or it has been "
    "loaded from an existing archive. If you want to change any field of the "
    "experiment meta, do it before any of the above."
)
