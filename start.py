# -*- coding: utf-8 -*-
from scrapy import cmdline

cmdline.execute("scrapy crawl dblp -o ./data/papers.jl -L WARNING".split())
# cmdline.execute("scrapy crawl dblp".split())
