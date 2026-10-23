from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodStorageStep")


@_attrs_define
class ZpodStorageStep:
    """
    Attributes:
        status (str):
        step (str):
        target (str):
        command (None | str | Unset):
        detail (str | Unset):  Default: ''.
        exit_code (int | None | Unset):
        output (None | str | Unset):
    """

    status: str
    step: str
    target: str
    command: None | str | Unset = UNSET
    detail: str | Unset = ""
    exit_code: int | None | Unset = UNSET
    output: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        step = self.step

        target = self.target

        command: None | str | Unset
        if isinstance(self.command, Unset):
            command = UNSET
        else:
            command = self.command

        detail = self.detail

        exit_code: int | None | Unset
        if isinstance(self.exit_code, Unset):
            exit_code = UNSET
        else:
            exit_code = self.exit_code

        output: None | str | Unset
        if isinstance(self.output, Unset):
            output = UNSET
        else:
            output = self.output

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "step": step,
                "target": target,
            }
        )
        if command is not UNSET:
            field_dict["command"] = command
        if detail is not UNSET:
            field_dict["detail"] = detail
        if exit_code is not UNSET:
            field_dict["exit_code"] = exit_code
        if output is not UNSET:
            field_dict["output"] = output

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = d.pop("status")

        step = d.pop("step")

        target = d.pop("target")

        def _parse_command(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        command = _parse_command(d.pop("command", UNSET))

        detail = d.pop("detail", UNSET)

        def _parse_exit_code(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        exit_code = _parse_exit_code(d.pop("exit_code", UNSET))

        def _parse_output(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output = _parse_output(d.pop("output", UNSET))

        zpod_storage_step = cls(
            status=status,
            step=step,
            target=target,
            command=command,
            detail=detail,
            exit_code=exit_code,
            output=output,
        )

        zpod_storage_step.additional_properties = d
        return zpod_storage_step

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
