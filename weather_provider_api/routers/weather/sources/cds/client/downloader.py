#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.
#
# 2019: Modified version by Alliander to improve scalability.

import json
import os
import time
from pathlib import Path

import requests
from loguru import logger


def bytes_to_string(n):
    u = ["", "K", "M", "G", "T", "P"]
    i = 0
    while n >= 1024:
        n /= 1024.0
        i += 1
    return "%g%s" % (int(n * 10 + 0.5) / 10.0, u[i])


def read_rc_file(path: Path):
    config = {}
    with open(path) as f:
        for line in f.readlines():
            if ":" in line:
                k, v = line.strip().split(":", 1)
                if k in ("url", "key", "verify"):
                    config[k] = v.strip()
    return config


class Result(object):
    def __init__(self, client, reply):
        self.reply = reply
        self._url = client.api_url
        self.session = client.session
        self.robust = client.robust
        self.verify = client.api_verify
        self.cleanup = client.delete
        self._deleted = False

    def _download(self, url: str, size, target):
        if not target:
            target = url.split("/")[-1]

        logger.info(f"Downloading [{url}] to [{target}]. ({bytes_to_string(size)})")
        start = time.time()

        r = self.robust(requests.get)(url, stream=True, verify=self.verify)
        try:
            r.raise_for_status()
            total = 0

            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
        finally:
            r.close()

        if total != size:
            raise EOFError(f"Download failed due to incorrect file size: Downloaded {total} byte(s) out of {size}")

        elapsed = time.time() - start
        if elapsed:
            logger.info(f"Download rate: {bytes_to_string(size / elapsed)} bytes per second")
        return target

    def download(self, target=None):
        return self._download(self.location, self.content_length, target)

    @property
    def content_length(self):
        return int(self.reply["content_length"])

    @property
    def location(self):
        return self.reply["location"]

    @property
    def content_type(self):
        return self.reply["content_type"]

    def __repr__(self):
        return (
            f"Result(content_length={self.content_length}, content_type={self.content_type}, "
            f"location={self.location})"
        )

    def check(self):
        logger.debug(f'HEAD {self.reply["location"]}')
        metadata = self.robust(self.session.head)(self.reply["location"], verify=self.verify)
        metadata.raise_for_status()

    def delete(self):
        if self._deleted:
            return

        if "request_id" in self.reply:
            rid = self.reply("request_id")
            task_url = f"{self._url}/tasks/{rid}"

            delete = self.session.delete(task_url, verify=self.verify)
            logger.debug(f"DELETE returns: ({delete.status_code}) {delete.reason}")

            try:
                delete.raise_for_status()
            except RuntimeError:
                logger.warning(f"DELETE [{task_url}] returns: ({delete.status_code}) {delete.reason}")

            self._deleted = True

    def __del__(self):
        try:
            if self.cleanup:
                self.delete()
        except Exception as e:
            logger.error(e)
            raise e


