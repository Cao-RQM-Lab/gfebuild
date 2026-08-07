from __future__ import annotations

import gdsfactory as gf
import klayout

import pathlib as pl

GERBER_INT_DIGITS = 4
GERBER_DECIMAL_DIGITS = 6
MICRONS_TO_MM = 1e-3


def gerber(
    component: gf.Component,
    image_layer: gf.typings.LayerSpec,
    filename: str,
) -> None:
    """Writes a gerber file with the specified geometry

    Args:
        component: component containing all images
        image_layer: layer number of image
        filename: full path and filename to write to
    """

    def format_coord(value: float) -> str:
        scaled = round(value * (10**GERBER_DECIMAL_DIGITS))
        sign = "-" if scaled < 0 else ""
        return f"{sign}{abs(scaled):0{GERBER_INT_DIGITS + GERBER_DECIMAL_DIGITS}d}"

    image = component.extract(layers=[image_layer])

    polygons = image.get_polygons_points(
        by="tuple",
        layers=[image_layer],
        scale=MICRONS_TO_MM,
    ).get(tuple(image_layer), [])

    output_path = pl.Path(filename).with_suffix(".gbr")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        f.write("%TF.FileFunction,Other,Stencil*%\n")
        f.write("%TF.FilePolarity,Positive*%\n")
        f.write(
            f"%FSLAX{GERBER_INT_DIGITS}{GERBER_DECIMAL_DIGITS}Y{GERBER_INT_DIGITS}{GERBER_DECIMAL_DIGITS}*%\n"
        )
        f.write("%MOMM*%\n")
        f.write("%LPD*%\n")
        f.write("G01*\n")
        f.write("%ADD10C,0.050000*%\n")
        f.write("D10*\n")

        for polygon_points in polygons:
            points = [(float(x), float(y)) for x, y in polygon_points]
            points = points if points[0] == points[-1] else [*points, points[0]]

            f.write("G36*\n")
            x0, y0 = points[0]
            f.write(f"X{format_coord(x0)}Y{format_coord(y0)}D02*\n")
            for x, y in points[1:]:
                f.write(f"X{format_coord(x)}Y{format_coord(y)}D01*\n")
            f.write("G37*\n")

        f.write("M02*\n")
