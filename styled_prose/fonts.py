from __future__ import annotations

import json
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from urllib.parse import quote_plus

from httpx import Client, HTTPError, Response
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .config import load_config
from .exceptions import BadFontException
from .util import get_valid_filename

if TYPE_CHECKING:
    from typing import Any, Dict, Set, Tuple

CURRENT_VERSION: str = version("styled-prose")
FONT_CACHE: Path = Path.home() / ".cache" / "styled_prose_fonts"
GOOGLE_FONTS_URL: str = "https://fonts.google.com/download/list?family={}"
FONT_FILE_SUFFIXES: Set[str] = {
    "-Regular.ttf",
    "-Bold.ttf",
    "-Italic.ttf",
    "-BoldItalic.ttf",
}


class FontFamily(BaseModel):
    font_name: str

    # manual truetype files
    regular: Optional[Path] = None
    bold: Optional[Path] = None
    italicized: Optional[Path] = None
    bold_italicized: Optional[Path] = None

    # if download from google
    from_google_fonts: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_remote_or_local(self: FontFamily) -> FontFamily:
        if not self.from_google_fonts and not self.regular:
            # if local and missing a regular font file
            raise ValueError(
                f"Invalid font family {self.font_name}! You must specify a regular"
                " local font file, or enable `from_google_fonts` to use Google Fonts."
            )
        elif self.from_google_fonts and (
            self.regular or self.bold or self.italicized or self.bold_italicized
        ):
            # if remote but local files are provided
            raise ValueError(
                f"Invalid font family {self.font_name}! You cannot use Google Fonts"
                " while also providing local font files. Disable remote fetching or"
                " unset all local files."
            )

        return self


def _register_font_files(
    font_family: str,
    normal: Path,
    bold: Optional[Path] = None,
    italic: Optional[Path] = None,
    bold_italic: Optional[Path] = None,
) -> None:
    """Register the given font files, and combine them into a font family."""
    fonts: Dict[str, str] = {"normal": font_family}

    pdfmetrics.registerFont(TTFont(fonts["normal"], normal))

    if bold and bold.exists():
        fonts["bold"] = f"{fonts['normal']}_bold"
        pdfmetrics.registerFont(TTFont(fonts["bold"], bold))
    if italic and italic.exists():
        fonts["italic"] = f"{fonts['normal']}_italic"
        pdfmetrics.registerFont(TTFont(fonts["italic"], italic))
    if bold_italic and bold_italic.exists():
        fonts["boldItalic"] = f"{fonts['normal']}_bold_italic"
        pdfmetrics.registerFont(TTFont(fonts["boldItalic"], bold_italic))

    pdfmetrics.registerFontFamily(font_family, **fonts)


def _download_font_family(
    client: Client, font_family: str
) -> Tuple[Path, Path, Path, Path]:
    """
    Attempt to download the necessary TrueType font files for the provided font family
    from Google Fonts.
    """
    font_dir: Path = FONT_CACHE / get_valid_filename(font_family)
    font_dir.mkdir(parents=True, exist_ok=True)

    manifest_file: Path = font_dir / "manifest.json"
    manifest: Dict[str, Any]

    # if the font file manifest doesn't exist, download it
    if not manifest_file.exists():
        font_url: str = GOOGLE_FONTS_URL.format(quote_plus(font_family))
        resp: Response = client.get(font_url)
        resp.raise_for_status()
        body: bytes = resp.read()[5:]  # trim the beginning malformed `)]}'\n`
        manifest = json.loads(body)["manifest"]

        with open(manifest_file, "w") as f:
            json.dump(manifest, f)
    else:
        # if it does exist, read it
        with open(manifest_file, "r") as f:
            manifest = json.load(f)

    file: Path
    for files in manifest["files"]:
        # write the all the bundled files, except the google readme, to the cache
        # this will include the license to the font
        if files["filename"] != "README.txt":
            file = font_dir / files["filename"]
            #  if the file is in the cache already, skip it
            if not file.exists():
                file.write_text(files["contents"].replace("\r", ""))

    for files in manifest["fileRefs"]:
        # iterate through all the available fonts, downloading and caching
        # the all ones we care about (ie. the ones RL can use)
        font_style: str = files["filename"].split("-")[-1][:-4].lower()
        if font_style in {"regular", "bold", "italic", "bolditalic"}:
            file = font_dir / f"{font_style}.ttf"
            if not file.exists():
                # if the file doesn't exist, download it
                file_resp: Response = client.get(files["url"])
                file_resp.raise_for_status()
                file.write_bytes(file_resp.read())

    return (
        font_dir / "regular.ttf",
        font_dir / "bold.ttf",
        font_dir / "italic.ttf",
        font_dir / "bolditalic.ttf",
    )


@lru_cache(maxsize=None)
def register_fonts(path: Path) -> None:
    config: Dict[str, Any] = load_config(path)
    c_path: Path = Path(path).parent
    client: Optional[Client] = None

    try:
        for ff in config.get("fonts", []):
            # for each font family, register the provided fonts
            font_family: FontFamily = FontFamily(**ff)
            normal: Path
            bold: Optional[Path] = None
            italic: Optional[Path] = None
            bold_italic: Optional[Path] = None

            if font_family.from_google_fonts:
                # if from google
                if not client:
                    # if not client is defined, create one. this lets us share a single
                    # client instance across all remote fonts rather than create a new
                    # one every time, which is more efficient / resource friendly.
                    client = Client(
                        http2=True,
                        follow_redirects=True,
                        headers={"User-Agent": f"styled-prose/{CURRENT_VERSION}"},
                    )

                normal, bold, italic, bold_italic = _download_font_family(
                    client, font_family.font_name
                )
            else:
                # if local
                normal = c_path / font_family.regular  # type: ignore
                bold = c_path / font_family.bold if font_family.bold else None
                italic = (
                    c_path / font_family.italicized if font_family.italicized else None
                )
                bold_italic = (
                    c_path / font_family.bold_italicized
                    if font_family.bold_italicized
                    else None
                )

            _register_font_files(
                font_family.font_name,
                normal,  # pyright: ignore
                bold=bold,
                italic=italic,
                bold_italic=bold_italic,
            )
    except ValidationError as err:
        raise BadFontException(
            f"Invalid font family! Misconfigurations are listed below:\n" f"\n{err}"
        ) from None
    except HTTPError as err:
        raise BadFontException(
            "Failed to download the specified fonts from Google Fonts. Are you sure"
            " they're available?"
        ) from err
    finally:
        if client:
            client.close()
