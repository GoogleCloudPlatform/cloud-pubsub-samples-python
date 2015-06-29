#!/usr/bin/env python
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Utility for caching the discovery doc.

TODO: Make it an independent library and upload it to pypi.
"""


import datetime
import hashlib
import json
import os

from time import mktime

# Libraries used by or included with Google API Client Library for Python
from apiclient.discovery import _add_query_parameter
from apiclient.discovery import build_from_document
from apiclient.discovery import DISCOVERY_URI
from apiclient.errors import HttpError
from apiclient.errors import InvalidJsonError
import httplib2
import uritemplate


DISCOVERY_DOC_MAX_AGE = datetime.timedelta(hours=24)


def cache_file_name(service_name, version, discovery_service_url):
    """Returns the cache file name."""
    filename = 'discovery-doc-%s-%s-%s.json' % (
        hashlib.sha224(discovery_service_url).hexdigest(),
        service_name, version)
    return os.path.join(os.path.dirname(__file__), filename)


class DiscoveryDoc(object):
    """Representing the discovery document."""

    def __init__(self, document, service_name, version, updated=None,
                 discovery_service_url=DISCOVERY_URI):
        self.document = document
        self.service_name = service_name
        self.version = version
        self.updated = updated or datetime.datetime.now()
        self.discovery_service_url = discovery_service_url

    def save(self):
        """Saves the discovery doc to a cache file."""
        filename = cache_file_name(self.service_name, self.version,
                                   self.discovery_service_url)
        updated = int(mktime(self.updated.timetuple()))
        try:
            with open(filename, 'wb') as f:
                json.dump(
                    {"document": self.document, "updated": updated}, f)
        except IOError:
            # Failed to save, ignoring
            pass
        return

    @property
    def expired(self):
        """Returns True if the discovery doc is expired."""
        now = datetime.datetime.utcnow()
        return now - self.updated > DISCOVERY_DOC_MAX_AGE

    @classmethod
    def read_from_cache(cls, service_name, version,
                        discovery_service_url=DISCOVERY_URI):
        """Reads cache file and returns the cached discovery doc."""
        filename = cache_file_name(service_name, version,
                                   discovery_service_url)
        ret = None
        try:
            with open(filename, 'rb') as f:
                dat = json.load(f)
                updated = datetime.datetime.fromtimestamp(dat['updated'])
                ret = cls(dat['document'], service_name, version,
                          updated=updated,
                          discovery_service_url=discovery_service_url)
            print "Read from the cache"
        except IOError:
            # File not found, ignoring
            pass
        return ret

    @classmethod
    def build(cls, service_name, version, **kwargs):
        """Builds the client object."""
        discovery_service_url = kwargs.pop('discovery_service_url',
                                           DISCOVERY_URI)
        discovery_doc = DiscoveryDoc.read_from_cache(service_name, version,
                                                     discovery_service_url)
        if discovery_doc is None or discovery_doc.expired:
            # If None, retrieve_discovery_doc() will use default
            http = kwargs.get('http')
            discovery_doc = retrieve_discovery_doc(
                service_name, version, http=http,
                discovery_service_url=discovery_service_url)
            discovery_doc.save()

        return build_from_document(discovery_doc.document, **kwargs)


def retrieve_discovery_doc(service_name, version, http=None,
                           discovery_service_url=DISCOVERY_URI):
    """Retrieves the discovery doc."""
    params = {'api': service_name, 'apiVersion': version}
    requested_url = uritemplate.expand(discovery_service_url, params)

    # REMOTE_ADDR is defined by the CGI spec [RFC3875] as the environment
    # variable that contains the network address of the client sending the
    # request. If it exists then add that to the request for the discovery
    # document to avoid exceeding the quota on discovery requests.
    if 'REMOTE_ADDR' in os.environ:
        requested_url = _add_query_parameter(requested_url, 'userIp',
                                             os.environ['REMOTE_ADDR'])

    http = http or httplib2.Http()
    resp, content = http.request(requested_url)
    if resp.status >= 400:
        raise HttpError(resp, content, uri=requested_url)

    try:
        json.loads(content)
    except ValueError:
        raise InvalidJsonError(
            'Bad JSON: %s from %s.' % (content, requested_url))

    # we return content instead of the JSON deserialized service because
    # build_from_document() consumes a string rather than a dictionary
    return DiscoveryDoc(content, service_name, version,
                        updated=datetime.datetime.now(),
                        discovery_service_url=discovery_service_url)
