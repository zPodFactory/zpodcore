"""Rendering of a component's deploy inputs from its library JSON.

- ``component_deploy_govc_spec``: the govc import options, rendered as one Jinja
  template (``render_deploy_spec``).
- ``component_deploy_extra_config``: VMX ``guestinfo.*`` keys set on the VM before
  its first power-on (``render_extra_config``). The guest reads them at boot:
  cloud-init's VMware datasource, Ignition/Afterburn, Talos.

An extra config value is either a string, rendered with Jinja, or a structured
value whose strings are rendered with Jinja, then serialised and encoded::

    "guestinfo.metadata": {
        "format": "yaml",           # yaml | json | cloud-config
        "encoding": "base64",       # base64 (default) | gzip+base64 | none
        "content": {"instance-id": "{{zpod_hostname}}", ...}
    }

That sets ``guestinfo.metadata`` and ``guestinfo.metadata.encoding``. Inside
``content``, ``{"lines": [...]}`` becomes ``{"source": "data:;base64,..."}``, so a
file embedded in an Ignition config is written line by line.
"""

import base64
import gzip
import json

import yaml
from jinja2 import Environment, StrictUndefined

EXTRA_CONFIG_PREFIX = "guestinfo."
FORMATS = ("yaml", "json", "cloud-config")
ENCODINGS = ("base64", "gzip+base64", "none")
STRUCTURED_FIELDS = {"format", "encoding", "content"}


def _b64(value: str | bytes) -> str:
    data = value.encode() if isinstance(value, str) else value
    return base64.b64encode(data).decode()


# Deploy spec templates can base64 a value with {% filter b64encode %}...{% endfilter %}.
_spec_env = Environment()
_spec_env.filters["b64encode"] = _b64

# Extra config values fail on an unknown variable instead of rendering it empty:
# a guest booted with a blank IP or key is harder to diagnose than a failed deploy.
_extra_env = Environment(undefined=StrictUndefined)
_extra_env.filters["b64encode"] = _b64


class ExtraConfigError(ValueError):
    """component_deploy_extra_config is not valid."""


def render_deploy_spec(spec: dict, **variables) -> dict:
    """Render the Jinja placeholders of a component deploy spec."""
    return json.loads(_spec_env.from_string(json.dumps(spec)).render(**variables))


def _render_content(node, variables: dict):
    """Render every string of a structured value; numbers and booleans stay as is."""
    if isinstance(node, str):
        return _extra_env.from_string(node).render(**variables)
    if isinstance(node, list):
        return [_render_content(item, variables) for item in node]
    if isinstance(node, dict):
        if set(node) == {"lines"} and isinstance(node["lines"], list):
            text = "".join(
                f"{_render_content(line, variables)}\n" for line in node["lines"]
            )
            return {"source": f"data:;base64,{_b64(text)}"}
        return {key: _render_content(value, variables) for key, value in node.items()}
    return node


def _serialise(content, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(content, separators=(",", ":"))
    text = yaml.safe_dump(content, sort_keys=False, default_flow_style=False)
    return f"#cloud-config\n{text}" if fmt == "cloud-config" else text


def _encode(text: str, encoding: str) -> str:
    if encoding == "base64":
        return _b64(text)
    if encoding == "gzip+base64":
        return _b64(gzip.compress(text.encode(), mtime=0))
    return text


def _render_structured(key: str, value: dict, variables: dict) -> tuple[str, str]:
    """(encoded value, encoding) of a structured extra config value."""
    if unknown := set(value) - STRUCTURED_FIELDS:
        raise ExtraConfigError(f"{key}: unknown field(s) {', '.join(sorted(unknown))}")
    if "content" not in value:
        raise ExtraConfigError(f"{key}: a structured value needs a content")
    fmt = value.get("format")
    if fmt not in FORMATS:
        raise ExtraConfigError(f"{key}: format must be one of {', '.join(FORMATS)}")
    encoding = value.get("encoding", "base64")
    if encoding not in ENCODINGS:
        raise ExtraConfigError(f"{key}: encoding must be one of {', '.join(ENCODINGS)}")
    text = _serialise(_render_content(value["content"], variables), fmt)
    return _encode(text, encoding), encoding


def render_extra_config(extra_config: dict | None, **variables) -> dict[str, str]:
    """The VMX keys and values to set, from component_deploy_extra_config.

    Raises ExtraConfigError on a key outside guestinfo.*, a malformed value or an
    unknown variable, before anything is deployed.
    """
    if not extra_config:
        return {}
    if not isinstance(extra_config, dict):
        raise ExtraConfigError("component_deploy_extra_config must be an object")
    out: dict[str, str] = {}
    encodings: dict[str, str] = {}
    try:
        for key, value in extra_config.items():
            if not key.startswith(EXTRA_CONFIG_PREFIX) or key == EXTRA_CONFIG_PREFIX:
                raise ExtraConfigError(
                    f"{key}: only {EXTRA_CONFIG_PREFIX}* keys can be set"
                )
            if isinstance(value, str):
                out[key] = _extra_env.from_string(value).render(**variables)
            elif isinstance(value, dict):
                out[key], encoding = _render_structured(key, value, variables)
                if encoding != "none":
                    encodings[f"{key}.encoding"] = encoding
            else:
                raise ExtraConfigError(
                    f"{key}: the value must be a string or an object"
                )
    except ExtraConfigError:
        raise
    except Exception as e:  # Jinja syntax errors, undefined variables
        raise ExtraConfigError(f"{key}: {e}") from e
    for key, encoding in encodings.items():
        if out.get(key, encoding) != encoding:
            raise ExtraConfigError(
                f"{key} is set to {out[key]!r} but the value is {encoding}-encoded"
            )
        out[key] = encoding
    return out
