import logging

from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from zpodapi.lib import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 5 * 60  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init() -> None:
    try:
        with database.get_session_ctx() as session:
            session.execute("SELECT 1")
    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    logger.info("Waiting for Database")
    init()
    logger.info("Database Ready")


if __name__ == "__main__":
    main()
