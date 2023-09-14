from prefect import flow


@flow
def flow_init():
    print("Init")


if __name__ == "__main__":
    flow_init()
