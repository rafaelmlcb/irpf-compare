"""
DEPRECATED: Este módulo foi substituído por project/main.py.

Use:
    python3 project/main.py --input arquivo.DEC --output saida.xlsx

Ou via módulo:
    python3 -m project.main --input arquivo.DEC --output saida.xlsx
"""
import sys
import warnings

warnings.warn(
    "project/cli/main.py está depreciado. Use project/main.py diretamente.",
    DeprecationWarning,
    stacklevel=1,
)

from project.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
