"""
DataLoader — finds and loads the latest processed pkl files from data/interim/.

Resolves the 'latest' file by sorting all matching filenames alphabetically
(YYYYMMDD suffix means lexicographic sort == chronological sort).

Usage:
    loader = DataLoader()
    df = loader.load_citizenship_direction()
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


# ── DataLoader class ───────────────────────────────────────────────────────────

class DataLoader:
    """Loads the latest interim pkl files for each dataset.

    Args:
        base_path: Root of the repository. Defaults to 3 levels above this file.
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent
        self.interim_path = base_path / "data" / "interim"
        self._cache: dict[str, pd.DataFrame] = {}

    # ── Private helpers ────────────────────────────────────────────────────────

    def _load_latest(self, pattern: str) -> pd.DataFrame:
        """Find and load the latest pkl matching pattern."""
        if pattern in self._cache:
            return self._cache[pattern]
        files = sorted(self.interim_path.glob(f"{pattern}_*.pkl"))
        if not files:
            raise FileNotFoundError(
                f"No file matching '{pattern}_*.pkl' in {self.interim_path}"
            )
        path = files[-1]
        df = pd.read_pickle(path)
        print(f"  Loaded {path.name}  ({len(df):,} rows)")
        self._cache[pattern] = df
        return df

    # ── Public loaders ─────────────────────────────────────────────────────────

    def load_citizenship_direction(self) -> pd.DataFrame:
        """Direction × Citizenship (monthly).

        Columns: Month, Count, Direction, Citizenship
        """
        return self._load_latest("df_citizenship_direction")

    def load_direction_age_sex(self) -> pd.DataFrame:
        """Direction × Age Group × Sex (monthly).

        Columns: Month, Count, Direction, Age Group, Sex
        """
        return self._load_latest("df_direction_age_sex")

    def load_direction_visa(self) -> pd.DataFrame:
        """Direction × Visa type (monthly, arrivals focus).

        Columns: Month, Count, Direction, Visa
        """
        return self._load_latest("df_direction_visa")

    def load_citizenship_visa(self) -> pd.DataFrame:
        """Citizenship × Visa (monthly, arrivals).

        Columns: Month, Count, Visa, Citizenship
        """
        return self._load_latest("df_citizenship_visa")

    def load_direction_region(self) -> pd.DataFrame:
        """Direction × NZ Area (monthly).

        Columns: Month, Count, Direction, Region
        """
        return self._load_latest("df_direction_region")

    def load_clpr_india_visa(self) -> pd.DataFrame:
        """CLPR=India × Visa × Citizenship (monthly, arrivals).

        Columns: Month, Count, Direction, CLPR, Visa, Citizenship
        """
        return self._load_latest("df_clpr_india_visa")

    def load_clpr_china_visa(self) -> pd.DataFrame:
        """CLPR=China × Visa × Citizenship (monthly, arrivals).

        Columns: Month, Count, Direction, CLPR, Visa, Citizenship
        """
        return self._load_latest("df_clpr_china_visa")
