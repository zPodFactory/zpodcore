from datetime import datetime

from sqlmodel import select

from zpodapi.lib import database
from zpodcommon import models as M

with database.get_session_ctx() as session:
    user1 = session.exec(select(M.User).where(M.User.id == 1)).one()
    user2 = session.exec(select(M.User).where(M.User.id == 2)).one()

    pg = M.PermissionGroup(name="Team", users=[user2])
    session.add(pg)
    session.commit()
    session.refresh(pg)

    instance = M.Instance(
        name="test2",
        creation_date=datetime.now(),
        last_modified_date=datetime.now(),
        components=[
            M.InstanceComponent(component_uid="vcd-10.2"),
        ],
        endpoint=M.Endpoint(),
        permissions=[
            M.InstancePermission(
                name="owner",
                permission="zpodadmin",
                users=[user1],
                groups=[pg],
            )
        ],
        networks=[M.InstanceNetwork(cidr="192.168.0.0/24")],
        features=[M.InstanceFeature(data={"feature": "one"})],
    )
    session.add(instance)
    session.commit()
    session.refresh(instance)
    print("ZPOD", instance)


# # with database.get_session_ctx() as session:
#     instance = session.exec(select(M.Instance).where(M.Instance.name == "test1")).one()

#     print(f"\n\n{instance=}")
#     print(f"\n\n{instance.components}")
#     print(f"\n\n{instance.endpoint}")
#     print(f"\n\n{instance.networks}")


# with database.get_session_ctx() as session:
#     instance = session.exec(select(M.Instance).where(M.Instance.name == "test1")).one()
#     session.delete(instance)
#     session.commit()
