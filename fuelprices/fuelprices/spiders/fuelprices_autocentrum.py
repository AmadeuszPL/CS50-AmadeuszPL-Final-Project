import scrapy


class FuelpricesAutocentrumSpider(scrapy.Spider):
    name = 'fuelprices_autocentrum'
    allowed_domains = ['https://www.autocentrum.pl/paliwa/ceny-paliw/']
    start_urls = ['https://www.autocentrum.pl/paliwa/ceny-paliw/']

    def parse(self, response):
        print("procesing:"+response.url)
        #Extract data using css selectors
        fuel_header = response.css('.fuel-header::text').extract()
        #prices = response.css('.price::text').extract()
        #prices = response.xpath("normalize-space(//div[@class='price']/text())").extract()
        prices = response.xpath(".//div[@class='price']").xpath("normalize-space()").getall()

        #response.xpath('//a[@class="hotel_name_link url"]').xpath('normalize-space(@href)').getall()

        #response.xpath('normalize-space(//td[@class="price"]//p)').get()

        #Extract data using xpath
        #orders=response.xpath("//em[@title='Total Orders']/text()").extract()
        #company_name=response.xpath("//a[@class='store $p4pLog']/text()").extract()

        row_data=zip(fuel_header,prices)

        #Making extracted data row wise
        for item in row_data:
            #create a dictionary to store the scraped info
            scraped_info = {
                #key:value
                #'page':response.url,
                'fuel_header' : item[0], #item[0] means product in the list and so on, index tells what value to assign
                'price' : item[1],
            }

            #yield or give the scraped info to scrapy
            yield scraped_info
