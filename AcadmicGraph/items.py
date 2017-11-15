# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose
from scrapy.loader.processors import Join
from scrapy import Field


class AcadmicgraphItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class JournalPaperItem(scrapy.Item):
    title = Field()
    authors = Field(input_processor=MapCompose(lambda author_name: (author_name, 'Unknown')))
    pagination = Field()
    date_published = Field()
    header = Field()
    part_of = Field()


class CCFIndexItem(scrapy.Item):
    name = Field()
    level = Field(input_processor=MapCompose(lambda origin: origin[0]))
    type = Field(input_processor=MapCompose(lambda origin: origin[-2:]))
    genre = Field()
    href = Field()
