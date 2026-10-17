# Contributing

Use Python 3.10+ and work in the Python environment used by ComfyUI when testing nodes.

```sh
python -m unittest discover -s tests -v
python -m compileall -q __init__.py client.py nodes.py
```

The client tests use mocks and never spend Forma credits. To test node registration, install this checkout in an isolated ComfyUI instance and verify `FormaSeedreamImage` and `FormaPrunaAnimate` in `/object_info`. Load the editor workflow and check its controls and connections before changing the JSON.

Keep node class names and the `FORMA_IMAGE` connection stable. They are part of saved workflows. Changes to billing, recovery IDs, or credentials need regression tests. Do not make a live paid inference call as part of CI.

Update CHANGELOG.md for user-visible changes and increment the semantic version in pyproject.toml for releases. Use the existing root `__init__.py` entry point; this is a ComfyUI custom-node folder, not a standalone application.

## Registry publication

GitHub installation works without a Comfy Registry account. Before publishing there, create or verify the owner's publisher, set its actual `PublisherId` in `[tool.comfy]`, review the packaged files, and publish deliberately. No automatic publication or registry token is configured in this repository.

See the official [publishing guide](https://docs.comfy.org/registry/publishing) and [metadata specification](https://docs.comfy.org/registry/specifications). `.comfyignore` excludes development-only files from registry archives.
