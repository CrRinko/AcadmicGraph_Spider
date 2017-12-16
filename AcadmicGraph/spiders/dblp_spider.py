# -*- coding: utf-8 -*-

import re
from scrapy.loader import ItemLoader
from AcadmicGraph.items import *
from selenium import webdriver
import time
from bs4 import BeautifulSoup

class DblpSpider(scrapy.Spider):
    name = "dblp"

    def __init__(self, urls=None, level='AB', *args, **kwargs):
        super(DblpSpider, self).__init__(*args, **kwargs)
        self.urls = urls
        self.crawl_level = level
        # self.logger=logging.getLogger(self.__class__.__name__)

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
                                         meta={"name": name, "level": level, "genre": response.meta['genre'],
                                               "type": type, "short_name": short_name, "publisher": publisher})
                elif re.match('http://dblp.uni-trier.de/db/journals/', href):
                    yield scrapy.Request(href, callback=self.parse_dblp_journals,
                                         meta={"name": name, "level": level, "genre": response.meta['genre'],
                                               "type": type, "short_name": short_name, "publisher": publisher})

    # 爬取会议目录
    def parse_dblp_conf(self, response):
        confs = response.css(".data")
        for conf in confs:
            sub_title = conf.css(".title::text").extract_first()
            publisher = conf.css("span[itemprop=publisher]::text").extract_first()
            datePublished = conf.css("span[itemprop=datePublished]::text").extract_first()
            isbn = conf.css("span[itemprop=isbn]::text").extract_first()
            authors = conf.xpath("span[@itemprop='author']//*/text()").extract()
            contents = conf.xpath('./a[re:test(text(),"contents")]/@href').extract_first()
            yield ConferenceItem(
                title=response.meta['name'],
                sub_title=sub_title,
                publisher=publisher,
                date_published=datePublished,
                isbn=isbn,
                authors=authors,
                source_href=response.url,
                level=response.meta['level'],
                type=response.meta['type'],
                genre=response.meta['genre'],
                short_name=response.meta['short_name']
            )
            if contents is not None and re.match('http://dblp.uni-trier.de/db/conf/', contents):
                yield scrapy.Request(contents, callback=self.parse_dblp_conf_details,
                                     meta={"part_of": [response.meta['name'], sub_title],
                                           "level": response.meta["level"]})

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
            session = paper.xpath('../../preceding-sibling::header[1]/*/text()').extract_first()
            item = PaperItem(
                title=title,
                authors=authors,
                pagination=pagination,
                date_published=date_published,
                part_of=response.meta['part_of'] + [session],
                source_href=response.url,
                view_href=view_href,
                type="paper",
                level=response.meta['level']
            )
            if view_href is not None:
                yield scrapy.Request(view_href, callback=self.parse_paper_detail_general,
                                     meta={"item": item, "dont_obey_robotstxt": True})
            else:
                yield item

    # 爬取期刊目录
    def parse_dblp_journals(self, response):
        volumes = response.css(".clear-both~ ul a")
        item = JournalItem(
            title=response.meta['name'],
            publisher=response.meta['publisher'],
            level=response.meta['level'],
            genre=response.meta['genre'],
            short_name=response.meta['short_name'],
            source_href=response.url,
            type=response.meta['type']
        )
        yield item
        for volume in volumes:
            link = volume.css('::attr(href)').extract_first()
            if re.match('http://dblp.uni-trier.de/db/journals/', link):
                yield scrapy.Request(link, callback=self.parse_dblp_journals_details,
                                     meta={'part_of': [item['title']], "level": response.meta['level']})

    # 爬取期刊文章列表
    def parse_dblp_journals_details(self, response):
        papers = response.css(".data")
        for paper in papers:
            title = paper.css("span.title::text").extract_first()
            pagination = paper.css("span[itemprop=pagination]::text").extract_first()
            authors = paper.xpath("span[@itemprop='author']//*/text()").extract()
            date_published = paper.xpath("meta[@itemprop='datePublished']/@content").extract_first()
            headers = paper.xpath("../../preceding-sibling::header[1]/*/text()").extract_first()
            view_href = paper.xpath(
                './preceding-sibling::nav[@class="publ"][1]/ul/li[1]/div[@class="head"]/a/@href').extract_first()
            part_of = response.meta['part_of'] + list(map(lambda word: word.strip(), headers.split(',')))
            item = PaperItem(
                title=title,
                authors=authors,
                pagination=pagination,
                date_published=date_published,
                part_of=part_of,
                source_href=response.url,
                view_href=view_href,
                type="paper",
                level=response.meta['level']
            )
            if view_href is not None:
                yield scrapy.Request(view_href, callback=self.parse_paper_detail_general,
                                     meta={"item": item, "dont_obey_robotstxt": True})
            else:
                yield item

    # 爬取文章详情页（）
    def parse_paper_detail_general(self, response):
        item = response.meta['item']
        item['view_href'] = response.url
        if re.search('dl.acm.org', response.url):
            item = self.parse_paper_detail_dl_acm_org(response)
        elif re.search('ieeexplore.ieee.org', response.url):
            item = self.parse_paper_detail_ieeexplore_ieee_org(response)
        elif re.search("link.springer.com", response.url):
            item = self.parse_paper_detail_link_springer_com(response)
        elif re.search('www.sciencedirect.com', response.url):
            item = self.parse_paper_detail_www_sciencedirect_com(response)
        yield item

    def parse_paper_detail_dl_acm_org(self, response):
        item = response.meta['item']
        affiliation = response.css('small::text').extract()
        item['affiliation'] = affiliation
        return item

    def parse_paper_detail_ieeexplore_ieee_org(self, response):
        item = response.meta['item']
        driver = webdriver.PhantomJS()
        driver.get(response.url)
        time.sleep(1)
        driver.find_element_by_link_text("Authors").click()
        time.sleep(1)
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        tags = soup.find_all('div', class_='carousel-item ng-scope')
        affiliation = []
        for tag in tags:
            affiliation.append(tag.find('div', class_='ng-binding').get_text())
        item['affiliation'] = affiliation
        return item

    def parse_paper_detail_link_springer_com(self, response):
        item = response.meta['item']
        affiliations = response.css(".affiliation__item")
        affiliation = []
        for aff in affiliations:
            text = ', '.join(aff.xpath("./*/text()").extract())
            affiliation.append(text)
        item['affiliation'] = affiliation
        return item

    def parse_paper_detail_www_sciencedirect_com(self, response):
        item = response.meta['item']
        affiliation = []
        driver = webdriver.PhantomJS()
        driver.get(response.url)
        driver.find_elements_by_css_selector('.show-details')[0].click()
        for tag in driver.find_elements_by_css_selector('.affiliation dd'):
            affiliation.append(tag.text)
        item['affiliation'] = affiliation
        return item
