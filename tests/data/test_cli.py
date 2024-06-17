from datetime import datetime

import pytest
from pytest_mock import MockerFixture

from velib_spot_predictor.data.cli import prompt_for_correct_date


@pytest.mark.parametrize(
    "input_date", ["20210101", "2021010101", "202101010101"]
)
def test_prompt_for_correct_date_correct(
    mocker: MockerFixture, input_date: str
):
    """Test prompt_for_correct_date with correct input."""
    mocker.patch("click.prompt", return_value=input_date)
    date_from_input = prompt_for_correct_date("")
    assert date_from_input == datetime.strptime(
        input_date.ljust(12, "0"), "%Y%m%d%H%M"
    )
