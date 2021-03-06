# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


# 论文
class PaperItem(scrapy.Item):
    title = Field()
    authors = Field()
    pagination = Field()
    date_published = Field()
    part_of = Field()
    source_href = Field()  # 数据来源地址
    view_href = Field()
    level = Field()
    type = Field()
    # citation_count=Field()
    affiliation = Field()


# 会议
class ConferenceItem(scrapy.Item):
    title = Field()
    sub_title = Field()
    publisher = Field()
    date_published = Field()
    isbn = Field()
    authors = Field()
    # part_of = Field()
    source_href = Field()  # 数据来源地址
    level = Field()
    type = Field()
    genre = Field()
    short_name = Field()


# 期刊
class JournalItem(scrapy.Item):
    title = Field()
    # volume = Field()
    # number = Field()
    # date_published = Field()
    # part_of = Field()
    source_href = Field()  # 数据来源地址
    publisher = Field()
    level = Field()
    type = Field()
    genre = Field()
    short_name = Field()
