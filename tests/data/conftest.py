import os
from datetime import datetime, timedelta

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import create_engine
from time_machine import travel
from velib_spot_predictor.data.database.context import DatabaseSession
from velib_spot_predictor.data.database.models import Base, Station, Status
from velib_spot_predictor.environment import DBConfig

## Fixtures for testing with database interactions in memory


class TestDatabaseInteraction:
    @travel("2021-01-01 12:00:00")
    @pytest.fixture(autouse=True)
    def mock_db(self, mocker: MockerFixture, tmpdir):
        self.mock_db_path = os.path.join(tmpdir, "test.db")
        self.mock_db_url = f"sqlite:///{self.mock_db_path}"
        mocker.patch.dict(
            os.environ,
            {
                "DB_HOST": "fake_host",
                "DB_PORT": "3306",
                "DB_NAME": "fake_name",
                "DB_USER": "fake_user",
                "DB_PASSWORD": "fake_password",
            },
        )
        mocker.patch.object(
            DBConfig,
            "db_url",
            new_callable=mocker.PropertyMock,
            return_value=self.mock_db_url,
        )
        engine = create_engine(self.mock_db_url)
        Base.metadata.create_all(engine)
        with DatabaseSession() as session:
            session.add(
                Station(station_id=1, name="Station 1", capacity=10, lat=1.0, lon=4.0)
            )
            session.add(
                Station(station_id=2, name="Station 2", capacity=20, lat=2.0, lon=5.0)
            )
            session.add(
                Status(
                    station_id=1,
                    status_datetime=datetime.now(),
                    num_bikes_available=5,
                    num_bikes_available_types_mechanical=3,
                    num_bikes_available_types_ebike=2,
                    num_docks_available=5,
                    is_installed=True,
                    is_returning=True,
                    is_renting=True,
                )
            )
            session.add(
                Status(
                    station_id=2,
                    status_datetime=datetime.now(),
                    num_bikes_available=10,
                    num_bikes_available_types_mechanical=6,
                    num_bikes_available_types_ebike=4,
                    num_docks_available=10,
                    is_installed=True,
                    is_returning=True,
                    is_renting=True,
                )
            )
            session.add(
                Status(
                    station_id=1,
                    status_datetime=datetime.now() - timedelta(hours=1),
                    num_bikes_available=6,
                    num_bikes_available_types_mechanical=4,
                    num_bikes_available_types_ebike=2,
                    num_docks_available=4,
                    is_installed=False,
                    is_returning=False,
                    is_renting=False,
                )
            )
            session.commit()
        yield
        Base.metadata.drop_all(engine)
        engine.dispose()
