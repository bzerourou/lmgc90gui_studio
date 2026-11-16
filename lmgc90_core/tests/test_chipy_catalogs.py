from lmgc90_core.chipy_catalogs import (
    GBV_VECTOR_NAMES,
    GBV_VECTORS,
    INSP2D_FUNCS,
    INSP3D_FUNCS,
    INSPI_FUNCS,
    SET_FUNCS,
)


def test_chipy_catalogs_keep_curated_entries_and_valid_metadata():
    assert [len(catalog) for catalog in (
        INSP2D_FUNCS, INSP3D_FUNCS, INSPI_FUNCS, SET_FUNCS,
    )] == [70, 67, 96, 161]

    for catalog in (INSP2D_FUNCS, INSP3D_FUNCS, INSPI_FUNCS, SET_FUNCS):
        names = [entry[0] for entry in catalog]
        assert len(names) == len(set(names))
        assert all(
            len(entry) == 3
            and isinstance(entry[0], str)
            and isinstance(entry[1], str)
            and isinstance(entry[2], int)
            for entry in catalog
        )

    assert GBV_VECTOR_NAMES == [name for name, _ in GBV_VECTORS]
