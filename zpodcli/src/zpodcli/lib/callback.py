from rich import print

from zpodcli.lib.config import config


def isauthenticated():
    cfg = config()
    if cfg.ismissing():
        print(
            "Please connect to a zPod Server first using the following command:\n\n",
            "[bold]zcli connect --server <xxx> --token <xxx>.[/bold]\n",
        )
        exit(0)

    # Configuration is done, but we need to check if the token is valid
    # TODO: check if token is valid
    return True
