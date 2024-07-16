"""Base classes for the ETL process."""

from abc import ABC, abstractmethod

import pandas as pd


class IExtractor(ABC):
    """Extract interface for ETLs, extracts the data from source."""

    @abstractmethod
    def extract(self) -> pd.DataFrame:
        """Extract data from the source."""


class ITransformer(ABC):
    """Transform interface for ETLs, transforms the data."""

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the data."""


class ILoader(ABC):
    """Load interface for ETLs, loads the data."""

    @abstractmethod
    def load(self, df: pd.DataFrame) -> None:
        """Load the data."""


class DummyTransformer(ITransformer):
    """Dummy transformer, does nothing."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the data."""
        return df


class IETL:
    """ETL interface, runs the ETL process."""

    @property
    @abstractmethod
    def extractor(self) -> IExtractor:
        """Extractor."""

    @property
    @abstractmethod
    def transformer(self) -> ITransformer:
        """Transformer."""

    @property
    @abstractmethod
    def loader(self) -> ILoader:
        """Loader."""

    def run(self) -> None:
        """Run the ETL process."""
        df = self.extractor.extract()
        if self.transformer is not None:
            df = self.transformer.transform(df)
        self.loader.load(df)
