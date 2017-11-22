# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import re
import logging
from scrapy import settings
from AcadmicGraph.items import *
from AcadmicGraph.spiders.dblp_spider import DblpSpider


# 检查PaperItem和ConferenceItem的字段，警告其中字段为空的项
class CheckNullFieldPipeline(object):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_item(self, item, spider):
        if isinstance(item, (PaperItem, ConferenceItem)):
            null_field_names = []
            for field_name, value in item.items():
                if value is None:
                    null_field_names.append(field_name)
                if len(null_field_names) > 0:
                    self.logger.warning("%s (%s) has null fields: %s [source=%s]" % (
                        item.__class__.__name__, item['title'], ', '.join(null_field_names), item['source_href']))
        return item


class ViewHrefCountingPipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        return ViewHrefCountingPipeline(crawler.settings.getint('VIEW_COUNTING_SIMPLE_SIZE'),
                                        crawler.settings.getlist('VIEW_COUNTING_LEVELS'))

    def __init__(self, simple_size, levels=None):
        self.websites = dict()
        self.pattern = re.compile("http[s]://.*/")
        self.count = 0
        self.simple_size = simple_size
        self.levels = levels
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_item(self, item, spider):
        if isinstance(item, PaperItem):
            if self.levels is not None and item['level'] not in self.levels:
                return item
            site = self.pattern.match(item['view_href']).group()
            if site not in self.websites.keys():
                self.websites[site] = {
                    'count': 0,
                    'simple': item['view_href']
                }
            self.websites[site]['count'] += 1
            self.count += 1
            if self.count % self.max_print_count == 0:
                self.logger.info("Websites in %d simples:\n%s" % (self.count, self.websites))
        return item

    def close_spider(self, spider):
        self.logger.info("Websites in %d simples:\n%s" % (self.count, self.websites))
