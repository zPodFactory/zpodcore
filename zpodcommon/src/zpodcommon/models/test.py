from datetime import datetime

from sqlmodel import select

from zpodapi.lib import database
from zpodcommon import models as M

# with database.get_session_ctx() as session:
#     endpoint = M.Endpoint()
#     session.add(endpoint)
#     zpod = M.Instance(
#         name="test3",
#         creation_date=datetime.now(),
#         last_modified_date=datetime.now(),
#         components=[
#             M.InstanceComponent(component_uid="vcd-10.2"),
#         ],
#         endpoint_id=1,
#         permissions=[
#             M.InstancePermission(
#                 name="owner",
#                 permission="zpodadmin",
#                 user_links=[
#                     M.InstancePermissionUser(user_id=1),
#                 ],
#             )
#         ],
#     )
#     session.add(zpod)
#     session.commit()
#     session.refresh(zpod)
#     print("ZPOD", zpod)
#     print("COMPONENTS", zpod.components)
#     print("COMPONENTS", zpod.components[0].component)

with database.get_session_ctx() as session:
    user1 = session.exec(select(M.User).where(M.User.id == 1)).one()
    user2 = session.exec(select(M.User).where(M.User.id == 2)).one()

    pg = M.PermissionGroup(name="Team", users=[user2])
    session.add(pg)
    session.commit()
    session.refresh(pg)

    zpod = M.Instance(
        name="test1",
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
    )
    session.add(zpod)
    session.commit()
    session.refresh(zpod)
    print("ZPOD", zpod)
    print("COMPONENTS", zpod.components)
    print("COMPONENTS", zpod.components[0].component)


# # with database.get_session_ctx() as session:
#     result = session.exec(select(M.Zpod).where(M.Zpod.name == "test"))
#     zpod = result.one()

#     print(f"\n\n{zpod=}")
#     print(f"\n\n{zpod.components}")
#     print(f"\n\n{zpod.endpoint}")
#     print(f"\n\n{zpod.networks}")

#     # session.delete(zpod)
#     # session.commit()
