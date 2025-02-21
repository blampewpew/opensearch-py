# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.
#
# Modifications Copyright OpenSearch Contributors. See
# GitHub history for details.

import asyncio
import re
from datetime import datetime

import pytest
from pytest import fixture
from test_data import (
    DATA,
    FLAT_DATA,
    TEST_GIT_DATA,
    create_flat_git_index,
    create_git_index,
)

from opensearchpy._async.helpers.actions import async_bulk
from opensearchpy._async.helpers.test import get_test_client
from opensearchpy.connection.async_connections import add_connection
from test_opensearchpy.test_server.test_helpers.test_document import (
    Comment,
    History,
    PullRequest,
    User,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@fixture(scope="session")
async def client():
    client = await get_test_client(verify_certs=False, http_auth=("admin", "admin"))
    await add_connection("default", client)
    return client


@fixture(scope="session")
async def opensearch_version(client):
    info = await client.info()
    print(info)
    yield tuple(
        int(x)
        for x in re.match(r"^([0-9.]+)", info["version"]["number"]).group(1).split(".")
    )


@fixture
async def write_client(client):
    yield client
    await client.indices.delete("test-*", ignore=404)
    await client.indices.delete_template("test-template", ignore=404)


@fixture
async def data_client(client):
    # create mappings
    await create_git_index(client, "git")
    await create_flat_git_index(client, "flat-git")
    # load data
    await async_bulk(client, DATA, raise_on_error=True, refresh=True)
    await async_bulk(client, FLAT_DATA, raise_on_error=True, refresh=True)
    yield client
    await client.indices.delete("git", ignore=404)
    await client.indices.delete("flat-git", ignore=404)


@fixture
def pull_request(write_client):
    PullRequest.init()
    pr = PullRequest(
        _id=42,
        comments=[
            Comment(
                content="Hello World!",
                author=User(name="honzakral"),
                created_at=datetime(2018, 1, 9, 10, 17, 3, 21184),
                history=[
                    History(
                        timestamp=datetime(2012, 1, 1),
                        diff="-Ahoj Svete!\n+Hello World!",
                    )
                ],
            ),
        ],
        created_at=datetime(2018, 1, 9, 9, 17, 3, 21184),
    )
    pr.save(refresh=True)
    return pr


@fixture
async def setup_ubq_tests(client):
    index = "test-git"
    await create_git_index(client, index)
    await async_bulk(client, TEST_GIT_DATA, raise_on_error=True, refresh=True)
    return index
