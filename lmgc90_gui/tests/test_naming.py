from lmgc90_gui.utils.naming import (
    suggest_law_name, suggest_material_name, suggest_model_name, unique_name,
)


def test_unique_name_increments():
    assert unique_name("STEEL", []) == "STEEL"
    assert unique_name("STEEL", ["STEEL"]) == "STEE1"
    assert unique_name("STEEL", ["STEEL", "STEE1"]) == "STEE2"


def test_material_defaults():
    assert suggest_material_name("RIGID", []) == "STEEL"
    assert suggest_material_name("RIGID", ["STEEL"]) == "RIGID"
    assert suggest_material_name("ELAS", []) == "CONCR"
    assert suggest_material_name("ELAS", ["CONCR"]) == "ELAS"


def test_model_defaults():
    assert suggest_model_name("MECAx", "Rxx2D", []) == "rigid"
    assert suggest_model_name("MECAx", "Rxx2D", ["rigid"]) == "rigi1"
    assert suggest_model_name("MULTI", "T3xxx", []) == "MULTI"


def test_law_defaults():
    assert suggest_law_name("IQS_CLB", []) == "IQS"
    assert suggest_law_name("IQS_CLB", ["IQS"]) == "IQS01"
    assert suggest_law_name("GAP_SGR_CLB", []) == "GAP"
