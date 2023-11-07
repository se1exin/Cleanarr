#!/usr/bin/env python3
#
# this file is meant for local development only. it expects a populated .env file
# with connection details to a valid plex server. it can be run via pytest, which
# will run multiple iterations and rounds of the get_dupe_content method, or can
# be invoked directly with ./backend/benchmark.py to simply run get_dupe_content()
# and print traces to stdout (note: traces only available if DEBUG=1 set)

import pytest
import time
from plexwrapper import PlexWrapper
from utils import print_top_traces
from dotenv import load_dotenv

load_dotenv()

def get_dupe_content():
    PlexWrapper().get_dupe_content()

def test_get_dupe_content(benchmark):
    benchmark.pedantic(get_dupe_content, iterations=10, rounds=3)


# allow for direct invocation, without pytest
if __name__ == "__main__":
    get_dupe_content()
    print_top_traces(10)
