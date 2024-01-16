# Bug Buddy

Bug Buddy is a python library that helps you take action on exceptions in your code.

It is primarily a decorator that will locally cache exceptions and, if specified, upload the exception as a gitlab or github issue. Too often do we encounter bugs in our code that are not properly managed and fixed. Prescribing to the notion that code is in an ever-improving state, Bug Buddy helps devlopers track both high-frequency and one-off bugs by autocaching locally and uploading to a remote so they may be linked to appropriate update branches.

## Installation

![Version](https://img.shields.io/badge/version-1.0.1-blue)
[![python](https://img.shields.io/badge/Python-3.10-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Packaged with Poetry](https://img.shields.io/badge/packaging-poetry-cyan.svg?style=flat-square&logo=python)](https://python-poetry.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

You can install Bug Buddy using pip:

```
pip install bug-buddy
```

## Usage

To use Bug Buddy, you need to import it and decorate the top-level callable of your code with `@bug_buddy`. For example:

```
import pandas as pd
from bug_buddy import bug_buddy

@bug_buddy(project_id=43922234, gitlab=True)
def main() -> None:
    """Runner function.

    Create a dataframe with two columns.

    Expect to throw a ValueError with the exception logged
    to Gitlab by bug_buddy.
    """

    pd.DataFrame({"a": [1, 2, 3], "b": [4, 5]})
```

Running this code, Bug Buddy returns the traceback as well as a logging statement identifying that bug has been cached and uploaded to a project ID at the remote if one was specified.

## Parameters

The `@bug_buddy` decorator accepts the following parameters:

- `project_id`: The ID of the repository that issues are to be created for. You can find the ID by going to the project's homepage and clicking on the **Project information** button.
- `gitlab`: A boolean value indicating whether to upload the exception to Gitlab or not. Default is `False`.
- `github`: A boolean value indicating whether to upload the exception to Github or not. Default is `False`.

## Features

Bug Buddy has the following features:

- It supports both Gitlab and Github (**IN DEV**), and you can choose which one to use by setting the `gitlab` or `github` parameter to `True`.
- It automatically creates a formatted issue for the exception, including the traceback, the code snippet, and the environment information.
- It tags the issue with exception type encountered.
- It caches the exceptions locally in a JSON file stored in `$HOME`, so you can access them offline or delete them if needed.
