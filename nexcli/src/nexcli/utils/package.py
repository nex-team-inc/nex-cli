from importlib.metadata import Distribution, PackageNotFoundError
from json import loads


def is_editable(pkg: Distribution) -> bool:
    """Check if the given pkg was installed as editable or not"""
    json_text = pkg.read_text("direct_url.json")
    if json_text is None:
        return False
    dir_info = loads(json_text).get("dir_info", None)
    if dir_info is None:
        return False
    return dir_info.get("editable", False)


def is_valid_package_for_install(pkg_name: str) -> bool:
    """Checks if a package name is available for install."""
    try:
        pkg = Distribution.from_name(pkg_name)
        return not is_editable(pkg)
    except PackageNotFoundError:
        return True
