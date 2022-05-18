#!/usr/bin/env python3
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
from typing import Any, Callable, Optional


API_ENDPOINT = "https://porkbun.com/api/json/v3"
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
PORKPY_OPTIONS = {
    "file": click.option(
        "-f",
        "--file",
        type=click.Path(exists=True),
        default="porkpy.json",
        help="JSON file containing apikey & secretapikey for the Porkbun API.",
    ),
    "secrets": click.option(
        "-s",
        "--secrets",
        type=str,
        help="String containing the apikey & secretapikey for the Porkbun Api. These should be seperated by a `:`.",
    ),
    "auth_string": click.option(
        "-a",
        "--auth-string",
        type=bool,
        default=False,
        is_flag=True,
        help="Display your apikey & secretapikey.",
    ),
    "id": click.option(
        "-i",
        "--id",
        type=str,
        default=None,
        help="Numeric ID of specific DNS record. Available in response to info request to Porkbun API.",
    ),
    "domain": click.option(
        "-d",
        "--domain",
        type=str,
        required=True,
        help="Domain name used to interact with. Must be authorized through Porkbun website beforehand.",
    ),
    "name": click.option(
        "-n",
        "--name",
        type=str,
        default="",
        help="The subdomain for the record being created, not including the domain itself. Omit to create a record on the root domain. Use * to create a wildcard record.",
    ),
    "type": click.option(
        "-t",
        "--type",
        type=click.Choice(VALID_DOMAIN_TYPES),
        help="The type of record being created. Valid types are: A, MX, CNAME, ALIAS, TXT, NS, AAAA, SRV, TLSA, CAA",
    ),
    "type_req": click.option(
        "-t",
        "--type",
        required=True,
        type=click.Choice(VALID_DOMAIN_TYPES),
        help="The type of record being created. Valid types are: A, MX, CNAME, ALIAS, TXT, NS, AAAA, SRV, TLSA, CAA",
    ),
    "subdomain": click.option(
        "-u", "--subdomain", type=str, help="Subdomain for record."
    ),
    "content": click.option(
        "-c",
        "--content",
        required=True,
        type=str,
        help="The answer content for the record.",
    ),
    "ttl": click.option(
        "-l",
        "--ttl",
        type=str,
        default="300",
        help="The time to live in seconds for the record. The minimum and the default is 300 seconds.",
    ),
    "priority": click.option(
        "-p",
        "--priority",
        type=str,
        default="0",
        help="The priority of the record for those that support it. Default is 0.",
    ),
    "tld": click.option(
        "-t",
        "--tld",
        type=str,
        default=None,
        multiple=True,
        help="Specific TLDs you'd like pricing for. Use multiple flags for multiple TLDs. Omit for all TLDs.",
    ),
    "ssl": click.option(
        "--ssl",
        type=bool,
        default=False,
        is_flag=True,
        help="Retrieve the SSL certificate bundle for the domain.",
    ),
    "confirm": click.option(
        "--confirm",
        required=True,
        type=bool,
        default=False,
        is_flag=True,
        help="Confirm that you want to delete this record. Must be present for action to be completed.",
    ),
}


def add_options(*options: str) -> Callable[[Any], Any]:
    opts: list[Any] = []
    for o in options:
        # TODO: Add error when option not in PORKPY_OPTIONS
        if o in PORKPY_OPTIONS:
            opts.append(PORKPY_OPTIONS[o])

    def _add_options(f: Callable) -> Callable:
        for option in reversed(opts):
            f = option(f)
        return f

    return _add_options


def get_json_response(url: str, **kwargs: Any) -> dict:
    response = requests.post(url, **kwargs)
    json_response = response.json()
    return json_response


# With our auth we want to go in order of importance:
# - command line args
# - json file (can be set by flag, but defaults to "porkpy.json" in cwd)
# - env variables ("PORKPY_SECRET" & "PORKPY_API")
class PorkAuth:
    """Call for authorizing access to Porkbun API"""

    AUTH_PAYLOAD: dict[str, Optional[str]] = {"secretapikey": None, "apikey": None}

    # what I need to do here is determine if key, and secret are both passed in
    # then check to see if they actually work by pinging the api, and if so then
    # we've got a valid auth and can proceed with whatever dumb shit we want to
    # do.
    def __init__(
        self, file: Optional[str], secrets: Optional[str] = None, **kwargs: Any
    ) -> None:
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

    def test_auth(self, ipv4: bool = False) -> tuple[bool, dict]:
        endpoint = API_ENDPOINT

        if ipv4:
            endpoint = endpoint.replace("porkbun.com", "api-ipv4.porkbun.com")

        response = get_json_response(
            API_ENDPOINT + "/ping", data=json.dumps(self.AUTH_PAYLOAD)
        )

        return (response["status"] == "SUCCESS", response)

    def auth_str(self) -> str:
        return json.dumps(self.AUTH_PAYLOAD)


