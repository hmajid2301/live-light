# -*- coding: utf-8 -*-
"""This module updates the live light. If the current time is not within the schedule it will switch the live light
off. If the live light is on it detects if a specific USB is plugged in/out, then updates the color
accordingly. For example if the USB is plugged in it will change the color to red (default value) and
green (default) when the USB is plugged out.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""
import asyncio
import configparser
import datetime
import logging
import sys
from textwrap import wrap
import time

import pyudev
import requests


logger = logging.getLogger(__name__)


def usb_devices_changed(_):
    """This function is a callback which is called everytime USB is plugged/out (by pyudev). It checks if the specific
    USB is plugged in and updates the color of the live light.

    """
    config = get_config()
    log_level = config.get("other", "logging_level")
    setup_logging(level=log_level)
    product_name = config.get("main", "usb_name")
    server_address = config.get("main", "server_address")
    active_color = hex_to_rgb_dict(hex_code=config.get("color", "active"))
    inactive_color = hex_to_rgb_dict(hex_code=config.get("color", "inactive"))

    is_plugged_in = is_usb_plugged_in(product_name)
    if is_plugged_in:
        update_color(server_address, active_color)
    else:
        update_color(server_address, inactive_color)


def get_config():
    """Gets the config from the config file, the config file is usually created using debconf (in the postinst script
    of the debian package).

    Returns:
        ConfigParser: The config file.

    """
    parser = configparser.ConfigParser()
    parser.read("live-light-client.conf")
    return parser


def setup_logging(level):
    """Setups a basic logger for this app.

    Args:
        level (str): What the log level should be set to i.e. INFO.

    """
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def hex_to_rgb_dict(hex_code):
    """Takes a hex string (``"#00FF00"``) and converts it into an RGB dict (``{"red": 0, "green": 255, "blue": 0}``).
    Each of the two characters correspond to a single component of RGB. As an RGB component is 1 byte (8 bits) and 
    each hex character is 4 bits so two hex characters make a byte.

    Args:
        hex_code (str): The hex code to convert into an RGB dict.

    Returns:
        dict: The hex string as an RGB dict.

    """
    if "#" in hex_code[0]:
        hex_code = hex_code[1:]

    hex_list = wrap(hex_code, 2)
    rgb = [int(hex_value, 16) for hex_value in hex_list]

    return {"red": rgb[0], "green": rgb[1], "blue": rgb[2]}


def is_usb_plugged_in(product_name):
    """Checks if the specificed USB (product_name) is currently plugged into the computer.

    Args:
        product_name (str): The name of the USB device we are looking for. This should match the out shown in `lsusb`.

    Returns:
        bool: True if the USB device is plugged in, else returns False.

    """
    usb_plugged_in = False
    context = pyudev.Context()

    for device in context.list_devices(subsystem="usb"):
        try:
            usb_name = device.attributes.get("product").decode().strip()
        except AttributeError:
            continue

        if usb_name == product_name:
            usb_plugged_in = True

    return usb_plugged_in


def update_color(server_address, new_color):
    """Makes an API request to update the color on the server. It first gets the current color on the server and if
    the color is different then sends a request to update the color.

    Args:
        server_address (str): Where to make the API request to i.e ``http://raspberrypi.local``.
        new_color (dict): What to update the new color to, as an RGB dict i.e. ``{"red": 0, "green": 255, "blue": 0}``.

    """
    logger.info("Getting current color.")
    response = requests.get(f"{server_address}/color")
    current_color = response.json()
    logger.info(f"Current color, {current_color}.")

    if not current_color == new_color:
        logger.info(f"Updating with new color {new_color}.")
        response = requests.put(f"{server_address}/color", json=new_color)
        logger.info(f"Response from PI {response.status_code}.")


def clear_color(server_address):
    """Makes an API request to turn off the live light.

    Args:
        server_address (str): Where to make the API request to i.e ``http://raspberrypi.local``.

    """
    logger.info(f"Turning off LEDs.")
    response = requests.delete(f"{server_address}/color")
    logger.info(f"Response, {response.status_code}.")


async def main():
    """The main function creates an event loop that will loop forever. When it first starts it works out if the light
    should be on/off. As most likely the user has just turned on their computer at a random time. So we need to work
    out if the live light needs to be on. After this it loops between the on/off mode and sleeps in between them.
    We can work out exactly how many seconds to sleep as we can work out the time the live light next needs to turn
    on/off.

    """
    logger.info("Starting live-light-client.")
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="usb")
    observer = pyudev.MonitorObserver(monitor, callback=usb_devices_changed, name="monitor-observer")

    config = get_config()
    schedule = get_schedule_config(config)
    day_time_data = get_date_time_data(schedule)

    is_active_time = day_time_data["day"] in schedule["active_days"] and (
        day_time_data["current_time"] > day_time_data["start_time"]
        and day_time_data["current_time"] < day_time_data["end_time"]
    )
    logger.info(f"Should we turn on live light {is_active_time}.")

    try:
        while True:
            turn_on_off_live_light(is_active_time, observer)
            seconds_to_sleep = get_seconds_to_sleep(is_active_time, schedule)
            await asyncio.sleep(seconds_to_sleep)
            is_active_time = not is_active_time
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logger.error(f"Invalid configuration file, {e}.")
        sys.exit(1)
    except IndexError:
        logger.error(
            f"Invalid active {config.get('color', 'active')} and inactive color {config.get('color', 'inactive')} values."
        )
        sys.exit(1)


def get_schedule_config(config):
    """Get all the config related to scheduling this includes:

    - Active Days
    - Start Time
    - End Time

    It will also convert the hours and minute we should start/end in to ints.

    Args:
        config (ConfigParser): ConfigParser object used to get the config.

    Returns:
        dict: Containing the active days, start and end times.

    """
    active_days_list = [day.strip() for day in config.get("schedule", "active_days").split(",")]
    start_time_hour, start_time_minute = config.get("schedule", "start_time").split(":")
    end_time_hour, end_time_minute = config.get("schedule", "end_time").split(":")

    return {
        "active_days": active_days_list,
        "start": {"hour": int(start_time_hour), "minute": int(start_time_minute)},
        "end": {"hour": int(end_time_hour), "minute": int(end_time_minute)},
    }


def get_date_time_data(schedule):
    """Get data related to the "current" time. Such as the current day. The current date time.
    The time to start and end the live light today.

    Args:
        schedule (dict): The schedule data i.e. active days, start and end times.

    Returns:
        dict: Containing the datetime data.

    """
    current_datetime = datetime.datetime.now()
    current_day = current_datetime.strftime("%A")
    start_time = current_datetime.replace(
        hour=schedule["start"]["hour"], minute=schedule["start"]["minute"], second=0, microsecond=0
    )
    end_time = current_datetime.replace(
        hour=schedule["end"]["hour"], minute=schedule["end"]["minute"], second=0, microsecond=0
    )

    return {"current_time": current_datetime, "day": current_day, "start_time": start_time, "end_time": end_time}


def get_seconds_to_sleep(is_active_time, schedule):
    """Gets the number of seconds the main "loop" should sleep for before turning off/on the live light. The opposite
    of it's current state.

    Args:
        is_active_time (boolean): True if the live light is active. False if the live light is off

    Returns:
        int: Number of seconds to sleep until we need to toggle the light on/off.

    """
    day_time_data = get_date_time_data(schedule)
    current_datetime = day_time_data["current_time"]
    if is_active_time:
        seconds_to_sleep = (day_time_data["end_time"] - current_datetime).total_seconds()
    else:
        days_to_sleep = get_days_to_sleep(current_day=day_time_data["day"], active_days=schedule["active_days"])
        next_active_day_start_time = day_time_data["start_time"] + datetime.timedelta(days=days_to_sleep)
        seconds_to_sleep = (next_active_day_start_time - current_datetime).total_seconds()

    return seconds_to_sleep


def turn_on_off_live_light(is_active_time, observer):
    """Either turns on/off the live light. When the live light is turned off it also switches off. When switched off
    we also turn off the observer daemon listening for new USB devices. 

    Args:
        is_active_time (boolean): True if the live light should be on and False if live light should be switched off.
        observer (pyudev.Observer): The pyudev daemon used, when a USB device is plugged/out.

    """

    if is_active_time:
        logger.info("Turning on live light.")
        usb_devices_changed(None)
        observer.start()
    else:
        logger.info("Turning off live light.")
        observer.stop()
        config = get_config()
        server_address = config.get("main", "server_address")
        clear_color(server_address)


def get_days_to_sleep(current_day, active_days):
    """Get the number of days we should sleep for. This is used to work out how long the live light should be switched
    on for. Often this will be 0 if say it's Mon and next active day is Tue. But we can more days to sleep for
    example if it's Fri and next active day is Mon, then we will sleep for 2 days. Before we need to switch on the
    live light again.
    
    To do this we get the next active day. If the next active day is "behind" the current day i.e. today is Fri
    and next active day is Mon. Then it will the monday next week so we add 7 to it's current index. In example
    Fri has an index of 4 and Mon has an index of 0, we add 7 to Mon so Mon = 7 and Fri = 4 then when we work
    out days till we are next active it will be 2 days (weekend).

    Args:
        current_day (str): The current day i.e. "Monday".
        active_days (list): The days we want the live light to be on for.

    Returns:
        int: How many days we should turn the live light off for.

    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    next_active_day = get_next_active_day(days, current_day, active_days)
    current_day_index = days.index(current_day)
    next_day_index = days.index(next_active_day)

    if next_day_index <= current_day_index:
        next_day_index += 7

    days_until_next_active_day = next_day_index - current_day_index
    return days_until_next_active_day


def get_next_active_day(days, current_day, active_days):
    """Gets the next active day, often this will simply be the next day, i.e. if you set the active days as Mon - Fri
    and today is Mon, then the next active day is Tue. However is today is Fri then the next active day will be Mon.

    If say our active days are Mon - Fri and today is say ``Fri``, then next active day is ``Mon``. So instead of adding
    one to the index and getting ``Sat`` we will simple go to the start of our list index 0 which is ``Mon``. However
    most of the time the next day will be the active day i.e. today is ``Mon`` so we will simply just add one to our index
    to get ``Tue``.

    Args:
        days (list): Of days Mon - Sun.
        current_day (str): The current day i.e. ``Monday``.
        active_days (list): Of days we want the live light to be on.

    Returns:
        str: Next day the live light should be switched on.

    """
    common_days = [day for day in days if day in active_days]
    current_day_index = common_days.index(current_day)
    next_active_day = 0 if current_day_index + 1 == len(common_days) else current_day_index + 1
    return days[next_active_day]


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
