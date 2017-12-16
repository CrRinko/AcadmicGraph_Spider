# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import re
import logging
from AcadmicGraph.items import *


# 检查PaperItem和ConferenceItem的字段，警告其中字段为空的项
class CheckNullFieldPipeline(object):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_item(self, item, spider):
        if isinstance(item, (PaperItem, ConferenceItem, JournalItem)):
            null_field_names = []
            for field_name in item.fields:
                if field_name not in item or item[field_name] is None or item[field_name] == '' or item[
                    field_name] == [] or item[field_name] == ['']:
                    null_field_names.append(field_name)
                    item[field_name] = None
            if len(null_field_names) > 0:
                self.logger.warning("%s (%s) has null fields: %s [source=%s]" % (
                    item.__class__.__name__, item['title'], ', '.join(null_field_names), item['source_href']))
        return item


# 统计论文详情页的网站分布
class ViewHrefCountingPipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        return ViewHrefCountingPipeline(crawler.settings.getint('VIEW_COUNTING_SIMPLE_SIZE'))

    def __init__(self, simple_size):
        self.websites = dict()
        self.pattern = re.compile(
            "^((http://)|(https://))?([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}(:\d+)?(/)")
        self.count = 0
        self.simple_size = simple_size
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_item(self, item, spider):
        if isinstance(item, PaperItem) and "view_href" in item and item["view_href"] is not None:
            site = self.pattern.match(item['view_href']).group()
            if site not in self.websites.keys():
                self.websites[site] = {
                    'count': 0,
                    'simple': item['view_href']
                }
            self.websites[site]['count'] += 1
            self.count += 1
            if self.count % self.simple_size == 0:
                self.logger.info("Websites in %d simples:\n%s" % (self.count, self.websites))
        return item

    def close_spider(self, spider):
        self.logger.info("Websites in %d simples:\n%s" % (self.count, self.websites))
