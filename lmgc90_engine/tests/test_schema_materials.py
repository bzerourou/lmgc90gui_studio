from lmgc90_engine.schema import materials


_FALLBACK_SCHEMA = {
    "RIGID": (),
    "ELAS": (
        ("young", 210.0, "float"),
        ("anisotropy", "isotropic", "str"),
        ("young1", 200.0, "float"),
    ),
}
_FALLBACK_CHOICES = {"anisotropy": ("isotropic", "orthotropic")}
_FALLBACK_OPTIONS = {"RIGID": ("density",), "ELAS": ("young",)}


def test_material_schema_uses_runtime_fields_and_fallback_metadata(monkeypatch):
    monkeypatch.setattr(materials, "load_compatibility_catalogs", lambda: {
        "bulkBehavOptions": {
            "RIGID": ["density"],
            "ELAS": ["density", "young", "runtime_field"],
            "JOINT_ELAS": ["density", "stiffnesses", "elas"],
        },
        "checkBulkBehavOptions": {
            "JOINT_ELAS": {
                "root": "elas",
                "children": [
                    {"root": "ELAS", "children": []},
                    {"root": "VISCO_ELAS", "children": []},
                ],
            },
        },
    })
    monkeypatch.setattr(
        materials, "compatibility_catalog_source", lambda: "INTROSPECTION",
    )

    schema = materials.material_schema_catalog(
        _FALLBACK_SCHEMA,
        _FALLBACK_CHOICES,
        _FALLBACK_OPTIONS,
    )

    assert schema["source"] == "INTROSPECTION"
    assert schema["types"] == ("RIGID", "ELAS", "JOINT_ELAS")
    assert schema["properties"]["ELAS"] == (
        ("young", 210.0, "float"),
        ("runtime_field", None, "auto"),
        ("young1", 200.0, "float"),
    )
    assert "JOINT_ELAS" in schema["types"]
    assert schema["properties"]["JOINT_ELAS"] == (
        ("stiffnesses", None, "auto"),
        ("elas", None, "auto"),
    )
    assert schema["choices_by_type"]["JOINT_ELAS"]["elas"] == (
        "ELAS", "VISCO_ELAS",
    )
    assert schema["choices"] == _FALLBACK_CHOICES


def test_material_schema_uses_core_fallback_without_runtime(monkeypatch):
    monkeypatch.setattr(materials, "load_compatibility_catalogs", lambda: {})

    schema = materials.material_schema_catalog(
        _FALLBACK_SCHEMA,
        _FALLBACK_CHOICES,
        _FALLBACK_OPTIONS,
    )

    assert schema["source"] == "FALLBACK"
    assert schema["types"] == ("RIGID", "ELAS")
    assert schema["properties"] == _FALLBACK_SCHEMA


def test_material_schema_exposes_runtime_only_material_types(monkeypatch):
    monkeypatch.setattr(materials, "load_compatibility_catalogs", lambda: {
        "bulkBehavOptions": {"THERMO_RIGID": ["density"]},
    })

    schema = materials.material_schema_catalog(
        _FALLBACK_SCHEMA,
        _FALLBACK_CHOICES,
        _FALLBACK_OPTIONS,
    )

    assert schema["types"] == ("THERMO_RIGID",)
    assert schema["properties"]["THERMO_RIGID"] == ()
