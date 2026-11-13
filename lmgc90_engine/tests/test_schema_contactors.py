from lmgc90_engine.schema import contactors


def test_contactor_schema_uses_runtime_catalogs_and_preserves_fallbacks(monkeypatch):
    monkeypatch.setattr(
        contactors,
        "load_compatibility_catalogs",
        lambda: {
            "dimension2contactor": {"2": ["DISKx", "NEWxx"]},
            "bodyType2contactor": {"RBDY2": ["DISKx", "NEWxx"]},
            "geo2contactor": {"Point": ["NEWxx"]},
            "contactorOptions": {
                "NEWxx": ["radius"],
                "DISKx": ["byrd"],
            },
            "contactorOptionalOptions": {"NEWxx": ["mode"]},
        },
    )
    monkeypatch.setattr(
        contactors, "compatibility_catalog_source", lambda: "SNAPSHOT",
    )

    schema = contactors.contactor_schema_catalog(
        fallback_options={"DISKx": ("legacy",)},
        fallback_optional_options={"DISKx": ("weights",)},
    )

    assert schema["source"] == "SNAPSHOT"
    assert schema["dimension_contactors"]["2"] == ("DISKx", "NEWxx")
    assert schema["body_type_contactors"]["RBDY2"] == ("DISKx", "NEWxx")
    assert schema["geometry_contactors"]["Point"] == ("NEWxx",)
    assert schema["options"] == {
        "DISKx": ("byrd",),
        "NEWxx": ("radius",),
    }
    assert schema["optional_options"] == {
        "DISKx": ("weights",),
        "NEWxx": ("mode",),
    }


def test_contactor_schema_reports_fallback_without_runtime_catalog(monkeypatch):
    monkeypatch.setattr(contactors, "load_compatibility_catalogs", lambda: {})

    schema = contactors.contactor_schema_catalog(
        fallback_options={"DISKx": ("byrd",)},
    )

    assert schema["source"] == "FALLBACK"
    assert schema["options"]["DISKx"] == ("byrd",)
