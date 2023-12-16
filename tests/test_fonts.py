import pytest

from styled_prose.fonts import GOOGLE_FONTS_URL, register_fonts


@pytest.fixture(autouse=True)
def clear_cache():
    # clear the cache every run since we want to invoke all the logic for every
    # parametrization
    register_fonts.cache_clear()


@pytest.mark.parametrize(
    "config,exception",
    (
        ({}, r".*Misconfigurations.*"),
        ({"font_name": "mock"}, r".*You must specify a regular.*"),
        (
            {"font_name": "mock", "from_google_fonts": False},
            r".*You must specify a regular.*",
        ),
        (
            {"font_name": "mock", "from_google_fonts": True, "regular": "test"},
            r".*You cannot use Google Fonts.*",
        ),
        ({"font_name": "mock", "extra": False}, r".*Misconfigurations.*"),
    ),
    ids=(
        "empty",
        "only-name",
        "unspecified-local",
        "local-and-remote",
        "extra-property",
    ),
)
def test_register_fonts_invalid(monkeypatch, config, exception):
    monkeypatch.setattr("styled_prose.fonts.load_config", lambda _: {"fonts": [config]})

    with pytest.raises(Exception, match=exception):
        register_fonts("mock.toml")


@pytest.mark.parametrize(
    "fonts",
    (
        {"regular": "mock.ttf"},
        {"regular": "mock.ttf", "bold": "mock_bold.ttf"},
        {
            "regular": "mock.ttf",
            "bold": "mock_bold.ttf",
            "italicized": "mock_italic.ttf",
        },
        {
            "regular": "mock.ttf",
            "bold": "mock_bold.ttf",
            "italicized": "mock_italic.ttf",
            "bold_italicized": "mock_bold_italic.ttf",
        },
    ),
    ids=(
        "regular",
        "regular-bold",
        "regular-bold-italics",
        "regular-bold-italics-both",
    ),
)
def test_register_fonts_local(monkeypatch, fonts, mocker):
    # mock loaded config
    monkeypatch.setattr(
        "styled_prose.fonts.load_config",
        lambda _: {"fonts": [dict(font_name="mock", **fonts)]},
    )

    # mock font registration
    monkeypatch.setattr("pathlib.Path.exists", lambda _: True)
    monkeypatch.setattr("styled_prose.fonts.TTFont", lambda a, b: (a, str(b)))
    mock_register_font = mocker.patch("reportlab.pdfbase.pdfmetrics.registerFont")
    mock_register_family = mocker.patch(
        "reportlab.pdfbase.pdfmetrics.registerFontFamily"
    )

    register_fonts("mock.toml")

    # assert fonts have been registered
    for file in fonts.values():
        mock_register_font.assert_any_call((file[:-4], file))

    # asset the fonts have been registered to a family
    fonts["normal"] = fonts.pop("regular")
    fonts["italic"] = fonts.pop("italicized", None)
    fonts["boldItalic"] = fonts.pop("bold_italicized", None)
    mock_register_family.assert_called_once_with(
        "mock", **{key: file[:-4] for key, file in fonts.items() if file}
    )


def test_register_fonts_remote(monkeypatch, tmp_path, mocker, respx_mock, data_dir):
    monkeypatch.setattr(
        "styled_prose.fonts.load_config",
        lambda _: {"fonts": [{"font_name": "mock", "from_google_fonts": True}]},
    )

    # mock font downloads
    monkeypatch.setattr("styled_prose.fonts.FONT_CACHE", tmp_path)
    respx_mock.get(
        GOOGLE_FONTS_URL.format("mock"),
    ).respond(text=(data_dir / "remote_manifest.txt").read_text())
    respx_mock.get("https://mock/regular.ttf").respond(text="true")
    respx_mock.get("https://mock/bold.ttf").respond(text="true")
    respx_mock.get("https://mock/italic.ttf").respond(text="true")
    respx_mock.get("https://mock/bold_italic.ttf").respond(text="true")

    # mock font registration
    monkeypatch.setattr("styled_prose.fonts.TTFont", lambda a, b: (a, b))
    mock_register_font = mocker.patch("reportlab.pdfbase.pdfmetrics.registerFont")
    mock_register_family = mocker.patch(
        "reportlab.pdfbase.pdfmetrics.registerFontFamily"
    )

    register_fonts("mock.toml")

    # assert files have been cached
    assert (tmp_path / "mock/manifest.json").exists()
    assert (
        tmp_path / "mock/LICENSE.txt"
    ).read_bytes() == b"Copyright 2023 Elias Gabriel"
    for file in {"regular", "bold", "italic", "bolditalic"}:
        assert (tmp_path / f"mock/{file}.ttf").read_bytes() == b"true"

    # assert fonts have been registered
    mock_register_font.assert_any_call(("mock", (tmp_path / "mock/regular.ttf")))
    mock_register_font.assert_any_call(("mock_bold", (tmp_path / "mock/bold.ttf")))
    mock_register_font.assert_any_call(("mock_italic", (tmp_path / "mock/italic.ttf")))
    mock_register_font.assert_any_call(
        ("mock_bold_italic", (tmp_path / "mock/bolditalic.ttf"))
    )

    # asset the fonts have been registered to a family
    mock_register_family.assert_called_once_with(
        "mock",
        normal="mock",
        bold="mock_bold",
        italic="mock_italic",
        boldItalic="mock_bold_italic",
    )
