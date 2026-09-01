import warnings

import langchain  # noqa: F401
import pytest
from langchain_core._api.deprecation import LangChainPendingDeprecationWarning


@pytest.hookimpl(wrapper=True, trylast=True)
def pytest_collection():
    warnings.filterwarnings(
        "ignore",
        message=r"The default value of `allowed_objects` will change in a future version\.",
        category=LangChainPendingDeprecationWarning,
    )
    return (yield)
