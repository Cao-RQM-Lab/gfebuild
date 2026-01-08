from __future__ import annotations

import gdsfactory as gf

import numpy as np
import importlib.resources
from collections.abc import Sequence

import gfebuild as gb


ALIGNMENT_MARK_FILE = importlib.resources.files(__package__) / "pm_mark.gds"
ALIGNMENT_MARK_LAYER = (1, 0)
ALIGNMENT_MARK_CLEARANCE_RADIUS = 500
RETICLE_GEOMETRY_LAYER = (4, 0)

TEXT_SIZE = 2500


def wafer(
    radius: float,
    chip_center: bool,
    place_partial: bool,
    marks: Sequence[tuple[float, float]],
    component: gf.Component,
    image_size: gf.typings.Size,
    image_layer: gf.typings.LayerSpec,
    id: str,
    text: str,
) -> tuple[gf.Component, Sequence[tuple[float, float]]]:
    """Returns a wafer populated with chips, and a list of all placed center coordinates

    Args:
        radius: wafer radius
        chip_center: `True` to place chip center at wafer center, `False` to place chip corner at wafer center
        place_partial: `True` to place partial chips at wafer edge
        marks: coordinates to place alignment marks
        component: component containing all images
        image_size: image size
        image_layers: layer number of image
        geometry_layer: reticle polygon layer
        id: reticle ID
        text: additional text
    """
    id = id.upper()
    text = text.upper()

    wafer, placements = gb.wafer(
        radius=radius,
        chip_center=chip_center,
        place_partial=place_partial,
        avoid={mark: ALIGNMENT_MARK_CLEARANCE_RADIUS for mark in marks},
        component=component,
        image_size=image_size,
        image_layer=image_layer,
        geometry_layer=RETICLE_GEOMETRY_LAYER,
    )

    alignment_mark = (
        gf.import_gds(gdspath=ALIGNMENT_MARK_FILE)
        .extract(
            layers=[ALIGNMENT_MARK_LAYER],
        )
        .remap_layers({ALIGNMENT_MARK_LAYER: RETICLE_GEOMETRY_LAYER})
    )

    for mark in marks:
        ref = wafer << alignment_mark
        ref.move(mark)

    wafer << gf.components.text(
        text=id,
        size=TEXT_SIZE,
        position=(-radius, radius),
        justify="left",
        layer=RETICLE_GEOMETRY_LAYER,
    )

    wafer << gf.components.text(
        text=text,
        size=TEXT_SIZE,
        position=(radius, radius),
        justify="right",
        layer=RETICLE_GEOMETRY_LAYER,
    )

    wafer.flatten()
    wafer.name = id

    return wafer, placements