class CDSDownloadClient(object):
    def __init__(
        self,
        url: str = os.environ.get("CDSAPI_URL"),
        key: str = os.environ.get("CDSAPI_KEY"),
        verify=None,
        timeout=None,
        full_stack: bool = False,
        delete: bool = False,
        retry_max: int = 500,
        sleep_max: int = 120,
        info_callback=None,
        warning_callback=None,
        error_callback=None,
        debug_callback=None,
        persist_request_callback=None,
    ):
        self.api_url, self.api_key, self.api_verify = self._load_cdsapi_config(url, key, verify)

        self.timeout = timeout
        self.sleep_max = sleep_max
        self.retry_max = retry_max
        self.full_stack = full_stack
        self.delete = delete
        self.last_state = None

        # Callbacks:
        self.info_callback = info_callback
        self.debug_callback = debug_callback
        self.warning_callback = warning_callback
        self.error_callback = error_callback
        self.persist_request_callback = persist_request_callback

        #
        self.persisted_request = False
        self.session = requests.Session()
        self.session.auth = tuple(self.api_key.split(":", 2))

        settings_dict = dict(
            url=self.api_url,
            key=self.api_key,
            verify=self.api_verify,
            timeout=self.timeout,
            sleep_max=self.sleep_max,
            retry_max=self.retry_max,
            full_stack=self.full_stack,
            delete=self.delete,
        )

        logger.debug(f"CDSAPI Downloader Settings: {settings_dict}")

    def retrieve(self, name, request, target=None, request_id=None):
        """This function retrieves a download-result and stores it at the target location if given."""
        logger.info(f"Starting retrieval of URL:{self.api_url}/resources/{name}")
        result = self._request_retrieval(
            f"{self.api_url}/resources/{name}", request, request_id if request_id else None
        )
        if target:
            result.download(target)
        return result

    def _request_retrieval(self, url, request, request_id=None):
        reply = self._request_handler(url, request, request_id)

        sleep = 1
        start = time.time()

        while True:
            logger.debug(f"REPLY: {reply}")

            reply_state = reply["state"]

            if reply_state != self.last_state:
                logger.info(f"Request is: {reply_state}")
                self.last_state = reply_state

            if reply_state == "completed":
                logger.debug("Request completed!")
                return Result(self, reply)

            if reply_state in ("queued", "running", "resuming_download"):
                sleep, reply = self._active_request_handler(reply, url, request, request_id, start, sleep)
                continue

            if reply_state == "failed":
                logger.error(f"An error occurred: {reply['error'].get('message')}")
                logger.error(f"The following reason was given: {reply['error'].get('reason')}")

                for part in reply.get("error", {}).get("context", {}).get("traceback", "").split("\n"):
                    if part.strip() == "" and not self.full_stack:
                        break
                    logger.error(f" {part}")

                raise RuntimeError(f'{reply["error"].get("message")} | {reply["error"].get("reason")}')

            raise RuntimeError(f"UNKNOWN API STATE: [{reply_state}]")

    def _request_handler(self, url, request, request_id):
        if request_id is None:
            logger.info(f"Sending request to {url}")
            logger.debug(f"POST {url} {json.dumps(request)}")

            result = self.robust(self.session.post)(url, json=request, verify=self.api_verify)
            reply = None

            try:
                result.raise_for_status()
                reply = result.json()
            except RuntimeError:
                if reply is None:
                    try:
                        reply = result.json()
                    except RuntimeError:
                        reply = dict(message=result.text)
                logger.debug(json.dumps(reply))

                if "message" in reply:
                    error = reply["message"]

                    if "context" in reply and "required_terms" in reply["context"]:
                        e = [error]
                        for term in reply["context"]["required_terms"]:
                            e.append(
                                f"To access this resource, you'll first need to accept the terms of {term['title']} "
                                f"at: {term['url']}"
                            )
                            error = ". ".join(e)
                    raise RuntimeError(error)
                else:
                    raise RuntimeError("An unknown error occurred...")
        else:
            logger.info("Resuming the download task and skipping initial request to API.")
            reply = {"state": "resuming_download", "request_id": request_id}

        return reply

    def _active_request_handler(self, reply, url, request, request_id, start, sleep):
        rid = reply["request_id"]  # Other Request ID?

        if self.persist_request_callback and not self.persisted_request:
            self.persist_request_callback(url=url, request=request, request_id=request_id, start_timestamp=start)
            self.persisted_request = True

        if self.timeout and (time.time() - start > self.timeout):
            raise TimeoutError("Request Timed Out!")

        logger.debug(f"The Request ID is {rid} (sleeping for {sleep} seconds)")
        time.sleep(sleep)
        sleep *= 1.5

        sleep = self.sleep_max if sleep > self.sleep_max else sleep

        task_url = f"{self.api_url}/tasks/{rid}"
        logger.debug(f"GET: {task_url}")

        result = self.robust(self.session.get)(task_url, verify=self.api_verify)
        result.raise_for_status()
        reply = result.json()
        return sleep, reply

    @staticmethod
    def _load_cdsapi_config(url, key, verify):
        dotrc_file = Path(os.environ.get("CDSAPI_RC", str(Path.home().joinpath(".cdsapirc"))))
        cdsapi_key = os.environ.get("CDSAPI_KEY", None)
        cdsapi_url = os.environ.get("CDSAPI_URL", None)

        # Prefer the CDSAPI RC file over CDSAPI_KEY and CDSAPI_URL:
        if (not url or not key) and dotrc_file.exists():
            logger.debug("CDS API [.rc]-file exists. ")
            config = read_rc_file(dotrc_file)

            if not key:
                key = config.get("key")
            if not url:
                url = config.get("url")
            if not verify:
                verify = int(config.get("verify", 1))

        # If key or url are still missing try using CDSAPI_KEY and/or CDSAPI_URL:
        if (not url or not key) and cdsapi_key and cdsapi_url:
            key = cdsapi_key
            url = cdsapi_url

        # If key or url are still missing, or no verify status was passed, exit with error:
        if not url or not key or not verify:
            raise AttributeError(
                f"Missing or incomplete configuration. "
                f"Please create or verify the file at [{dotrc_file}], or create/verify "
                f"the CDSAPI_KEY and CDSAPI_URL environment variables."
            )
        logger.info("Successfully loaded settings for the CDS Downloader!")

        return url, key, True if verify else False

    def robust(self, call):
        def retryable(code, reason):
            if code in [
                requests.codes.internal_server_error,
                requests.codes.bad_gateway,
                requests.codes.service_unavailable,
                requests.codes.gateway_timeout,
                requests.codes.too_many_requests,
                requests.codes.request_timeout,
            ]:
                return True
            logger.debug(f"The current response code is considered not retryable: ({code}) {reason}")
            return False

        def wrapped(*args, **kwargs):

            tries = 0
            while tries < self.retry_max:
                logger.info(f"WRAPPED [Tries: {tries} ({self.retry_max})]")
                try:
                    r = call(*args, **kwargs)
                except requests.exceptions.ConnectionError as e:
                    r = None
                    logger.warning(f"Recovering from ConnectionError [{e}]. (Attempt #{tries}) of {self.retry_max})")
                if r:
                    if not retryable(r.status_code, r.reason):
                        return r
                    logger.warning(
                        f"Recovering from HTTPError [{r.status_code, r.reason}]. "
                        f"(Attempt #{tries} of {self.retry_max})"
                    )

                tries += 1
                logger.warning(f"Retrying after {self.sleep_max} seconds..")
                time.sleep(self.sleep_max)

        return wrapped
