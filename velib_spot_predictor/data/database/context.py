"""Context for database session."""
from types import TracebackType
from typing import Optional, Type

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from velib_spot_predictor.environment import DBConfig


class DatabaseSession:
    """Class to manage database session.

    Examples
    --------
    >>> from velib_spot_predictor.data.database.context import DatabaseSession
    >>> with DatabaseSession() as session:
    ...     # Do something with the session
    """

    def __init__(self):
        """Initialize the database session."""
        db_url = DBConfig().db_url
        self.engine = create_engine(db_url)
        self.session = sessionmaker(bind=self.engine)

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
