import requests
import bs4
from urllib.parse import urljoin
import pymongo
import datetime as dt


class Date_Helper:
    @staticmethod
    def get_month_by_name(month_name:str):
        month_description = {
            'января': 1,
            'февраля': 2,
            'марта': 3,
            'мая': 4,
            'апреля': 5,
            'июня': 6,
            'июля': 7,
            'августа': 8,
            'сентября': 9,
            'октября': 10,
            'ноября': 11,
            'декабря': 12
        }
        return month_description.get(month_name)

    @staticmethod
    def fromto_format_to_date(from_to_string:str) -> list:
        dates_part = (from_to_string.split('\n'))
        result = []
        try:
            # TODO обрабоотать дату формата "только 13 марта"
            from_day = int(dates_part[1].split(' ')[1])
            from_month = Date_Helper.get_month_by_name(dates_part[1].split(' ')[2])
            from_year = dt.datetime.now().year

            to_day = int(dates_part[2].split(' ')[1])
            to_month = Date_Helper.get_month_by_name(dates_part[2].split(' ')[2])
            to_year = dt.datetime.now().year if to_month >= from_month else dt.datetime.now().year + 1
            result = [dt.datetime(from_year, from_month, from_day),
                dt.datetime(to_year, to_month, to_day)]
        except:
            print('ошибка обработки нетипичной даты')
            result = [None, None]
            pass

        return result


class MagnitParse:
    def __init__(self, start_url, db_client):
        self.start_url = start_url
        self.db = db_client["geek_brains_data_mining"]

    def _template(self):
        return {
            'url': lambda a: urljoin(self.start_url, a.attrs.get('href')),
            'promo_name': lambda a: a.find('div', attrs={'class': 'card-sale__headers'}).text,
            'title': lambda a: a.find('div', attrs={'class': 'card-sale__title'}).text,

            # TODO Обработка цены типа "выгодно"
            'new_price': lambda a: float((a.find('div', attrs={'class': 'label__price'})).find('span', attrs={'class': 'label__price-integer'}).text +
                                         '.' +
                                         (a.find('div', attrs={'class': 'label__price'})).find('span', attrs={'class': 'label__price-decimal'}).text),

            'old_price': lambda a: float((a.find('div', attrs={'class': 'label__price_old'})).find('span', attrs={
                'class': 'label__price-integer'}).text +
                                         '.' +
                                         (a.find('div', attrs={'class': 'label__price_old'})).find('span', attrs={
                                             'class': 'label__price-decimal'}).text),
            'image_url': lambda a: urljoin(self.start_url, a.find('img').attrs.get('data-src')),
            'date_from': lambda a: Date_Helper.fromto_format_to_date(a.find("div", attrs={"class": "card-sale__date"}).text)[0],
            'date_to': lambda a: Date_Helper.fromto_format_to_date(a.find("div", attrs={"class": "card-sale__date"}).text)[1],

        }

    def _get_response(self, url):
        response = requests.get(url)
        return response

    def _get_soup(self, url):
        response = self._get_response(url)
        soup = bs4.BeautifulSoup(response.text, "lxml")
        return soup

    def run(self):
        soup = self._get_soup(self.start_url)
        catalog = soup.find('div', attrs={'class': 'сatalogue__main'})
        for product_a in catalog.find_all('a', recursive=False):
            product_data = self._parse(product_a)
            self.save(product_data)

    def _parse(self, product_a: bs4.Tag) -> dict:
        product_data = {}
        for key, funk in self._template().items():
            try:
                product_data[key] = funk(product_a)
            except AttributeError:
                pass

        return product_data


    def save(self, data:dict):
        collection = self.db['magnit_2021-03-10']
        collection.insert_one(data)

if __name__ == '__main__':
    url = 'https://magnit.ru/promo/'
    db_client = pymongo.MongoClient('mongodb://localhost:27017')
    parser = MagnitParse(url, db_client)
    parser.run()

