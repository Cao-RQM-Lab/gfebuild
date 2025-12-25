from __future__ import annotations

import gdsfactory as gf
import klayout

import numpy as np
from collections.abc import Sequence


def reticle(
    size: gf.typings.Size,
    scale: float,
    clearance: float,
    component: gf.Component,
    image_size: gf.typings.Size,
    image_layers: Sequence[gf.typings.LayerSpec],
    geometry_layer: gf.typings.LayerSpec,
) -> tuple[
    Sequence[gf.Component], dict[gf.typings.LayerSpec, tuple[int, float, float]]
]:
    """Returns a series of reticles populated with given images, and a dictionary with the locations of each layer: `{layer_number: (reticle_number, x_pos, y_pos)}`

    Args:
        size: reticle size (reticle scale)
        scale: reticle scale, reticle scale = scale * image scale
        clearance: minimum clearance between images (reticle scale)
        component: component containing all images
        image_size: size of each image (image scale)
        image_layers: layer numbers of each image
        geometry_layer: reticle polygon layer
    """
    n_x = (size[0] + clearance) // (scale * image_size[0] + clearance)
    n_y = (size[1] + clearance) // (scale * image_size[1] + clearance)
    n_r = int(np.ceil(len(image_layers) / (n_x * n_y)))
    offset_x = -0.5 * (n_x - 1) * (scale * image_size[0] + clearance)
    offset_y = -0.5 * (n_y - 1) * (scale * image_size[1] + clearance)

    reticles = [gf.Component() for _ in range(n_r)]
    placements = {}
    for r in range(n_r):
        for y in range(n_y):
            for x in range(n_x):
                i = x + y * n_x + r * n_x * n_y
                x_pos = x * (scale * image_size[0] + clearance) + offset_x
                y_pos = y * (scale * image_size[1] + clearance) + offset_y
                if i >= len(image_layers):
                    break
                image = component.extract(layers=[image_layers[i]]).remap_layers(
                    {image_layers[i]: geometry_layer}
                )
                image.transform(klayout.dbcore.DCplxTrans(mag=scale))
                image_ref = reticles[r] << image
                image_ref.move((x_pos, y_pos))

                placements[image_layers[i]] = (r, x_pos, y_pos)

        reticles[r].flatten()

    return reticles, placements
