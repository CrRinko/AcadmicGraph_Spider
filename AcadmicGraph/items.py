# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field
from scrapy.loader.processors import Join
from scrapy.loader.processors import MapCompose


# 文章
class PaperItem(scrapy.Item):
    title = Field()
    authors = Field(input_processor=MapCompose(lambda author_name: (author_name, 'Unknown')))
    pagination = Field()
    date_published = Field()
    header = Field(input_processor=MapCompose(lambda header: header), output_processor=Join(", "))
    part_of = Field()
    source_href = Field()  # 数据来源地址


# 会议
class ConferenceItem(scrapy.Item):
    title = Field()
    publisher = Field()
    date_published = Field()
    isbn = Field()
    authors = Field()
    part_of = Field()
    source_href = Field()  # 数据来源地址


# CCF推荐目录上的会议/期刊
class CCFIndexItem(scrapy.Item):
    name = Field()
    level = Field(input_processor=MapCompose(lambda origin: origin[0]))
    type = Field(input_processor=MapCompose(lambda origin: origin[-2:]))
    genre = Field()
    href = Field()
