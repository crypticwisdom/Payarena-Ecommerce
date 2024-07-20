import calendar
import datetime
import logging
import math
import random
import string
import uuid

import pytz
from dateutil.relativedelta import relativedelta


def log_request(*args):
    for arg in args:
        logging.info(arg)


def get_delta_hour_date_time(delta):
    return (datetime.datetime.utcnow() - datetime.timedelta(hours=delta)).replace(tzinfo=pytz.UTC)


def normal_round(n):
    return 0.5 * math.ceil(2.0 * n)


def get_first_last_name(name):
    first_name = name
    last_name = ''
    try:
        first_name = name.split()[0]
        last_name = name[len(first_name) + 1:]
    except Exception as ex:
        log_request("An error occurred. Please try again. Exception : {} ".format(str(ex)))
    return first_name, last_name


def get_uuid():
    return str(uuid.uuid4())[:50]


def get_previous_date(date, delta):
    previous_date = date - datetime.timedelta(days=delta)
    return previous_date


def get_next_date(date, delta):
    previous_date = date + datetime.timedelta(days=delta)
    return previous_date


def get_previous_month_date(date, delta):
    return date - relativedelta(months=delta)


def get_week_start_and_end_datetime(date_time):
    week_start = date_time - datetime.timedelta(days=date_time.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    week_start = datetime.datetime.combine(week_start.date(), datetime.time.min)
    week_end = datetime.datetime.combine(week_end.date(), datetime.time.max)
    return week_start, week_end


def get_month_start_and_end_datetime(date_time):
    month_start = date_time.replace(day=1)
    month_end = month_start.replace(day=calendar.monthrange(month_start.year, month_start.month)[1])
    month_start = datetime.datetime.combine(month_start.date(), datetime.time.min)
    month_end = datetime.datetime.combine(month_end.date(), datetime.time.max)
    return month_start, month_end


def get_year_start_and_end_datetime(date_time):
    year_start = date_time.replace(day=1, month=1, year=date_time.year)
    year_end = date_time.replace(day=31, month=12, year=date_time.year)
    year_start = datetime.datetime.combine(year_start.date(), datetime.time.min)
    year_end = datetime.datetime.combine(year_end.date(), datetime.time.max)
    return year_start, year_end


def get_month_end_date(start_date):
    end_date = datetime.date(start_date.year, start_date.month,
                             calendar.monthrange(start_date.year, start_date.month)[-1])
    return end_date


def get_random_string(str_length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(str_length))


def get_future_date_time(date_time, delta):
    return date_time + datetime.timedelta(hours=delta)


def get_date(date_str):
    try:
        dob = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception as ex:
        log_request("An error occurred. Exception :" + str(ex))
        dob = datetime.datetime.now().date()
    return dob


def get_age(dob):
    today = datetime.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
