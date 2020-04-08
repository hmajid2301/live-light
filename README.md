# Live Light

A Mood light that will change colour depending from red -> green (vice versa), if the user is busy. It was intended
to be used to show others that I am in a meeting. It is built specifically for a Raspberry PI connected to a 
[Pirmoroni Mood Light](https://learn.pimoroni.com/tutorial/sandyj/assembling-mood-light).

<span>
  <img src="images/red.jpg" width="30%" />
  <img src="images/green.jpg" width="30%" />
</span>

This repo consists of two packages:

> Info: you can find the debian packages to install [here in releases](https://gitlab.com/hmajid2301/live-light/-/releases)

## Live Light Server

This Debian package is to be installed on the device with the Mood light (i.e. The PI).
It runs a simple Gunicorn, Flask API. Hosted by Nginx. It allows you use a REST API to
change the colour on the Mood light. 

An example request make look like (assuming your PI is called `raspberrypi.local`):

```bash
curl -X PUT --header "Content-Type: application/json"\
            --data '{"red":0,"green":255, "blue": 0}' \
            http://raspberrypi.local/color
```

## Live Light Client

This debian package is to be installed on the host machine where the USB will be plugged into.
In my case it's my Desktop where it detects if my headset is plugged in and changes the colour
accordingly. The live lights uses a basic schedule you provide outside of the day and hours
you provide it will switch itself off. By default it will be on between the hours of 9AM -> 5.30PM,
only on Mon - Fri (not turned on at weekends).

### USB Name

You can get this on by running `lsusb`. Then copy the device name `Corsair Corsair VOID RGB USB Gaming Headset`.

```bash
$ lsusb
Bus 006 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 005 Device 003: ID 1b1c:1b5c Corsair CORSAIR NIGHTSWORD RGB Gaming Mouse
Bus 005 Device 002: ID 1b1c:1b49 Corsair CORSAIR K70 RGB MK.2 Mechanical Gaming Keyboard
Bus 005 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 004 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 003 Device 004: ID 1b1c:0c12 Corsair Corsair VOID RGB USB Gaming Headset 
Bus 003 Device 003: ID 05e3:0608 Genesys Logic, Inc. Hub
...
```

### Server Address

The address (including schema) of your `live-light-server`. Such as `http://raspberrypi.local`. This is the URL the
client will make the requests to.

### Example Config

Once the debconf values have all been filled the `live-light-client.conf` may look something like.

```ini
[main]
usb_name=Corsair VOID RGB USB Gaming Headset
server_address=http://raspberrypi.local

[schedule]
active_days=Monday,Tuesday,Wednesday,Thursday,Friday
start_time=09:00
end_time=17:30

[color]
active=#FF0000
inactive=#00FF00

[other]
logging_level=INFO
```

## Demo

[![Live Light Demo](http://i3.ytimg.com/vi/7YuyvgypuXI/maxresdefault.jpg)](http://www.youtube.com/watch?v=7YuyvgypuXI "Live Light Demo")

## Installation

* Go to [releases](https://gitlab.com/hmajid2301/live-light/-/releases)
* Download artifacts
* Install `live-light-client` on your personal machine
* Install `live-light-server` on your PI

### Example

The example assumes you want to use version 0.1.0. It also assumes you can ssh to your
raspberrypi using the username `pi` and "domain" `raspberrypi.local`. Adjust below
as required.

```bash
wget https://gitlab.com/hmajid2301/live-light/-/jobs/502692706/artifacts/download
unzip artifacts.zip
sudo dpkg -i live-light-client*.deb

# Copy server .deb to PI
scp live-light-server*.deb pi@raspberrypi.local:~/
ssh pi@raspberrypi.local
sudo dpkg -i live-light-server*.deb
```

### Build from Source

You can also build the debian packages from source.

```bash
sudo apt install build-essential autoconf automake autotools-dev dh-make debhelper devscripts fakeroot xutils lintian \
                pbuilder
git clone https://gitlab.com/hmajid2301/live-light.git
cd live-light-client
debuild -i -us -uc -b
cd live-light-server
debuild -i -us -uc -b

# Location of the debian packages
cd ..
ls -l *.deb
```

## Reasoning

This is a just simple tool I built When you install the package it will ask a few questions. over a weekend during the coronavirus lockdown, so that others in my household
would know when I was in a meeting. The reason I ended up changing the light by using a USB was because I have a lot
of impromptu meetings that aren't in my calendar. I did think about using my calendar originally. Also I end up using
a few meeting apps such as Skype, Slack & Teams. So it also wouldn't so simple to detect if I was in a call in either
of them.

## Future Features

- Make requests using HTTPS
- Allow other methods of changing colour (generalise)
- Extend `live-light-server` api to be able to display more complicated patterns
- Add docker images

## Appendix

- [Assemble Mood Light](https://www.youtube.com/watch?v=eHD9JIQk0I)
- [Setup `.local` address](https://www.howtogeek.com/167190/how-and-why-to-assign-the-.local-domain-to-your-raspberry-pi/)
- [Inspired By Jim Bennett ](https://dev.to/azure/an-iot-busy-light-for-folks-working-from-home-34ig)

> P.S I'm sorry to my other brits for misspelling colour so may times 😢.