class PorkRecord:
    def __init__(self, domain: str, auth: PorkAuth) -> None:
        self.domain = domain
        self.auth = auth
        return

    def retrieve(
        self, type: Optional[str] = None, subdomain: Optional[str] = None
    ) -> str:
        if type is not None and subdomain is not None:
            response = get_json_response(
                API_ENDPOINT
                + f"/dns/retrieveByNameType/{self.domain}/{type}/{subdomain}",
                data=self.auth.auth_str(),
            )
        else:
            response = get_json_response(
                API_ENDPOINT + f"/dns/retrieve/{self.domain}", data=self.auth.auth_str()
            )

        return json.dumps(response)

    def retrieve_ssl(self) -> str:
        response = get_json_response(
            API_ENDPOINT + f"/ssl/retrieve/{self.domain}", data=self.auth.auth_str()
        )

        return json.dumps(response)

    def create_record(
        self,
        type: str,
        content: str,
        name: Optional[str],
        ttl: Optional[str],
        priority: Optional[str],
        **_: Any,
    ) -> str:
        payload: dict = {
            k: v
            for (k, v) in (
                ("type", type),
                ("content", content),
                ("name", name),
                ("ttl", ttl),
                ("prio", priority),
            )
            if v is not None
        }
        payload = {**self.auth.AUTH_PAYLOAD, **payload}

        response = get_json_response(
            f"{API_ENDPOINT}/dns/create/{self.domain}", data=json.dumps(payload)
        )

        return json.dumps(response)

    def edit_record(
        self,
        id: str,
        type: str,
        subdomain: str,
        content: str,
        name: str,
        ttl: str,
        priority: str,
        **_: Any,
    ) -> str:
        return "Edit routes currently not working. To edit please pull down the pre-existing record, delete it, then create it with modified values."
        # if id is not None:
        #     payload = {
        #         k: v
        #         for (k, v) in (
        #             ("content", content),
        #             ("ttl", ttl),
        #             ("prio", priority),
        #             ("name", name),
        #             ("type", type)
        #         )
        #         if v is not None
        #     }
        #     payload = {**self.auth.AUTH_PAYLOAD, **payload}
        #     print(payload)

        #     response = get_json_response(
        #         f"{API_ENDPOINT}/dns/edit/{self.domain}/{id}",
        #         data=payload
        #     )

        #     return json.dumps(response)

        # else:
        #     payload = {
        #         k: v
        #         for (k, v) in (
        #             ("content", content),
        #             ("ttl", ttl),
        #             ("prio", priority),
        #             ("name", subdomain),
        #             ("type", type)
        #         )
        #         if v is not None
        #     }
        #     payload = {**self.auth.AUTH_PAYLOAD, **payload}

        #     response = get_json_response(
        #         f"{API_ENDPOINT}/dns/editByNameType/{self.domain}/{type}/{subdomain}",
        #         data=payload
        #     )

        #     return json.dumps(response)

    def delete_record(self, id: str, **_) -> str:
        if id is not None:
            response = get_json_response(
                f"{API_ENDPOINT}/dns/delete/{self.domain}/{id}",
                data=self.auth.auth_str(),
            )

            return json.dumps(response)


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    pass


@cli.command(name="pricing", short_help="Check pricing of TLDs")
@add_options("tld")
def pricing(tld: str) -> None:
    """
    Displays JSON response containing prices for requested TLDs. If no domains
    are provided it will provide the pricing for all domains available through
    Porkbun. Call with multiple TLD flags for a response object that contains
    pricing for only those TLDs.

    Ex: porkpy pricing -t com -t net
    """
    json_resp: dict = get_json_response(API_ENDPOINT + "/pricing/get")
    output: dict = {}

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
@add_options("file", "secrets", "auth_string")
def authorized(**kwargs: Any) -> None:
    """
    Checks to see if you are authorized to use the Porkbun API. Will return a
    JSON object containing your IP and a success status code.
    """
    auth = PorkAuth(**kwargs)

    if kwargs["auth_string"]:
        print(auth.auth_str())
    else:
        success: bool
        response: dict
        success, response = auth.test_auth()
        print(json.dumps(response))


