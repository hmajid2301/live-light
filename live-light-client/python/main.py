import configparser
import logging
import sys
import time

import pyudev
import requests


logger = logging.getLogger(__name__)


def usb_devices_changed(device):
    """Called everytime a USB is plugged in or out of the computer."""
    red_color = {"red": 255, "green": 0, "blue": 0}
    green_color = {"red": 0, "green": 255, "blue": 0}

    try:
        config = get_config()
        setup_logging(level=config.get("main", "logging_level"))
        product_name = config.get("main", "usb_name")
        pi_address = config.get("main", "pi_address")
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logger.error(f"Invalid configuration file, {e}.")
        sys.exit(1)

    if device.action == "add":
        is_correct = is_correct_usb_plugged_in(device, product_name)
        if is_correct:
            update_color(pi_address, red_color)

    else:
        is_correct = was_correct_usb_plugged_out(product_name)
        if is_correct:
            update_color(pi_address, green_color)
        else:
            update_color(pi_address, red_color)


def get_config():
    parser = configparser.ConfigParser()
    parser.read('live-light-client.conf')
    return parser


def setup_logging(level):
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def is_correct_usb_plugged_in(device, product_name):
    """Check the name of the USB that has just been plugged in and if it matches the one we are checking for."""
    correct_usb = False
    try:
        usb_name = device.attributes.get("product").decode().strip()
        if usb_name == product_name:
            correct_usb = True
    except AttributeError:
        pass

    return correct_usb


def was_correct_usb_plugged_out(product_name):
    """Check all USBs plugged in and check if any match the name of the one expected device."""
    correct_usb_plugged_out = True
    context = pyudev.Context()

    for device in context.list_devices(subsystem='usb'):
        try:
            usb_name = device.attributes.get("product").decode().strip()
        except AttributeError:
            continue

        if usb_name == product_name:
            correct_usb_plugged_out = False

    return correct_usb_plugged_out


def update_color(pi_address, new_color):
    """Update color on the PI."""
    logger.info(f"Getting current color {new_color}.")
    response = requests.get(f"{pi_address}/color")
    current_color = response.json()
    logger.info(f"Current color, {current_color}.")

    if not current_color == new_color:
        logger.info(f"Updating with new color {new_color}.")
        response = requests.put(f"{pi_address}/color", json=new_color)
        logger.info(f"Response from PI {response.status_code}.")


if __name__ == "__main__":
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='usb')

    random_device = list(context.list_devices(subsystem='usb'))[0]
    usb_devices_changed(device=random_device)

    observer = pyudev.MonitorObserver(monitor, callback=usb_devices_changed, name='monitor-observer')
    observer.start()
    while True:
        time.sleep(15)
