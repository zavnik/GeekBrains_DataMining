import requests
from pathlib import Path
import json
import time


class Parse5Ka:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 "
        "(X11; Linux x86_64; rv:85.0) "
        "Gecko/20100101 Firefox/85.0",
    }

    def __init__(self, start_url: str, products_path: Path, category_url: str):
        self.start_url = start_url
        self.products_path = products_path
        self.category_url = category_url

    def _get_response(self, url):
        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            time.sleep(0.5)

    def run(self):
        for product in self._parse(self.start_url):
            product_path = self.products_path.joinpath(f"{product['id']}.json")
            self._save(product, product_path)

    def _parse(self, url):
        while url:
            response = self._get_response(url)
            data = response.json()
            url = data["next"]
            for product in data["results"]:
                yield product

    def get_category_list(self, url):
        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            time.sleep(0.5)

    def category_parser_launcher(self):
        for cat in self.get_category_list(self.category_url):
            cat['products'] = []
            url = f'{self.start_url}?categories={cat["parent_group_code"]}'
            file_path = self.products_path.joinpath(
                f'{cat["parent_group_code"]}.json')
            for prod in self._parse(url):
                cat['products'].append(prod)
            self._save(cat, file_path)

    @staticmethod
    def _save(data: dict, file_path):
        jdata = json.dumps(data, ensure_ascii=False)
        file_path.write_text(jdata, encoding="UTF-8")


def get_dir_path(dirname: str) -> Path:
    dir_path = Path(__file__).parent.joinpath(dirname)
    if not dir_path.exists():
        dir_path.mkdir()
    return dir_path


if __name__ == "__main__":
    url = "https://5ka.ru/api/v2/special_offers/"
    url_get_cat_list = 'https://5ka.ru/api/v2/categories/'
    path_for_cat_list = get_dir_path('categories')
    parser = Parse5Ka(url, path_for_cat_list, url_get_cat_list)
    parser.category_parser_launcher()
