# -*- coding: utf-8 -*-

import scrapy
import re
from scrapy.loader import ItemLoader
from AcadmicGraph.items import PaperItem
from AcadmicGraph.items import CCFIndexItem
from  AcadmicGraph.items import ConferenceItem


class DblpSpider(scrapy.Spider):
    name = "dblp"
    start_urls = ['http://www.ccf.org.cn/xspj/gyml/']

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
            if (re.match('http://dblp.uni-trier.de/db/conf/', href)):
                yield scrapy.Request(href, callback=self.parse_dblp_conf, meta={"part_of": name})
            elif (re.match('http://dblp.uni-trier.de/db/journals/', href)):
                yield scrapy.Request(href, callback=self.parse_dblp_journals, meta={'part_of': name})

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
                yield scrapy.Request(contents, callback=self.parse_dblp_conf_details, meta={'part_of': title})

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
            loader = ItemLoader(item=PaperItem(), response=response)
            loader.add_value("title", title)
            loader.add_value("authors", authors)
            loader.add_value("pagination", pagination)
            loader.add_value("date_published", date_published)
            loader.add_value("header", headers)
            loader.add_value("part_of", response.meta['part_of'])
            loader.add_value("source_href", response.url)
            yield loader.load_item()

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
            loader = ItemLoader(item=PaperItem(), response=response)
            loader.add_value("title", title)
            loader.add_value("authors", authors)
            loader.add_value("pagination", pagination)
            loader.add_value("date_published", date_published)
            loader.add_value("header", headers)
            loader.add_value("part_of", response.meta['part_of'])
            yield loader.load_item()
