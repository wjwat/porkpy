#!/usr/bin/evn python3
# -*- coding: utf-8 -*-

# Copyright © 2022 Will Watkins
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__author__ = "Will Watkins"
__copyright__ = "Copyright 2022 Will Watkins"
__license__ = "MIT"
__version__ = "0.1.0"


import click
import json
import requests
import sys


class PorkAuth:
    """Call for authorizing access to Porkbun API"""

    API_KEY = None
    API_SECRET = None

    def __init__(self, key=None, secret=None):
        # what I need to do here is determine if key, and secret are both passed in
        # then check to see if they actually work by pining the api, and if so then
        # we've got a valid auth and can proceed with whatever dumb shit we want to
        # do.
        print("stub")


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


@cli.command(help="Check pricing of TLDs")
@click.option(
    "-d",
    "--domain",
    default=None,
    help="Specific TLDs you'd like info for. Use multiple flags for multiple TLDs. Omit for all TLDs.",
    multiple=True,
    type=str,
)
def pricing(domain):
    # FIXME: check for status code response from our post request and display
    # info to the user about why it might have failed.
    response = requests.post("https://porkbun.com/api/json/v3/pricing/get")
    json_resp = response.json()
    output = {}

    if json_resp["status"] == "SUCCESS":
        if len(domain) == 0:
            output = json_resp
        else:
            output["status"] = json_resp["status"]
            for d in domain:
                try:
                    output["pricing"] = {d: json_resp["pricing"][d]}
                except KeyError:
                    # FIXME: Should we indicate in our output that the user is an
                    # idiot and needs to stop passing in stupid requests?
                    continue
    else:
        print("FIXME: API call was unsuccessful.")

    print(json.dumps(output))


def main():
    cli()
    return 0


if __name__ == "__main__":
    sys.exit(main())
