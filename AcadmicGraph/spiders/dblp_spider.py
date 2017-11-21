# -*- coding: utf-8 -*-

import scrapy
import re
import logging
from scrapy.loader import ItemLoader
from AcadmicGraph.items import *


class DblpSpider(scrapy.Spider):
    name = "dblp"

    def __init__(self, urls=None, *args, **kwargs):
        super(DblpSpider, self).__init__(*args, **kwargs)
        self.urls = urls

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
            name = link.xpath("../preceding-sibling::div[2]/text()").extract()
            level = link.xpath("../../../preceding-sibling::h3[1]/text()").extract()
            type = link.xpath("../../../preceding-sibling::h4[2]/text()").extract()
            href = link.css("::attr(href)").extract_first()
            loader = ItemLoader(item=CCFIndexItem(), response=response)
            loader.add_value("name", name)
            loader.add_value("level", level)
            loader.add_value("type", type)
            loader.add_value("genre", response.meta['genre'])
            loader.add_value("href", href)
            yield loader.load_item()
            if re.match('http://dblp.uni-trier.de/db/conf/', href):
                yield scrapy.Request(href, callback=self.parse_dblp_conf, meta={"part_of": name, "level": level})
            elif re.match('http://dblp.uni-trier.de/db/journals/', href):
                yield scrapy.Request(href, callback=self.parse_dblp_journals, meta={'part_of': name, "level": level})

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
                source_href=response.url
            )
            if re.match('http://dblp.uni-trier.de/db/conf/', contents):
                meta = response.meta.copy()
                meta['part_of'] = title
                yield scrapy.Request(contents, callback=self.parse_dblp_conf_details, meta=meta)

    # 爬取会议详细文章列表
    def parse_dblp_conf_details(self, response):
        papers = response.css(".data")
        for paper in papers[1::]:
            title = paper.css("span.title::text").extract_first()
            authors = paper.xpath("span[@itemprop='author']//*/text()").extract()
            date_published = paper.xpath("meta[@itemprop='datePublished']/@content").extract_first()
            headers = [
                paper.xpath("../../preceding-sibling::header[h2][1]//text()").extract_first(),
                paper.xpath("../../preceding-sibling::header[h3][1]//text()").extract_first(),
            ]
            pagination = paper.css("span[itemprop=pagination]::text").extract_first()
            view_href = paper.xpath(
                './preceding-sibling::nav[@class="publ"][1]/ul/li[1]/div[@class="head"]/a/@href').extract_first()
            loader = ItemLoader(item=PaperItem(), response=response)
            loader.add_value("title", title)
            loader.add_value("authors", authors)
            loader.add_value("pagination", pagination)
            loader.add_value("date_published", date_published)
            loader.add_value("header", headers)
            loader.add_value("part_of", response.meta['part_of'])
            loader.add_value("source_href", response.url)
            loader.add_value("view_href", view_href)
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
            header = volume.xpath('../../preceding-sibling::header[1]/*/text()').extract_first()
            link = volume.css('::attr(href)').extract_first()
            if re.match('http://dblp.uni-trier.de/db/journals/', link):
                meta = response.meta.copy()
                meta['header'] = header
                yield scrapy.Request(link, callback=self.parse_dblp_journals_details, meta=meta)

    # 爬取期刊文章列表
    def parse_dblp_journals_details(self, response):
        papers = response.css(".data")
        for paper in papers:
            title = paper.css("span.title::text").extract_first()
            pagination = paper.css("span[itemprop=pagination]::text").extract_first()
            authors = paper.xpath("span[@itemprop='author']//*/text()").extract()
            date_published = paper.xpath("meta[@itemprop='datePublished']/@content").extract_first()
            headers = [response.meta['header'],
                       paper.xpath("../../preceding-sibling::header[1]/*/text()").extract_first()]
            view_href = paper.xpath(
                './preceding-sibling::nav[@class="publ"][1]/ul/li[1]/div[@class="head"]/a/@href').extract_first()
            loader = ItemLoader(item=PaperItem(), response=response)
            loader.add_value("title", title)
            loader.add_value("authors", authors)
            loader.add_value("pagination", pagination)
            loader.add_value("date_published", date_published)
            loader.add_value("header", headers)
            loader.add_value("part_of", response.meta['part_of'])
            loader.add_value("view_href", view_href)
            loader.add_value("level", response.meta['level'])
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

    def errback_robots_forbidden(self, failure):
        logging.error(failure)
