# -*- coding: utf-8 -*-
from scrapy import cmdline

# cmdline.execute("scrapy crawl dblp -o ./data/papers.jl -L INFO --logfile ./logs/log1".split())
cmdline.execute("scrapy crawl dblp -o ./data/papers.jl -L INFO".split())
# cmdline.execute("scrapy crawl dblp -o ./data/papers.jl -a urls=./start_urls".split())
# cmdline.execute("scrapy crawl dblp".split())