@cli.group(help="Interact with authorized domains.")
def domain() -> None:
    """
    Provides access to manage your DNS records for authorized domains. You can
    authorize your domain with API access through the Porkbun web interface.
    """
    pass


@domain.command("info")
@add_options("domain", "ssl", "file", "secrets", "type", "subdomain")
def domain_retrieve_records(**kwargs: Any) -> None:
    """
    Displays info for the provided domain as long as you are authorized, and the
    domain has API access enabled. Will also display the SSL bundle for a given
    domain if the --ssl flag is used.
    """
    if (kwargs["type"] is None or kwargs["subdomain"] is None) and (
        kwargs["type"] != kwargs["subdomain"]
    ):
        option = "type" if (kwargs["type"] is None) else "subdomain"
        raise click.BadOptionUsage(
            option_name=option,
            message=f"Missing option: --{option}, both type and subdomain options must be provided",
        )
    if kwargs["ssl"]:
        raise click.BadOptionUsage(
            option_name="ssl",
            message="--ssl may not be used in conjunction with --type and --subdomain",
        )

    auth = PorkAuth(**kwargs)
    domain = PorkRecord(kwargs["domain"], auth)

    if kwargs["ssl"]:
        ssl: str = domain.retrieve_ssl()
        print(ssl)
    elif kwargs["type"] is not None and kwargs["subdomain"] is not None:
        record: str = domain.retrieve(kwargs["type"], kwargs["subdomain"])
        print(record)
    else:
        records: str = domain.retrieve()
        print(records)


@domain.command("create")
@add_options(
    "domain", "file", "secrets", "type_req", "content", "name", "ttl", "priority"
)
def domain_create_record(**kwargs: Any) -> None:
    """
    Creates a record for a given authorized domain.
    """
    auth = PorkAuth(**kwargs)
    domain = PorkRecord(domain=kwargs["domain"], auth=auth)
    response: str = domain.create_record(**kwargs)
    print(response)


@domain.command("edit")
@add_options(
    "domain",
    "id",
    "file",
    "secrets",
    "type_req",
    "subdomain",
    "content",
    "name",
    "ttl",
    "priority",
)
def domain_edit_records(**kwargs: Any) -> None:
    """
    THIS CURRENTLY DOES NOT WORK.

    If you'd like to edit a record please do so through the Porkbun web
    interface.
    """
    print(
        "Edit route currently not working, please use the Porkbun website to edit pre-existing records."
    )
    # if kwargs["id"] is None and kwargs["subdomain"] is None:
    #     option: str = "id" if kwargs["id"] is None else "subdomain"
    #     raise click.BadOptionUsage(
    #         option_name=option,
    #         message=f"Missing option --{option}",
    #     )
    # elif kwargs["id"] is not None and kwargs["subdomain"] is not None:
    #     raise click.BadOptionUsage(
    #         option_name="id/type", message="Cannot edit by both subdomain & id"
    #     )

    # auth = PorkAuth(**kwargs)
    # domain = PorkRecord(domain=kwargs["domain"], auth=auth)
    # response: str = domain.edit_record(**kwargs)
    # print(response)


@domain.command("delete")
@add_options("domain", "file", "secrets", "id", "confirm")
def domain_delete_records(**kwargs: Any) -> Any:
    """
    This will delete a given record for the provided domain. Which record is
    indicated by the id that is provided. To find the id of a given record use
    the `info` command.

    You must include the `confirm` flag to delete that record.
    """
    if kwargs["id"] is None:
        raise click.BadOptionUsage(
            option_name="id", message="Missing --id option, unable to delete."
        )
    if kwargs["confirm"] is False:
        raise click.BadOptionUsage(
            option_name="confirm", message="Missing --confirm option, unable to delete."
        )

    auth = PorkAuth(**kwargs)
    domain = PorkRecord(domain=kwargs["domain"], auth=auth)
    response: str = domain.delete_record(**kwargs)
    print(response)


def main() -> int:
    cli()
    return 0


if __name__ == "__main__":
    sys.exit(main())
