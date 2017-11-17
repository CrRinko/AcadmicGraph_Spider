# -*- coding: utf-8 -*-
from scrapy import cmdline

cmdline.execute("scrapy crawl dblp -o ./data/papers.jl".split())
# cmdline.execute("scrapy crawl dblp".split())
