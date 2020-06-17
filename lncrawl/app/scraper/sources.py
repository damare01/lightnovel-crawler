# -*- coding: utf-8 -*-
"""
Auto imports all crawlers from the lncrawl.sources
"""

import importlib
import os
import re
from glob import glob
from types import ModuleType
from typing import List, Union
from urllib.parse import urlparse

from ... import sources
from .scraper import Scraper

# This list will be auto-generated
scraper_list: List[Scraper] = []


def is_rejected_source(url: str) -> bool:
    host = urlparse(url).netloc
    if host in sources.rejected_sources:
        return True
    return False


def raise_if_rejected(url: str) -> None:
    host = urlparse(url).netloc
    if host in sources.rejected_sources:
        raise Exception(sources.rejected_sources[host])


def get_scraper_by_url(url: str) -> Union[Scraper, None]:
    raise_if_rejected(url)
    parsed_url = urlparse(url)
    for scraper in scraper_list:
        for base_url in scraper.base_urls:
            if urlparse(base_url).netloc == parsed_url.netloc:
                return scraper
    return None


def get_scraper_by_name(name: str) -> Union[Scraper, None]:
    for scraper in scraper_list:
        if getattr(scraper, 'name', '') == name:
            return scraper
    return None


# To auto-import all submodules
def import_scraper(scraper_name: str, scraper_module: ModuleType):
    re_url = re.compile(r'^^(https?|ftp)://[^\s/$.?#].[^\s]*$', re.I)
    for key in dir(scraper_module):
        scraper = getattr(scraper_module, key)
        if type(scraper) != type(Scraper) or scraper.__base__ != Scraper:
            continue

        base_urls = getattr(scraper, 'base_urls')
        if not isinstance(base_urls, list):
            raise Exception(key + ': `base_urls` should be a list of strings')

        new_base_urls = []
        for url in base_urls:
            url = url.strip().strip('/')
            if re_url.match(url):
                new_base_urls.append(url)

        if len(new_base_urls) == 0:
            raise Exception(key + ': `base_urls` should contain at least one valid url')

        if any([is_rejected_source(url) for url in new_base_urls]):
            continue  # do not add rejected scraper

        instance: Scraper = scraper(scraper_name)
        instance.base_urls = new_base_urls
        scraper_list.append(instance)


def find_scrapers(path: str):
    re_module = re.compile(r'^([^_.][^.]+).py[c]?$', re.IGNORECASE)
    for file_path in glob(sources_folder + '/**/*.py', recursive=True):
        if not os.path.isfile(file_path):
            continue

        file_name = os.path.basename(file_path)
        regex_result = re_module.match(file_name)
        if not regex_result:  # does not contains a module
            continue

        rel_path = file_path[len(sources_folder) + 1:-3]
        scraper_name = rel_path.replace(os.sep, '.')
        module_name = sources.__package__ + '.' + scraper_name
        module = importlib.import_module(module_name, package=__package__)

        import_scraper(scraper_name, module)


sources_folder = os.path.abspath(getattr(sources, '__path__')[0])
find_scrapers(sources_folder)
