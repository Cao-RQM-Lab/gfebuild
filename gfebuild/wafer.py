from __future__ import annotations

import gdsfactory as gf
import klayout

import numpy as np
from collections.abc import Sequence


def wafer(
    radius: float,
    chip_center: bool,
    place_partial: bool,
    avoid: dict[tuple[float, float], float],
    component: gf.Component,
    image_size: gf.typings.Size,
    image_layer: gf.typings.LayerSpec,
    geometry_layer: gf.typings.LayerSpec,
) -> tuple[gf.Component, Sequence[tuple[float, float]]]:
    """Returns a wafer populated with chips, and a list of all placed center coordinates

    Args:
        radius: wafer radius
        chip_center: `True` to place chip center at wafer center, `False` to place chip corner at wafer center
        place_partial: `True` to place partial chips at wafer edge
        avoid: coordinates to avoid, in a dictionary of form `{(x, y): radius}`
        component: component containing all images
        image_size: image size
        image_layers: layer number of image
        geometry_layer: reticle polygon layer
    """
    c = gf.Component()
    placements = []

    image = component.extract(layers=[image_layer]).remap_layers(
        {image_layer: geometry_layer}
    )

    x_count = int(np.ceil(radius / image_size[0])) + 1
    x_limit = image_size[0] * x_count
    y_count = int(np.ceil(radius / image_size[1])) + 1
    y_limit = image_size[1] * y_count

    for y in np.linspace(
        -y_limit, y_limit, 2 * y_count + int(chip_center), endpoint=chip_center
    ):
        for x in np.linspace(
            -x_limit, x_limit, 2 * x_count + int(chip_center), endpoint=chip_center
        ):
            x_pos = x if chip_center else x + 0.5 * image_size[0]
            y_pos = y if chip_center else y + 0.5 * image_size[1]

            def check_intersection(
                c_center: tuple[float, float],
                c_radius: float,
                partial: bool,
            ):
                r_left = x_pos - 0.5 * image_size[0]
                r_right = x_pos + 0.5 * image_size[0]
                r_bottom = y_pos - 0.5 * image_size[1]
                r_top = y_pos + 0.5 * image_size[1]

                # circle fully inside rectangle
                if (
                    c_center[0] - c_radius >= r_left
                    and c_center[0] + c_radius <= r_right
                    and c_center[1] - c_radius >= r_bottom
                    and c_center[1] + c_radius <= r_top
                ):
                    return True

                # rectangle fully inside circle
                x_dist_max = np.max(
                    [np.abs(r_left - c_center[0]), np.abs(r_right - c_center[0])]
                )
                y_dist_max = np.max(
                    [np.abs(r_bottom - c_center[1]), np.abs(r_top - c_center[1])]
                )
                if np.linalg.norm([x_dist_max, y_dist_max]) <= c_radius:
                    return True

                # check partial intersection
                x_dist_close = c_center[0] - np.max(
                    [r_left, np.min([c_center[0], r_right])]
                )
                y_dist_close = c_center[1] - np.max(
                    [r_bottom, np.min([c_center[1], r_top])]
                )

                if partial and np.linalg.norm([x_dist_close, y_dist_close]) <= c_radius:
                    return True

                return False

            if not check_intersection(
                c_center=(0, 0),
                c_radius=radius,
                partial=place_partial,
            ):
                continue

            flag = False
            for avoid_pos, avoid_r in avoid.items():
                if check_intersection(
                    c_center=avoid_pos,
                    c_radius=avoid_r,
                    partial=True,
                ):
                    flag = True
                    break

            if flag:
                continue

            image_ref = c << image
            image_ref.move((x_pos, y_pos))
            placements.append((x_pos, y_pos))

    return c, placements
