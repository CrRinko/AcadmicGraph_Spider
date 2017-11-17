# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import logging
from AcadmicGraph.items import *
from AcadmicGraph.spiders.dblp_spider import DblpSpider


# 检查PaperItem和ConferenceItem的字段，警告其中字段为空的项
class CheckNullFieldPipeline(object):
    def __init__(self):
        self.logger = logging.getLogger("check_null_field")

    def process_item(self, item, spider):
        if isinstance(spider, DblpSpider):
            if isinstance(item, (PaperItem, ConferenceItem)):
                null_field_names = []
                for field_name, value in item.items():
                    if value is None:
                        null_field_names.append(field_name)
                    if len(null_field_names) > 0:
                        self.logger.warning("%s (%s) has null fields: %s [source=%s]" % (
                            item.__class__.__name__, item['title'], ', '.join(null_field_names), item['source_href']))
        return item
