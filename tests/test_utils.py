from bot.utils import str_time_to_timedelta, get_time


def test_get_time():
    time1_str = "5d 13h 4m 21s"
    assert get_time("d", time1_str) == 5
    assert get_time("h", time1_str) == 13
    assert get_time("m", time1_str) == 4
    assert get_time("s", time1_str) == 21

    time2_str = "2d 17h 32m 46s"
    assert get_time("d", time2_str) == 2
    assert get_time("h", time2_str) == 17
    assert get_time("m", time2_str) == 32
    assert get_time("s", time2_str) == 46
