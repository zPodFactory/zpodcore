from datetime import datetime

from sqlmodel import select

from zpodapi.lib import database
from zpodcommon import models as M

with database.get_session_ctx() as session:
    endpoint = M.Endpoint()
    session.add(endpoint)
    zpod = M.Instance(
        name="test2",
        creation_date=datetime.now(),
        last_modified_date=datetime.now(),
        components=[
            M.InstanceComponent(component_uid="vcd-10.2"),
        ],
        endpoint_id=1,
        permissions=[
            M.InstancePermission(
                name="owner",
                permission="zpodadmin",
                users=[
                    M.InstancePermissionUser(user_id=1),
                ],
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
