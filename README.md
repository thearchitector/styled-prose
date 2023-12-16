# styled-prose

![GitHub Workflow Status](https://raster.shields.io/github/actions/workflow/status/thearchitector/styled-prose/ci.yaml?label=tests&style=flat-square)
![PyPI - Downloads](https://raster.shields.io/pypi/dw/styled-prose?style=flat-square)

Generate images and thumbnails based on bitmap transformations of rendered prose.

## Example

The following stylesheet is a super simple example that overrides the `default` style's font size and family. The font family `EB Garamond` is downloaded from Google Fonts and cached.

```toml
# stylesheet.toml

[[fonts]]
font_name = "EB Garamond"
from_google_fonts = true

[[styles]]
name = "default"
font_size = 14
font_name = "EB Garamond"
```

With that stylesheet, and some basic prose, you can generate an image.

```python
from PIL import Image
from styled_prose import StyledProseGenerator

text: str = """
This is normal.

<i>This is italicized.</i>

<b>This is bold.</b>

<i><b>This is bold and italicized.</b></i>

<u>This is underlined.</u>

<strike>This is struck from the record.</strike>
"""

generator: StyledProseGenerator = StyledProseGenerator("stylesheet.toml")
img: Image.Image = generator.create_jpg(
    text,
    angle=-2.5, # optional; an angle by which to rotate the image
    thumbnail=(210, 210), # optional; the dimensions of a random thumbnail
)

img.save("prose.jpg", quality=95)
```

## License

This software is licensed under the [3-Clause BSD License](LICENSE).
