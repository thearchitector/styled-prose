import pytest

from styled_prose.util import get_valid_filename


@pytest.mark.parametrize(
    "input,output",
    (
        (" leading", "leading"),
        ("trailing ", "trailing"),
        ("hello world", "hello_world"),
        ("hello1_world", "hello1_world"),
        ("hello.world", "hello.world"),
        ("hello-world", "hello-world"),
        ("hello world!", "hello_world"),
    ),
)
def test_valid_filename(input, output):
    assert get_valid_filename(input) == output


@pytest.mark.parametrize("input", ("", " ", "!", "!.!", ".!.", "hello."))
def test_invalid_filename(input):
    with pytest.raises(ValueError, match=r"Unable to convert.*"):
        get_valid_filename(input)
