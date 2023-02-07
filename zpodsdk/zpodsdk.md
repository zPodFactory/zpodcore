# zPod SDK

This is the self-generated zPod SDK.

## Getting Started

You will be able to generate the zpodsdk python bindings by running the following command:

```bash
just zpodsdk-build
```

This will generate the openapi.json file and then build the python bindings using a dedicated container configured with the correct tooling. (zpodsdk_builder)

Sample output:

```bash
zpodcore on main [?⇡] via 🐳 desktop-linux
❯ just zpodsdk-build
docker exec -t zpodapi python scripts/openapi/generate_openapi_json.py
Generating openapi.json...
mv -vf scripts/openapi/openapi.json zpodsdk_builder/openapi.json
scripts/openapi/openapi.json -> zpodsdk_builder/openapi.json
docker build -t zpodfactory/zpodsdk_builder zpodsdk_builder
[+] Building 34.4s (19/19) FINISHED
...
...
...
docker run -v "$(pwd)/zpodsdk:/zpodcore/zpodsdk" zpodfactory/zpodsdk_builder
Generating zpodsdk

zpodcore on main [?⇡] via 🐳 desktop-linux
❯ ll zpodsdk/
drwxr-xr-x    - tsugliani  3 Jan 17:16 zpod
.rwxr-xr-x  633 tsugliani  3 Jan 17:16 pyproject.toml
.rw-r--r-- 1.1k tsugliani  3 Jan 17:19 README.md
```
