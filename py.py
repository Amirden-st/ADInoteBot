
import re
import datetime

test_datetime = datetime.datetime(2021, 7, 28, 23, 0)
now = datetime.datetime.now()

testdelta = datetime.timedelta(hours=1)
print(test_datetime.strftime("%y-%m-%d %H:%M"))
print(re.search(
    r'(?P<year>\d{2,4}(?=\.\d{2}\.\d{2}))?\.?(?P<month>\d{2}(?=\.\d{2}))?\.?(?P<day>\d{2})?(?:\s+)?(?P<hour>\d{1,2}):?(?P<minute>\d{2})?', '.20 21:43').groupdict())
print(list(map(int, {1: "2"})))
t = datetime.datetime(year=2021, month=2, day=13, hour=23, minute=12)
print(t.strftime("%y.%m.%d %H:%M"))
print("21.06.06 23:00" > "21.06.06 23:00")
