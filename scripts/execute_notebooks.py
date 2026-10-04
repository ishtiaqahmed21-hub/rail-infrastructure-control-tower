"""Execute each analytical notebook from the repository root."""

from pathlib import Path
import os
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
for variable, folder in {
    "IPYTHONDIR": "ipython",
    "JUPYTER_RUNTIME_DIR": "jupyter_runtime",
    "JUPYTER_CONFIG_DIR": "jupyter_config",
    "MPLCONFIGDIR": "matplotlib",
}.items():
    directory = ROOT / ".cache" / folder
    directory.mkdir(parents=True, exist_ok=True)
    os.environ[variable] = str(directory)
for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
    notebook = nbformat.read(path, as_version=4)
    NotebookClient(
        notebook,
        timeout=180,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    ).execute()
    nbformat.write(notebook, path)
    print(path.name, "PASS")
