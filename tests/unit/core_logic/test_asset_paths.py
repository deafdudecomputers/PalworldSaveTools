from __future__ import annotations
import os
from tests.dynamic_importer import import_from

get_resources_directory = import_from('common', 'get_resources_directory')


def test_get_resources_directory_returns_string():
    path = get_resources_directory()
    assert isinstance(path, str)
    assert os.path.isabs(path)


def test_resources_directory_has_i18n():
    path = get_resources_directory()
    assert os.path.isdir(os.path.join(path, "i18n"))


def test_resources_directory_has_assets():
    path = get_resources_directory()
    assert os.path.isdir(os.path.join(path, "assets"))
