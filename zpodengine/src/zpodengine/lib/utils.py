from prefect import context


def ctx_params():
    return context.get_run_context().parameters


def ctx_param(param):
    return ctx_params()[param]
