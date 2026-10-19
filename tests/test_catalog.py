import importlib
import json
import sys
import types
import unittest
from pathlib import Path

PACKAGE = "forma_catalog_test"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(Path(__file__).parents[1])]
sys.modules[PACKAGE] = package
catalog = importlib.import_module(PACKAGE + ".catalog")
FormaError = importlib.import_module(PACKAGE + ".client").FormaError


def selection(model, workflow):
    values = {"model": model["id"]}
    for field in catalog.model_fields(model, workflow):
        key = catalog.field_id(field)
        if field.get("media"):
            values[key] = {key: "Reference", "value": "https://media.example/reference.png"} if field.get("required") else {key: "None"}
        elif field["name"] == "prompt":
            values[key] = "A quiet coastline"
        elif "default" in field:
            values[key] = json.dumps(field["default"]) if field["type"] == "array" else field["default"]
        elif field["type"] in ("integer", "float", "number", "boolean"):
            values[key] = {key: "Default"}
        else:
            values[key] = "[]" if field["type"] == "array" else ""
    return {"workflow": workflow, "model": values}


class CatalogTests(unittest.TestCase):
    def test_every_catalog_model_and_workflow_has_valid_defaults(self):
        self.assertEqual(len(catalog.MODELS), 39)
        covered = set()
        for model in catalog.MODELS.values():
            modes = model["workflows"] + (["first-last-frame-to-video"] if model["id"] in catalog.END_FRAMES else [])
            for workflow in modes:
                with self.subTest(model=model["id"], workflow=workflow):
                    selected = selection(model, workflow)
                    actual, mode, values = catalog.selected_model(model["kind"], selected)
                    inputs, prompt = catalog.prepare_inputs(actual, mode, values)
                    self.assertTrue(prompt)
                    self.assertFalse(catalog.HIDDEN_FIELDS.intersection(inputs))
                    covered.add(mode)
        self.assertEqual(covered, set(sum(catalog.WORKFLOWS.values(), [])))

    def test_incompatible_model_workflow_and_unknown_fields_are_rejected(self):
        model = catalog.MODELS["p-video"]
        selected = selection(model, "image-to-video")
        selected["workflow"] = "reference-to-video"
        with self.assertRaises(FormaError):
            catalog.selected_model("video", selected)
        with self.assertRaises(FormaError):
            catalog.selected_model("image", selection(model, "image-to-video"))
        selected = selection(model, "image-to-video")
        selected["model"]["made_up_option"] = 1
        with self.assertRaises(FormaError):
            catalog.prepare_inputs(model, "image-to-video", selected["model"])

    def test_conditioning_required_for_i2i_i2v_a2v_and_first_last_frame(self):
        for mid, mode, field in [("z-image-turbo", "image-to-image", "image"), ("p-video", "image-to-video", "image"),
                                 ("p-video", "audio-to-video", "audio"), ("minimax-hailuo-02-std", "first-last-frame-to-video", "end_image")]:
            model = catalog.MODELS[mid]
            values = selection(model, mode)["model"]
            values[field] = {field: "None"}
            with self.subTest(mode=mode), self.assertRaises(FormaError):
                catalog.prepare_inputs(model, mode, values)

    def test_reference_limits_and_secret_urls_are_rejected(self):
        model = catalog.MODELS["kling-video-o1-r2v"]
        values = selection(model, "reference-to-video")["model"]
        for value in ("https://user:secret@example.com/a.png", "file:///etc/passwd", "\n".join(["https://example.com/a.png"] * 11)):
            values["images"] = {"images": "Reference", "value": value}
            with self.assertRaises(FormaError):
                catalog.prepare_inputs(model, "reference-to-video", values)

    def test_scalar_ranges_choices_and_optional_omission(self):
        model = catalog.MODELS["p-video"]
        for field, value in [("duration", 0), ("resolution", "made-up"), ("duration", float("nan")), ("draft", "false")]:
            values = selection(model, "text-to-video")["model"]
            values[field] = value
            with self.assertRaises(FormaError):
                catalog.prepare_inputs(model, "text-to-video", values)
        model = catalog.MODELS["fal-flux-2-klein-9b"]
        inputs, _ = catalog.prepare_inputs(model, "text-to-image", selection(model, "text-to-image")["model"])
        self.assertNotIn("seed", inputs)

    def test_lora_json_is_parsed_and_bounded(self):
        model = catalog.MODELS["qwen-image-t2i-lora"]
        field = next(f for f in model["fields"] if f["type"] == "array" and not f.get("media"))
        values = selection(model, "text-to-image")["model"]
        values[field["name"]] = '[{"path":"https://example.com/lora.safetensors","scale":0.8}]'
        inputs, _ = catalog.prepare_inputs(model, "text-to-image", values)
        self.assertEqual(inputs[field["name"]][0]["scale"], 0.8)
        values[field["name"]] = '[{"path":"https://example.com/lora.safetensors","scale":3}]'
        with self.assertRaises(FormaError):
            catalog.prepare_inputs(model, "text-to-image", values)
