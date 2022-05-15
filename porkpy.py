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
__version__ = "0.1.1"


import click
import json
import os
import requests
import sys


API_ENDPOINT = "https://porkbun.com/api/json/v3/"
AUTH_OPTIONS = (
    click.option("-f", "--file", type=click.Path(exists=True), default="porkpy.json"),
    click.option("-s", "--secrets", type=str),
)
DOMAIN_OPTIONS = (
    click.option("-d", "--domain", required=True, type=str),
    click.option("-n", "--name", type=str),
    click.option("-t", "--type", type=str),
    click.option("-c", "--content", type=str),
    click.option("-l", "--ttl", type=str),
    click.option("-p", "--priority", type=str),
)
VALID_DOMAIN_TYPES = (
    "A",
    "MX",
    "CNAME",
    "ALIAS",
    "TXT",
    "NS",
    "AAAA",
    "SRV",
    "TLSA",
    "CAA",
)


def add_options(options):
    def _add_options(f):
        for option in reversed(options):
            f = option(f)
        return f

    return _add_options


class PorkRecord:
    def __init__(self, domain, auth):
        self.domain = domain
        self.auth = auth
        return

    def retrieve(self):
        response = requests.post(
            API_ENDPOINT + f"dns/retrieve/{self.domain}", data=self.auth.auth_str()
        )
        json_resp = response.json()
        return json.dumps(json_resp)


# With our auth we want to go in order of importance:
# - command line args
# - json file (can be set by flag, but defaults to "porkpy.json" in cwd)
# - env variables ("PORKPY_SECRET" & "PORKPY_API")
class PorkAuth:
    """Call for authorizing access to Porkbun API"""

    AUTH_PAYLOAD = {"secretapikey": None, "apikey": None}

    # what I need to do here is determine if key, and secret are both passed in
    # then check to see if they actually work by pinging the api, and if so then
    # we've got a valid auth and can proceed with whatever dumb shit we want to
    # do.
    def __init__(self, file, secrets=None):
        if secrets:
            key, secret = secrets.split(":")
            self.AUTH_PAYLOAD = {"apikey": key, "secretapikey": secret}
        elif file:
            with open(file, "r") as auth_file:
                self.AUTH_PAYLOAD = {**json.load(auth_file)}
        else:
            self.AUTH_PAYLOAD = {
                "secretapikey": os.getenv("PORKPY_SECRET"),
                "apikey": os.getenv("PORKPY_API"),
            }

    def test_auth(self, ipv4=False):
        endpoint = API_ENDPOINT

        if ipv4:
            endpoint = endpoint.replace("porkbun.com", "api-ipv4.porkbun.com")

        response = requests.post(
            API_ENDPOINT + "ping", data=json.dumps(self.AUTH_PAYLOAD)
        )
        json_resp = response.json()
        return (json_resp["status"] == "SUCCESS", json_resp)

    def auth_str(self):
        return json.dumps(self.AUTH_PAYLOAD)


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


@cli.command(name="pricing", short_help="Check pricing of TLDs")
@click.option(
    "-t",
    "--tld",
    default=None,
    help="Specific TLDs you'd like pricing for. Use multiple flags for multiple TLDs. Omit for all TLDs.",
    multiple=True,
    type=str,
)
def pricing(tld):
    # FIXME: check for status code response from our post request and display
    # info to the user about why it might have failed.
    response = requests.post(API_ENDPOINT + "pricing/get")
    json_resp = response.json()
    output = {}

    if json_resp["status"] == "SUCCESS":
        if len(tld) == 0:
            output = json_resp
        else:
            output["status"] = json_resp["status"]
            for d in tld:
                try:
                    output["pricing"] = {d: json_resp["pricing"][d]}
                except KeyError:
                    # FIXME: Should we indicate in our output that the user is an
                    # idiot and needs to stop passing in stupid requests?
                    continue
    else:
        print("FIXME: API call was unsuccessful.")

    print(json.dumps(output))


@cli.command(name="auth", help="Check if you are authorized to access the Porkbun API")
@add_options(AUTH_OPTIONS)
def authorized(**kwargs):
    auth = PorkAuth(**kwargs)
    success, response = auth.test_auth()
    print(json.dumps(response))


# @cli.command(name="domain", )
@cli.group(help="Do stuff with your domain")
def domain(**kwargs):
    pass


@domain.command("info")
@add_options(DOMAIN_OPTIONS)
@add_options(AUTH_OPTIONS)
def domain_retrieve_records(**kwargs):
    auth_args = {d: v for (d, v) in kwargs.items() if d in ("secrets", "file")}
    auth = PorkAuth(**auth_args)
    domain = PorkRecord(kwargs["domain"], auth)
    print(domain.retrieve())


@domain.command("create")
def domain_create_record(**kwargs):
    pass


@domain.command("edit")
def domain_edit_records(**kwargs):
    pass


@domain.command("delete")
def domain_delete_records(**kwargs):
    pass


def main():
    cli()
    return 0


if __name__ == "__main__":
    sys.exit(main())
