import os

from PyQt5.QtGui import QImageReader

from resources import ICON_SIZES, asset_path, qss_url


def test_all_icon_sizes_ship():
    for size in ICON_SIZES:
        path = asset_path("icons", f"icon-{size}.png")
        assert os.path.isfile(path), path
        assert QImageReader(path).size().width() == size


def test_platform_bundle_icons_exist():
    assert os.path.isfile(asset_path("icon.icns"))
    assert os.path.isfile(asset_path("icon.ico"))


def test_app_icon_has_every_size(qapp):
    import main
    icon = main._app_icon()
    assert {s.width() for s in icon.availableSizes()} >= set(ICON_SIZES)


def test_checkbox_tick_is_loadable(qapp):
    assert os.path.isfile(asset_path("ui", "check.svg"))
    assert QImageReader(asset_path("ui", "check.svg")).canRead()
    assert "\\" not in qss_url("ui", "check.svg")
