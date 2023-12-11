from __future__ import annotations

import os
from pathlib import Path
from random import randint
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from uuid import uuid4

from pdf2image.pdf2image import convert_from_path
from PIL import Image, ImageChops, ImageColor, ImageFilter
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import Paragraph, SimpleDocTemplate

from .fonts import register_fonts
from .stylesheet import load_stylesheet

if TYPE_CHECKING:
    from typing import List, Optional, Tuple

    from .stylesheet import StyleSheet


class StyledProseGenerator:
    def __init__(self, config: Path) -> None:
        register_fonts(config)
        self.stylesheet: StyleSheet = load_stylesheet(config)

    def create_jpg(
        self,
        prose: str,
        style: str = "default",
        angle: float = 0,
        thumbnail: Optional[Tuple[int, int]] = None,
        prescale_thumbnail: bool = True,
        comparative_font_size: float = 6.0,
    ) -> Image.Image:
        """
        Converts the provided prose into an stylized image. If provided a style, that
        style is used when configuring and producing the rendered prose. If an angle is
        provided, that angle is applied to the stylized prose after generation. If
        thumbnail dimensions are provided, the image is cropped after the previous
        steps.

        `prescale_thumbnail` and `comparative_font_size` control the thumbnail cropping
        behavior; if enabled, to aesthetically accommodate various font sizes, a
        scaled initial thumbnail area is captured as to match the density of text in
        the same area if the prose were rendered using the provided
        `comparative_font_size`. The defaults produce a thumbnail with a text density
        similar to 6pt EB Garamond text inside a 210x210 square. The intermediate
        thumbnail is always scaled to the requested thumbnail dimensions using the
        Lanczos algorithm before being returned.
        """
        if style not in self.stylesheet:
            raise ValueError(
                f"Could not find a prose style named '{style}'. Does it exist?"
            )

        with TemporaryDirectory() as tmpdir:
            # construct the PDF
            filename: Path = Path(tmpdir) / f"{uuid4()}.pdf"
            document: SimpleDocTemplate = SimpleDocTemplate(
                str(filename),
                leftMargin=0,
                topMargin=0,
                rightMargin=0,
                bottomMargin=0,
                pagesize=LETTER,
            )
            raw_prose: str = prose.replace("\r", "").replace("\n", "<br />")
            document.build([Paragraph(raw_prose, self.stylesheet[style])])

            # convert the PDF to a series of images
            images: List[Image.Image] = convert_from_path(
                filename,
                thread_count=min(4, os.cpu_count() or 1),
                use_pdftocairo=True,
                fmt="jpeg",
            )

        # collate the images into a single long one
        width: int = images[0].size[0]
        height: int = images[0].size[1]
        total_height: int = height * len(images)
        output: Image.Image = Image.new("RGB", (width, total_height))
        for page, im in enumerate(images):
            output.paste(im, (0, page * height))

        white: Tuple[int, ...] = ImageColor.getrgb("white")
        if angle:
            # if an angle is supplied, rotate the image while expanding the dimensions
            # to accommodate
            output = output.rotate(
                angle,
                resample=Image.Resampling.NEAREST,
                fillcolor=white,
                expand=True,
            )

        # trim the whitespace around the image
        mask: Image.Image = Image.new(output.mode, output.size, white)
        diff: Image.Image = ImageChops.difference(output, mask)
        bbox: Optional[Tuple[int, int, int, int]] = diff.getbbox()
        if bbox:
            output = output.crop(bbox)

        if thumbnail:
            # produce a thumbnail for the image
            dims: Tuple[int, int] = output.size
            scale: float = 1

            if prescale_thumbnail:
                # to try and aesthetically accommodate various font sizes, we first
                # calculate a scaling ratio to alter the image's final "text density";
                # the optimal text density was subjectively picked to, visually, match
                # 6pt EB Garamond font within a 210x210 square.
                font_ratio: float = (
                    self.stylesheet[style].fontSize / comparative_font_size
                )
                scale = min(
                    font_ratio,
                    dims[0] / thumbnail[0],
                    dims[1] / thumbnail[1],
                )

            # crop the image to match the desired thumbnail
            scaled_tw, scaled_th = (
                int(thumbnail[0] * scale),
                int(thumbnail[1] * scale),
            )
            x: int = randint(0, dims[0] - scaled_tw)
            y: int = randint(0, dims[1] - scaled_th)
            output = output.crop((x, y, x + scaled_tw, y + scaled_th))

            if prescale_thumbnail:
                # if we scaled it before cropping, we need to scale it back to the
                # dimensions that were requested
                output = output.filter(ImageFilter.SHARPEN)
                output = output.resize(
                    thumbnail, resample=Image.Resampling.LANCZOS, reducing_gap=2.0
                )

        return output
