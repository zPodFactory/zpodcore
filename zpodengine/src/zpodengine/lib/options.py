def task_namer(name):
    return dict(name=name, task_run_name=name)


def task_options_setup(*, prefix="", **default_kwargs):
    def inner(*, name, **kwargs):
        return default_kwargs | task_namer(f"{prefix}: {name}") | kwargs

    return inner
