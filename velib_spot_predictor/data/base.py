"""Base classes for the ETL process."""

import abc

import pandas as pd


class IExtractor(abc.ABC):
    """Extract interface for ETLs, extracts the data from source."""

    @abc.abstractmethod
    def extract(self) -> pd.DataFrame:
        """Extract data from the source."""


class ITransformer(abc.ABC):
    """Transform interface for ETLs, transforms the data."""

    @abc.abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the data."""


class ILoader(abc.ABC):
    """Load interface for ETLs, loads the data."""

    @abc.abstractmethod
    def load(self, df: pd.DataFrame) -> None:
        """Load the data."""


class DummyTransformer(ITransformer):
    """Dummy transformer, does nothing."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the data."""
        return df


class IETL:
    """ETL interface, runs the ETL process."""

    def __init__(
        self, extractor: IExtractor, transformer: ITransformer, loader: ILoader
    ):
        """Initialize the ETL process.

        Parameters
        ----------
        extractor : IExtractor
            Extract instance
        transformer : ITransformer
            Transform instance
        loader : ILoader
            Load instance
        """
        self.extractor = extractor
        self.transformer = transformer
        self.loader = loader

    def run(self) -> None:
        """Run the ETL process."""
        df = self.extractor.extract()
        if self.transformer is not None:
            df = self.transformer.transform(df)
        self.loader.load(df)
