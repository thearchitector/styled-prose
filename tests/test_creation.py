from styled_prose import StyledProseGenerator


def test_create(data_dir):
    with open(data_dir / "prose.txt", "r") as f:
        text = f.read()

    generator = StyledProseGenerator(data_dir / "stylesheet.toml")
    img = generator.create_jpg(
        text,
        angle=-2.5,
        thumbnail=(210, 210),
    )

    img.save(data_dir / "prose.jpg", quality=95)
