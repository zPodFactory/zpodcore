from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.zpod_storage_operation_after_type_0 import (
        ZpodStorageOperationAfterType0,
    )
    from ..models.zpod_storage_operation_before_type_0 import (
        ZpodStorageOperationBeforeType0,
    )
    from ..models.zpod_storage_step import ZpodStorageStep
    from ..models.zpod_storage_view import ZpodStorageView


T = TypeVar("T", bound="ZpodStorageOperation")


@_attrs_define
class ZpodStorageOperation:
    """zboxapi's answer to create, adopt, grow and delete: the step table.

    Attributes:
        dry_run (bool):
        name (str):
        operation (str):
        after (None | Unset | ZpodStorageOperationAfterType0):
        before (None | Unset | ZpodStorageOperationBeforeType0):
        changed (bool | None | Unset):
        disk_state (None | str | Unset):
        rollback (list[ZpodStorageStep] | Unset):
        steps (list[ZpodStorageStep] | Unset):
        storage (None | Unset | ZpodStorageView):
    """

    dry_run: bool
    name: str
    operation: str
    after: None | Unset | ZpodStorageOperationAfterType0 = UNSET
    before: None | Unset | ZpodStorageOperationBeforeType0 = UNSET
    changed: bool | None | Unset = UNSET
    disk_state: None | str | Unset = UNSET
    rollback: list[ZpodStorageStep] | Unset = UNSET
    steps: list[ZpodStorageStep] | Unset = UNSET
    storage: None | Unset | ZpodStorageView = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.zpod_storage_operation_after_type_0 import (
            ZpodStorageOperationAfterType0,
        )
        from ..models.zpod_storage_operation_before_type_0 import (
            ZpodStorageOperationBeforeType0,
        )
        from ..models.zpod_storage_view import ZpodStorageView

        dry_run = self.dry_run

        name = self.name

        operation = self.operation

        after: dict[str, Any] | None | Unset
        if isinstance(self.after, Unset):
            after = UNSET
        elif isinstance(self.after, ZpodStorageOperationAfterType0):
            after = self.after.to_dict()
        else:
            after = self.after

        before: dict[str, Any] | None | Unset
        if isinstance(self.before, Unset):
            before = UNSET
        elif isinstance(self.before, ZpodStorageOperationBeforeType0):
            before = self.before.to_dict()
        else:
            before = self.before

        changed: bool | None | Unset
        if isinstance(self.changed, Unset):
            changed = UNSET
        else:
            changed = self.changed

        disk_state: None | str | Unset
        if isinstance(self.disk_state, Unset):
            disk_state = UNSET
        else:
            disk_state = self.disk_state

        rollback: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.rollback, Unset):
            rollback = []
            for rollback_item_data in self.rollback:
                rollback_item = rollback_item_data.to_dict()
                rollback.append(rollback_item)

        steps: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.steps, Unset):
            steps = []
            for steps_item_data in self.steps:
                steps_item = steps_item_data.to_dict()
                steps.append(steps_item)

        storage: dict[str, Any] | None | Unset
        if isinstance(self.storage, Unset):
            storage = UNSET
        elif isinstance(self.storage, ZpodStorageView):
            storage = self.storage.to_dict()
        else:
            storage = self.storage

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dry_run": dry_run,
                "name": name,
                "operation": operation,
            }
        )
        if after is not UNSET:
            field_dict["after"] = after
        if before is not UNSET:
            field_dict["before"] = before
        if changed is not UNSET:
            field_dict["changed"] = changed
        if disk_state is not UNSET:
            field_dict["disk_state"] = disk_state
        if rollback is not UNSET:
            field_dict["rollback"] = rollback
        if steps is not UNSET:
            field_dict["steps"] = steps
        if storage is not UNSET:
            field_dict["storage"] = storage

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.zpod_storage_operation_after_type_0 import (
            ZpodStorageOperationAfterType0,
        )
        from ..models.zpod_storage_operation_before_type_0 import (
            ZpodStorageOperationBeforeType0,
        )
        from ..models.zpod_storage_step import ZpodStorageStep
        from ..models.zpod_storage_view import ZpodStorageView

        d = dict(src_dict)
        dry_run = d.pop("dry_run")

        name = d.pop("name")

        operation = d.pop("operation")

        def _parse_after(data: object) -> None | Unset | ZpodStorageOperationAfterType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                after_type_0 = ZpodStorageOperationAfterType0.from_dict(data)

                return after_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | ZpodStorageOperationAfterType0, data)

        after = _parse_after(d.pop("after", UNSET))

        def _parse_before(
            data: object,
        ) -> None | Unset | ZpodStorageOperationBeforeType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                before_type_0 = ZpodStorageOperationBeforeType0.from_dict(data)

                return before_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | ZpodStorageOperationBeforeType0, data)

        before = _parse_before(d.pop("before", UNSET))

        def _parse_changed(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        changed = _parse_changed(d.pop("changed", UNSET))

        def _parse_disk_state(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        disk_state = _parse_disk_state(d.pop("disk_state", UNSET))

        _rollback = d.pop("rollback", UNSET)
        rollback: list[ZpodStorageStep] | Unset = UNSET
        if _rollback is not UNSET:
            rollback = []
            for rollback_item_data in _rollback:
                rollback_item = ZpodStorageStep.from_dict(rollback_item_data)

                rollback.append(rollback_item)

        _steps = d.pop("steps", UNSET)
        steps: list[ZpodStorageStep] | Unset = UNSET
        if _steps is not UNSET:
            steps = []
            for steps_item_data in _steps:
                steps_item = ZpodStorageStep.from_dict(steps_item_data)

                steps.append(steps_item)

        def _parse_storage(data: object) -> None | Unset | ZpodStorageView:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                storage_type_0 = ZpodStorageView.from_dict(data)

                return storage_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | ZpodStorageView, data)

        storage = _parse_storage(d.pop("storage", UNSET))

        zpod_storage_operation = cls(
            dry_run=dry_run,
            name=name,
            operation=operation,
            after=after,
            before=before,
            changed=changed,
            disk_state=disk_state,
            rollback=rollback,
            steps=steps,
            storage=storage,
        )

        zpod_storage_operation.additional_properties = d
        return zpod_storage_operation

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
