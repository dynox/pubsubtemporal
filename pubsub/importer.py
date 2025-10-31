import importlib
import pkgutil


def import_package_modules(package_name: str) -> None:
    try:
        root = importlib.import_module(package_name)
    except Exception:
        return

    root_path = getattr(root, "__path__", None)
    if not root_path:
        return

    for finder, name, is_pkg in pkgutil.iter_modules(root_path):
        full_name = f"{package_name}.{name}"
        try:
            importlib.import_module(full_name)

            if is_pkg:
                import_package_modules(full_name)
        except Exception:
            pass
