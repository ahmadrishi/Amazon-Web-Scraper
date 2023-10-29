import json
import scrapy
from urllib.parse import urljoin
import re

class CrawlingAmazon(scrapy.Spider):
    name = "amazon"
    allowed_domains = ["amazon.com"]
    
    def get_product(self, response):
        url = response.url
        image_data = json.loads(re.findall(r"colorImages':.*'initial':\s*(\[.+?\])},\n", response.text)[0])
        variant_data = re.findall(r'dimensionValuesDisplayData"\s*:\s* ({.+?}),\n', response.text)
        feature_bullets = [bullet.strip() for bullet in response.css("#feature-bullets li ::text").getall()]
        price = response.css('.a-price span[aria-hidden="true"] ::text').get("")
        if not price:
            price = response.css('.a-price .a-offscreen ::text').get("")
        yield {
            "url": url,
            "name": response.css("#productTitle::text").get("").strip(),
            "price": price,
            "stars": response.css("i[data-hook=average-star-rating] ::text").get("").strip(),
            "rating_count": response.css("div[data-hook=total-review-count] ::text").get("").strip(),
            "feature_bullets": feature_bullets,
            "images": image_data,
            "variant_data": variant_data,
        }


    def extract_products(self, response):
        page = response.meta['page']
        keyword = response.meta['keyword']

        products = response.css("div.s-result-item[data-component-type=s-search-result]")
        for product in products:
            relative_url = product.css("h2>a::attr(href)").get()
            product_url = urljoin('https://www.amazon.com/', relative_url).split("?")[0]
            yield scrapy.Request(url=product_url, callback=self.get_product, meta={'keyword':keyword, 'page':page})

        if page == 1:
            pages = response.xpath('//a[has-class("s-pagination-item")][not(has-class("s-pagination-separator"))]/text()').getall()
                
            for i in pages:
                url = f'https://www.amazon.com/s?k={keyword}&page={i}'
                yield scrapy.Request(url=url, callback=self.extract_products, meta={'keyword': keyword, 'page': i})

    def start_requests(self):
        keywords=['ipad']
        for keyword in keywords:
            url = f'https://www.amazon.com/s?k={keyword}&page=1'
            yield scrapy.Request(url=url, callback=self.extract_products, meta={'keyword': keyword, 'page': 1})
        
    