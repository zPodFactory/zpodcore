import time
from datetime import datetime

from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.nsx import NsxClient
from zpodengine.lib import database

SEGMENT_MAX_WAIT_FOR_EMPTY = 120
SEGMENT_WAIT_BETWEEN_TRIES = 5


@task
def nsx_project_destroy(project_id: str, endpoint_id: int):
    print(f"Destroy NSX Project: {project_id}")

    with database.get_session_ctx() as session:
        endpoint = session.get(M.Endpoint, endpoint_id)
        with NsxProjectDestroy(project_id=project_id, endpoint=endpoint) as npd:
            npd()


class NsxProjectDestroy:
    def __init__(self, project_id: str, endpoint: int, orgid="default") -> None:
        self.nsx = NsxClient(endpoint)
        self.project_id = project_id
        self.project_path = f"/orgs/{orgid}/projects/{project_id}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.nsx.close()

    def __call__(self):
        segments = self.instance_project_segments()
        for segment in segments:
            self.wait_for_segment_to_be_evacuted(segment)

        # TODO: Remove when bug is fixed -
        # https://bugzilla.eng.vmware.com/show_bug.cgi?id=3218007
        # Delete all segments manually
        for segment in segments:
            self.delete_segment_binding_map(segment)

        self.delete_project()

    def instance_project_segments(self):
        return self.nsx.search(
            resource_type="Segment",
            parent_path=fmt(f"{self.project_path}/infra"),
        )

    @property
    def segments(self):
        return (
            self.nsx.get(f"/policy/api/v1{self.project_path}/infra/segments/")
            .safejson()
            .get("results", [])
        )

    def wait_for_segment_to_be_evacuted(self, segment):
        start = datetime.now()
        while (datetime.now() - start).seconds < SEGMENT_MAX_WAIT_FOR_EMPTY:
            ports = self.nsx.get(f"/policy/api/v1{segment['path']}/ports").safejson()
            if ports["result_count"] == 0:
                print(
                    f"Segment ({segment['display_name']}) has no ports/"
                    "interfaces attached. Continuing."
                )
                break
            print(
                f"Segment ({segment['display_name']}) has ports/"
                "interfaces attached. Waiting..."
            )
            time.sleep(SEGMENT_WAIT_BETWEEN_TRIES)
        else:
            raise ValueError("Failed: Segment has connected ports / interfaces.")

    def delete_segment_binding_map(self, segment):
        print(f"Gathering Segment: {segment['id']} Binding Map")
        binding_maps = self.nsx.get(
            url=(
                f"/policy/api/v1{segment['path']}"
                f"/segment-discovery-profile-binding-maps"
            )
        ).results()

        for binding_map in binding_maps:
            print(f"Delete Segment Binding Map: {binding_map['id']}")
            self.nsx.delete(url=(f"/policy/api/v1{binding_map['path']}"))

    def delete_project(self):
        print(f"Delete Project: {self.project_id}")
        self.nsx.patch(
            url="/policy/api/v1/org-root",
            json=dict(
                resource_type="OrgRoot",
                children=[
                    dict(
                        resource_type="ChildResourceReference",
                        id="default",
                        target_type="Org",
                        children=[
                            dict(
                                Project=dict(
                                    id=self.project_id,
                                    resource_type="Project",
                                ),
                                resource_type="ChildProject",
                                marked_for_delete=True,
                            )
                        ],
                    )
                ],
            ),
        )


def fmt(txt):
    return txt.replace("/", "\\/")


if __name__ == "__main__":
    nsx_project_destroy.fn("zpodkv-Demo-enet-project", 1)
