from styled_prose.creation import create_pdf


def test_create(data_dir):
    text: str
    with open(data_dir / "prose.txt", "r") as f:
        text = f.read()

    create_pdf(data_dir / "stylesheet.toml", "prose.pdf", text)
