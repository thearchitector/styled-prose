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
    ids=(
        "leading-space",
        "trailing-space",
        "two-words",
        "no-change",
        "no-change_2",
        "no-change_3",
        "alphanumeric",
    ),
)
def test_valid_filename(input, output):
    assert get_valid_filename(input) == output


@pytest.mark.parametrize(
    "input",
    ("", " ", "!", "!.!", ".!.", "hello."),
    ids=("blank", "whitespace", "relative", "relative_2", "relative_3", "as_ext"),
)
def test_invalid_filename(input):
    with pytest.raises(ValueError, match=r"Unable to convert.*"):
        get_valid_filename(input)
