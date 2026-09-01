import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent
REPO_ROOT = FIXTURES_DIR.parent.parent

# Make scripts/ (production code) and fixtures/scripts, fixtures/prompts
# (test-support helpers) importable without installing this project as a package.
for path in (REPO_ROOT / "scripts", FIXTURES_DIR / "scripts", FIXTURES_DIR / "prompts"):
    sys.path.insert(0, str(path))
