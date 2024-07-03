"""Context for database session."""

from types import TracebackType
from typing import Optional, Type

from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from velib_spot_predictor.environment import DBConfig


class DatabaseSession(BaseModel):
    """Class to manage database session.

    Examples
    --------
    >>> from velib_spot_predictor.data.database.context import DatabaseSession
    >>> with DatabaseSession() as session:
    ...     # Do something with the session
    """

    db_config: DBConfig = Field(default_factory=DBConfig)

    @property
    def db_url(self) -> str:
        """Database URL."""
        return self.db_config.db_url

    @property
    def engine(self):
        """Database engine."""
        if not hasattr(self, "_engine"):
            self._engine = create_engine(self.db_url)
        return self._engine

    @property
    def session(self):
        """Database session."""
        if not hasattr(self, "_session"):
            self._session = sessionmaker(bind=self.engine)
        return self._session

    def __enter__(self):
        """Enter the context of a database session.

        Returns
        -------
        sqlalchemy.orm.Session
            Database session
        """
        return self.session()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        """Exit the context of a database session."""
        self.session().close()
        return True
