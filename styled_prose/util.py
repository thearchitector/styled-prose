from __future__ import annotations

import platform
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Set


def get_valid_filename(name: str) -> str:
    # Copyright (c) Django Software Foundation and individual contributors.
    # All rights reserved.
    #
    # Redistribution and use in source and binary forms, with or without modification,
    # are permitted provided that the following conditions are met:
    #
    #     1. Redistributions of source code must retain the above copyright notice,
    #        this list of conditions and the following disclaimer.
    #
    #     2. Redistributions in binary form must reproduce the above copyright
    #        notice, this list of conditions and the following disclaimer in the
    #        documentation and/or other materials provided with the distribution.
    #
    #     3. Neither the name of Django nor the names of its contributors may be used
    #        to endorse or promote products derived from this software without
    #        specific prior written permission.
    #
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    # ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    # WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    # DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
    # ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    # (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    # LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
    # ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    # SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    """
    s: str = str(name).strip().replace(" ", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)

    invalid: Set[str] = {"", ".", ".."}
    if platform.system() == "Windows":
        # windows has reserved filenames that we cannot allow
        invalid.update(
            {"CON", "PRN", "AUX", "NUL"},
            {f"COM{i}" for i in range(1, 10)},
            {f"LPT{i}" for i in range(1, 10)},
        )

    if s in invalid or s.endswith("."):
        raise ValueError(
            f"Unable to convert the provided font family name '{name}' into a filename."
        )

    return s


def to_camel_case(field: str, parent: str = "", swap: bool = False) -> str:
    """
    Convert a given field to camel case, optionally prepending or appending a parent
    namespace.

    ex. 'camel_case'                         -> 'camelCase'
    ex. ('color', parent='bullet')           -> 'bulletColor'
    ex. ('left', parent='indent', swap=True) -> 'leftIndent'
    """
    parts: list[str] = field.split("_")
    if not parent:
        parent, parts = parts[0], parts[1:]

    if swap:
        parent, parts = parts[0], (parts[1:] + [parent])

    return parent + "".join(part.title() for part in parts)
