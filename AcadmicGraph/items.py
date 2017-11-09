# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import Join


class AcadmicgraphItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class PaperItem(scrapy.Item):
    title = scrapy.Field()
    authors = scrapy.Field(output_processor=Join(','))
    pagination = scrapy.Field()
    date_published = scrapy.Field()
    headers = scrapy.Field(output_processor=Join(','))
    genre = scrapy.Field()
    publication = scrapy.Field()
    level = scrapy.Field()
    type = scrapy.Field()
