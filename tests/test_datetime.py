import time,datetime


def test_datetime_format():
    # fmt = '%Y-%m-%d %H:%M:%S'
    fmt="%Y-%m-%d %H:%M:%S"
    print(time.strftime(fmt, time.localtime()))


if __name__ == '__main__':
    test_datetime_format()
