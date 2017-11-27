# -*- coding: utf-8 -*-

import scrapy
import re
import logging
from scrapy.loader import ItemLoader
from AcadmicGraph.items import *


class DblpSpider(scrapy.Spider):
    name = "dblp"

    def __init__(self, urls=None, level='AB', *args, **kwargs):
        super(DblpSpider, self).__init__(*args, **kwargs)
        self.urls = urls
        self.crawl_level = level

    def start_requests(self):
        if self.urls is None:
            yield scrapy.Request('http://www.ccf.org.cn/xspj/gyml/', callback=self.parse)
        else:
            with open(self.urls, 'r') as url_file:
                for url in url_file:
                    if re.match('http://dblp.uni-trier.de/db/conf/', url):
                        yield scrapy.Request(url, callback=self.parse_dblp_conf, meta={'part_of': None})
                    elif re.match('http://dblp.uni-trier.de/db/journals/', url):
                        yield scrapy.Request(url, callback=self.parse_dblp_journals, meta={'part_of': None})

    def parse(self, response):
        disciplines = response.css(".m-snv li a::text")[2:-1].extract()
        discipline_link = response.css(".m-snv li a::attr(href)")[2:-1]
        for index in range(0, len(discipline_link)):
            yield response.follow(discipline_link[index], callback=self.parse_discipline,
                                  meta={'genre': disciplines[index]})

    # 爬取CCF推荐目录的各个领域分类目录
    def parse_discipline(self, response):
        links = response.css(".x-list3 a")
        for link in links:
            name = link.xpath("../preceding-sibling::div[2]/text()").extract_first()
            short_name = link.xpath("../preceding-sibling::div[3]/text()").extract_first()
            publisher = link.xpath("../preceding-sibling::div[1]/text()").extract_first()
            level = link.xpath("../../../preceding-sibling::h3[1]/text()").extract_first()
            type = link.xpath("../../../preceding-sibling::h4[2]/text()").extract_first()
            href = link.css("::attr(href)").extract_first()
            level = re.match('\w', level).group()
            if type == '中国计算机学会推荐国际学术刊物':
                type = 'journal'
            elif type == '中国计算机学会推荐国际学术会议':
                type = 'conference'
            if level in self.crawl_level:
                if re.match('http://dblp.uni-trier.de/db/conf/', href):
                    yield scrapy.Request(href, callback=self.parse_dblp_conf,
                                         meta={"part_of": name, "level": level, "genre": response.meta['genre'],
                                               "type": type, "short_name": short_name, "publisher": publisher})
                elif re.match('http://dblp.uni-trier.de/db/journals/', href):
                    yield scrapy.Request(href, callback=self.parse_dblp_journals,
                                         meta={"part_of": name, "level": level, "genre": response.meta['genre'],
                                               "type": type, "short_name": short_name, "publisher": publisher})

    # 爬取会议目录
    def parse_dblp_conf(self, response):
        confs = response.css(".data")
        for conf in confs:
            title = conf.css(".title::text").extract_first()
            publisher = conf.css("span[itemprop=publisher]::text").extract_first()
            datePublished = conf.css("span[itemprop=datePublished]::text").extract_first()
            isbn = conf.css("span[itemprop=isbn]::text").extract_first()
            authors = conf.xpath("span[@itemprop='author']//*/text()").extract()
            contents = conf.xpath('./a[re:test(text(),"contents")]/@href').extract_first()
            yield ConferenceItem(
                title=title,
                publisher=publisher,
                date_published=datePublished,
                isbn=isbn,
                authors=authors,
                part_of=response.meta['part_of'],
                source_href=response.url,
                level=response.meta['level'],
                type=response.meta['type'],
                genre=response.meta['genre'],
                short_name=response.meta['short_name']
            )
            if contents is not None and re.match('http://dblp.uni-trier.de/db/conf/', contents):
                yield scrapy.Request(contents, callback=self.parse_dblp_conf_details,
                                     meta={"part_of": title, "level": response.meta["level"]})

    # 爬取会议详细文章列表
    def parse_dblp_conf_details(self, response):
        papers = response.css(".data")
        for paper in papers[1::]:
            title = paper.css("span.title::text").extract_first()
            authors = paper.xpath("span[@itemprop='author']//*/text()").extract()
            date_published = paper.xpath("meta[@itemprop='datePublished']/@content").extract_first()
            pagination = paper.css("span[itemprop=pagination]::text").extract_first()
            view_href = paper.xpath(
                './preceding-sibling::nav[@class="publ"][1]/ul/li[1]/div[@class="head"]/a/@href').extract_first()
            loader = ItemLoader(item=PaperItem(), response=response)
            loader.add_value("title", title)
            loader.add_value("authors", list(map(lambda author: "%s:%s" % (author, 'Unknown'), authors)))
            loader.add_value("pagination", pagination)
            loader.add_value("date_published", date_published)
            loader.add_value("part_of", response.meta['part_of'])
            loader.add_value("source_href", response.url)
            loader.add_value("view_href", view_href)
            loader.add_value("type", "paper")
            loader.add_value("level", response.meta['level'])
            item = loader.load_item()
            if view_href is not None:
                yield scrapy.Request(view_href, callback=self.parse_paper_detail_general,
                                     meta={"item": item, "dont_obey_robotstxt": True})
            else:
                yield item

    # 爬取期刊目录
    def parse_dblp_journals(self, response):
        volumes = response.css(".clear-both~ ul a")
        for volume in volumes:
            title = volume.xpath('../../preceding-sibling::header[1]/*/text()').extract_first()
            item = JournalItem(
                title=title,
                publisher=response.meta['publisher'],
                level=response.meta['level'],
                genre=response.meta['genre'],
                short_name=response.meta['short_name'],
                part_of=response.meta['part_of'],
                source_href=response.url,
                type=response.meta['type']
            )
            link = volume.css('::attr(href)').extract_first()
            if re.match('http://dblp.uni-trier.de/db/journals/', link):
                yield scrapy.Request(link, callback=self.parse_dblp_journals_details,
                                     meta={'item': item, 'part_of': title, "level": response.meta['level']})

    # 爬取期刊文章列表
    def parse_dblp_journals_details(self, response):
        papers = response.css(".data")
        journal_headers = set()
        for paper in papers:
            title = paper.css("span.title::text").extract_first()
            pagination = paper.css("span[itemprop=pagination]::text").extract_first()
            authors = paper.xpath("span[@itemprop='author']//*/text()").extract()
            date_published = paper.xpath("meta[@itemprop='datePublished']/@content").extract_first()
            headers = paper.xpath("../../preceding-sibling::header[1]/*/text()").extract_first()
            view_href = paper.xpath(
                './preceding-sibling::nav[@class="publ"][1]/ul/li[1]/div[@class="head"]/a/@href').extract_first()
            if headers not in journal_headers:
                journal_headers.add(headers)
                headers = headers.split(",")
                journal_item = response.meta['item'].copy()
                journal_item['volume'] = headers[0]
                journal_item['date_published'] = headers[-1]
                if len(headers) == 3:
                    journal_item['number'] = headers[1]
                else:
                    journal_item['number'] = 'none'
                yield journal_item
            loader = ItemLoader(item=PaperItem(), response=response)
            loader.add_value("title", title)
            loader.add_value("authors", list(map(lambda author: "%s:%s" % (author, 'Unknown'), authors)))
            loader.add_value("pagination", pagination)
            loader.add_value("date_published", date_published)
            loader.add_value("part_of", response.meta['part_of'])
            loader.add_value("view_href", view_href)
            loader.add_value("source_href", response.url)
            loader.add_value("level", response.meta['level'])
            loader.add_value("type", "paper")
            item = loader.load_item()
            if view_href is not None:
                yield scrapy.Request(view_href, callback=self.parse_paper_detail_general,
                                     meta={"item": item, "dont_obey_robotstxt": True})
            else:
                yield item

    def parse_paper_detail_general(self, response):
        item = response.meta['item']
        item['view_href'] = response.url
        yield item