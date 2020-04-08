# -*- coding: utf-8 -*-
"""This module starts up a simple REST service which will update the live light. All on the `color` path.

- PUT: Update the color of the live light
- GET: Get the current color of the live light
- DELETE: Turn off the live light

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""
import http

from flask import Flask, jsonify, request
import unicornhat as uh


app = Flask(__name__)


@app.route("/color", methods=["PUT"])
def update_led_color():
    data = request.get_json()
    r, g, b = data["red"], data["green"], data["blue"]
    for x in range(4):
        for y in range(8):
            uh.set_pixel(x, y, r, g, b)

    uh.show()
    return "", http.HTTPStatus.NO_CONTENT


@app.route("/color", methods=["GET"])
def get_led_color():
    color = uh.get_pixel(0, 0)
    return {"red": color[0], "green": color[1], "blue": color[2],}, http.HTTPStatus.OK


@app.route("/color", methods=["DELETE"])
def clear_led_color():
    color = uh.off()
    return "", http.HTTPStatus.OK


if __name__ == "__main__":
    app.run()
