# -*- coding: utf-8 -*-

import scrapy
import re
from scrapy.loader import ItemLoader
from AcadmicGraph.items import JournalPaperItem
from AcadmicGraph.items import CCFIndexItem


class DblpSpider(scrapy.Spider):
    name = "dblp"
    start_urls = ['http://www.ccf.org.cn/xspj/gyml/']

    def parse(self, response):
        disciplines = response.css(".m-snv li a::text")[2:-1].extract()
        discipline_link = response.css(".m-snv li a::attr(href)")[2:-1]
        for index in range(0, len(discipline_link)):
            yield response.follow(discipline_link[index], callback=self.parse_discipline,
                                  meta={'genre': disciplines[index]})

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
            # yield CCFIndexItem(name=name,level=level,type=type,genre=response.meta['genre'],href=href)
            # if(re.match('http://dblp.uni-trier.de/db/conf/',href)):
            #     yield scrapy.Request(href,callback=self.parse_dblp_conf,meta={
            #         'genre':response.meta['genre'],
            #         'publication':name,
            #         'level':level,
            #         'type':type
            #     })
            if (re.match('http://dblp.uni-trier.de/db/journals/', href)):
                yield scrapy.Request(href, callback=self.parse_dblp_journals, meta={'part_of': name})

    def parse_dblp_conf(self, response):
        confs = response.css(".data")
        for conf in confs:
            title = conf.css(".title::text").extract_first()
            publisher = conf.css("span[itemprop=publisher]::text").extract_first()
            datePublished = conf.css("span[itemprop=datePublished]::text").extract_first()
            isbn = conf.css("span[itemprop=isbn]::text").extract_first()
            contents = conf.xpath('./a[re:test(text(),"contents")]/@href').extract_first()
            if re.match('http://dblp.uni-trier.de/db/conf/', contents):
                pass

    def parse_dblp_journals(self, response):
        volumes = response.css(".clear-both~ ul a")
        for volume in volumes:
            header = volume.xpath('../../preceding-sibling::header[1]/*/text()').extract_first()
            link = volume.css('::attr(href)').extract_first()
            if re.match('http://dblp.uni-trier.de/db/journals/', link):
                meta = response.meta.copy()
                meta['header'] = header
                yield scrapy.Request(link, callback=self.parse_dblp_journals_details, meta=meta)

    def parse_dblp_journals_details(self, response):
        papers = response.css(".data")
        for paper in papers:
            title = paper.css("span.title::text").extract_first()
            pagination = paper.css("span[itemprop=pagination]::text").extract_first()
            authors = paper.xpath("span[@itemprop='author']//*/text()").extract()
            date_published = paper.xpath("meta[@itemprop='datePublished']/@content").extract_first()
            header = paper.xpath("../../preceding-sibling::header[1]/*/text()").extract_first()
            loader = ItemLoader(item=JournalPaperItem(), response=response)
            loader.add_value("title", title)
            loader.add_value("authors", authors)
            loader.add_value("pagination", pagination)
            loader.add_value("date_published", date_published)
            loader.add_value("header", response.meta['header'] + ', ' + header)
            loader.add_value("part_of", response.meta['part_of'])
            yield loader.load_item()
