import importlib.util
import os
import sys


def import_all_models(base_path: str = "src"):
    base_path = os.path.abspath(base_path)

    for root, _, files in os.walk(base_path):
        if "models.py" in files:
            file_path = os.path.join(root, "models.py")
            module_name = os.path.relpath(file_path, start=os.getcwd()).replace(
                os.sep, "."
            )
            module_name = module_name[:-3]

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                continue

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
