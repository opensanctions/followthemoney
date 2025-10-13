def load_entry_points() -> None:
    from importlib.metadata import entry_points

    for ep in entry_points().select(group="followthemoney.cli"):
        ep.load()


load_entry_points()
