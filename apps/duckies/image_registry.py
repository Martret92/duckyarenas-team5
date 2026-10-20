"""Registro de recursos estáticos de Duckies."""

OUTFITS = {
    code: {
        sex: f"duckies/images/outfits/{code}/{sex}.svg"
        for sex in ("male", "female")
    }
    for code in (
        "prehistorico",
        "griego",
        "romano",
        "medieval",
        "renacentista",
        "revolucion_industrial",
        "siglo_xx",
    )
}

SPECIALIZATION_OUTFITS = {
    code: {
        sex: f"duckies/images/specializations/{code}/{sex}.svg"
        for sex in ("male", "female")
    }
    for code in (
        "developer",
        "gamer",
        "ciber",
        "sistemas",
        "data_ia",
    )
}

ITEM_IMAGES = {
    code: f"duckies/images/items/{code}.svg"
    for code in (
        "smoke",
        "false_options",
        "overclock",
        "firewall",
        "noise_filter",
        "slow_time",
    )
}

DEFAULT_IMAGE = "duckies/images/placeholders/default.svg"


def image_for(item, sex="male"):
    """Devuelve la ruta estática de la imagen de un objeto."""

    if item is None:
        return DEFAULT_IMAGE

    code = item.code.lower()

    sex = sex if sex in ("male", "female") else "male"

    if code.startswith("outfit_"):
        code = code.removeprefix("outfit_")

    if code.startswith("specialization_"):
        code = code.removeprefix("specialization_")

    if code in OUTFITS:
        return OUTFITS[code][sex]

    if code in SPECIALIZATION_OUTFITS:
        return SPECIALIZATION_OUTFITS[code][sex]

    return item.image_path or ITEM_IMAGES.get(
        code,
        DEFAULT_IMAGE,
    )
