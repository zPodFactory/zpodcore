from prefect import flow, task
from sqlmodel import select

from zpodcommon import models as M
from zpodengine.lib import database


@task
def get_users():
    with database.get_session_ctx() as session:
        print(session.exec(select(M.User)).all())


@flow(log_prints=True)
def flow_db_sample():
    get_users()


if __name__ == "__main__":
    print(flow_db_sample())
