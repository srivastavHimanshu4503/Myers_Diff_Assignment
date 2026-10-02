import importlib


def test_package_imports():
    # Guards the src layout and pytest pythonpath config: if either is
    # misconfigured, every later test would fail for an unrelated reason.
    module = importlib.import_module("diff_engine")
    assert module.__name__ == "diff_engine"
