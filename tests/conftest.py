"""
Pytest configuration for the constitution-skill project.

Adds the project root to sys.path so that tests can import
the `skills` package directly.
"""

import sys
from pathlib import Path

# Add project root (parent of tests/) to sys.path
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
