# -*- coding: utf-8 -*-

import scrapy
import re
from scrapy.loader import ItemLoader
from AcadmicGraph.items import PaperItem


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
            # if(re.match('http://dblp.uni-trier.de/db/conf/',href)):
            #     yield scrapy.Request(href,callback=self.parse_dblp_conf,meta={
            #         'genre':response.meta['genre'],
            #         'publication':name,
            #         'level':level,
            #         'type':type
            #     })
            if (re.match('http://dblp.uni-trier.de/db/journals/', href)):
                yield scrapy.Request(href, callback=self.parse_dblp_journals, meta={
                    'genre': response.meta['genre'],
                    'publication': name,
                    'level': level,
                    'type': type
                })

    def parse_dblp_conf(self, response):
        pass

    def parse_dblp_journals(self, response):
        volumes = response.css(".clear-both~ ul a")
        for volume in volumes:
            header = volume.xpath('../../preceding-sibling::header[1]/*/text()').extract_first()
            link = volume.css('::attr(href)').extract_first()
            if re.match('http://dblp.uni-trier.de/db/journals/', link):
                meta = response.meta.copy()
                if "header" not in meta:
                    meta["header"] = []
                meta["header"].append(header)
                yield scrapy.Request(link, callback=self.parse_dblp_journals_details, meta=meta)

    def parse_dblp_journals_details(self, response):
        papers = response.css(".data")
        for paper in papers:
            title = paper.css("span.title::text").extract_first()
            pagination = paper.css("span[itemprop=pagination]::text").extract_first()
            authors = paper.xpath("span[@itemprop='author']//*/text()").extract()
            date_published = paper.xpath("meta[@itemprop='datePublished']/@content").extract_first()
            header = paper.xpath("../../preceding-sibling::header[1]/*/text()").extract_first()
            paper_loader = ItemLoader(item=PaperItem(), response=response)
            paper_loader.add_value("title", title)
            paper_loader.add_value("authors", authors)
            paper_loader.add_value("pagination", pagination)
            paper_loader.add_value("date_published", date_published)
            paper_loader.add_value("headers", response.meta['header'] + [header])
            paper_loader.add_value("genre", response.meta['genre'])
            paper_loader.add_value("publication", response.meta['publication'])
            paper_loader.add_value("level", response.meta["level"])
            paper_loader.add_value("type", response.meta["type"])
            yield paper_loader.load_item()
