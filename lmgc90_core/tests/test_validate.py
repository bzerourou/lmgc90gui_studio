from lmgc90_core import MaterialType, Model, ValidationError, pre
from lmgc90_core.validate import validate_avatar, validate_material, validate_model


def test_material_name_too_long():
    m = pre.material(name="TOOLONG", materialType="RIGID", density=1.0)
    try:
        validate_material(m)
        assert False
    except ValidationError as e:
        assert "5" in str(e)


def test_material_density():
    m = pre.material(name="STEEL", materialType="RIGID", density=-1)
    try:
        validate_material(m)
        assert False
    except ValidationError:
        pass


def test_model_wrong_element():
    m = Model(name="rigid", physics="MECAx", element="Rxx3D", dimension=2)
    try:
        validate_model(m)
        assert False
    except ValidationError:
        pass


def test_disk_needs_2d_model():
    model = Model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2)
    av = pre.rigidDisk(r=0.1, center=[0, 0, 0], model="rigid", material="STEEL")
    try:
        validate_avatar(av, model)
        assert False
    except ValidationError:
        pass


def test_valid_disk():
    model = Model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2)
    av = pre.rigidDisk(r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL")
    validate_avatar(av, model)
