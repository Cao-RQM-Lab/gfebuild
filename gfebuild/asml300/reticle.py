from __future__ import annotations

import gdsfactory as gf

import numpy as np
import importlib.resources
from collections.abc import Sequence

import gfebuild as gb


TEMPLATE_FILE = importlib.resources.files(__package__) / "reticle_template.gds"

RETICLE_AVAILABLE_SIZE = (88000, 88000)
RETICLE_SCALE = 4
RETICLE_MIN_SPACE = 4000
RETICLE_GEOMETRY_LAYER = (4, 0)

BARCODE_START_POS = (69000, 53300)
BARCODE_HEIGHT = 5000

TEXT_SIZE = 2500
TEXT0_MID_POS = (-69500, -37500)
TEXT1_MID_POS = (-69500, 37500)

RETICLE_TEMPLATE = gf.import_gds(gdspath=TEMPLATE_FILE)


def reticle(
    component: gf.Component,
    image_size: gf.typings.Size,
    image_layers: Sequence[gf.typings.LayerSpec],
    id: str,
    text: str,
) -> tuple[
    Sequence[gf.Component], dict[gf.typings.LayerSpec, tuple[int, float, float]]
]:
    """Returns a series of reticles populated with given images, and a dictionary with the locations of each layer: `{layer_number: (reticle_number, x_pos, y_pos)}`

    Args:
        component: component containing all images
        image_size: size of each image (image scale)
        image_layers: layer numbers of each image
        id: reticle ID, 8 characters max, `-R0`, `-R1` etc. will be appended to the ID for each reticle generated
        text: additional text to add to top right box, 12 characters max
    """
    id = id[:8].upper()
    text = text[:12].upper()

    reticles, placements = gb.reticle(
        size=RETICLE_AVAILABLE_SIZE,
        scale=RETICLE_SCALE,
        clearance=RETICLE_MIN_SPACE,
        component=component,
        image_size=image_size,
        image_layers=image_layers,
        geometry_layer=RETICLE_GEOMETRY_LAYER,
    )

    n_r = len(reticles)

    asml_reticles = [RETICLE_TEMPLATE.copy() for _ in range(n_r)]

    for i in range(n_r):
        _ = asml_reticles[i] << reticles[i]

        barcode_ref = asml_reticles[i] << gb.asml300.barcode(
            string=f"{id}-R{i}",
            height=BARCODE_HEIGHT,
            geometry_layer=RETICLE_GEOMETRY_LAYER,
        )
        barcode_ref.rotate(angle=-90, center=(0, 0))
        barcode_ref.move(BARCODE_START_POS)

        id_ref = asml_reticles[i] << gf.components.text(
            text=f"{id}-R{i}",
            size=TEXT_SIZE,
            position=(0, 0),
            justify="center",
            layer=RETICLE_GEOMETRY_LAYER,
        )
        id_ref.rotate(angle=90, center=(0, 0))
        id_ref.move(TEXT0_MID_POS)

        text_ref = asml_reticles[i] << gf.components.text(
            text=text,
            size=TEXT_SIZE,
            position=(0, 0),
            justify="center",
            layer=RETICLE_GEOMETRY_LAYER,
        )
        text_ref.rotate(angle=90, center=(0, 0))
        text_ref.move(TEXT1_MID_POS)

        asml_reticles[i].flatten()
        asml_reticles[i].name = f"{id}-R{i}"

    return asml_reticles, placements
