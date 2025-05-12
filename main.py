import datetime
import os
import json
import requests


from const import HEADERS, CHECK_CONNECTION_URL, CARDS_URL, PRICES_URL, WAREHOUSES_URL, FBS_URL, DBS_URL, \
    SELF_PICK_UP_URL, CATEGORIES_URL, COMISSION_URL, CACHE_TIME


def cache(url):
    def decorator(func):
        def wrapper(*args, **kwargs):
            log_filename = f"{url.lstrip('https://').replace('/', '-')}.json"
            log_folder = os.getcwd() + "\\logs"
            log_path = log_folder + "\\" + log_filename
            if (log_filename not in os.listdir(log_folder) or os.path.getmtime(log_path) + CACHE_TIME <
                    datetime.datetime.now().timestamp()):
                res_func = func(*args, **kwargs)
                text = res_func.text
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(text)
                with open(log_path, "r", encoding="utf-8") as f:
                    str_ = f.read()
                    dict_ = json.loads(str_)
                    return dict_
            else:
                with open(log_path, "r", encoding="utf-8") as f:
                    str_ = f.read()
                    dict_ = json.loads(str_)
                    return dict_
        return wrapper
    return decorator


class API_WB:
    def __init__(self):
        if "logs" not in os.listdir():
            os.mkdir(os.getcwd() + "\\logs")

    @cache(CHECK_CONNECTION_URL)
    def check_creds(self):
        return requests.get(url=CHECK_CONNECTION_URL, headers=HEADERS)

    @cache(CARDS_URL)
    def get_prds(self):
        return requests.post(url=CARDS_URL, headers=HEADERS, json={"cursor": {"limit": 1000}})

    def get_prd(self, prd_id: int) -> dict:
        dict_ = {}
        products = self.get_prds().get("cards")
        for el in products:
            if el["nmID"] == int(prd_id):
                if el.get("dimensions").get("isValid"):
                    del el["dimensions"]["isValid"]
                skus = el["sizes"][0]["skus"][0]
                dict_.update({"brand": el["brand"], "title": el["title"], "dimensions": el["dimensions"],
                              "color": el["characteristics"][0]["value"][0]})

            prices = self._get_prices()
            if prices.get("data").get("listGoods"):
                dict_.update({"prices": prices["data"]["listGoods"][0]["sizes"][0]})
                if dict_.get("prices").get("techSizeName"):
                    del dict_["prices"]["techSizeName"]

            warehouses_list = self._get_warehouses()
            warehouses_id_list = [el["id"] for el in warehouses_list]
            for warehouse_id in warehouses_id_list:
                available_stock = self._get_stocks(warehouse_id, skus=None if "skus" not in dir() else skus)
                dict_.update({"amount": available_stock["stocks"][0]["amount"]})

            fbs = self._get_fbs()
            fbs_orders = fbs.get("orders")
            if fbs_orders:
                for order in fbs_orders:
                    if order["nmId"] == prd_id:
                        dict_["prices"].update({"fbs_salePrice": order["salePrice"], "fbs_price": order["price"]})

            dbs = self._get_dbs()
            dbs_orders = dbs.get("orders")
            if dbs_orders:
                for order in dbs_orders:
                    if order["nmId"] == prd_id:
                        dict_["prices"].update({"dbs_salePrice": order["salePrice"], "dbs_price": order["price"]})

            self_pick_up = self._get_self_pick_up()
            self_pick_up_orders = self_pick_up.get("orders")
            if self_pick_up_orders:
                for order in self_pick_up_orders:
                    if order["nmId"] == prd_id:
                        dict_["prices"].update({"self_pick_up_salePrice": order["salePrice"],
                                                "self_pick_up_price": order["price"]})

            return dict_

    def set_prd(self, prd_id: int, vendor_code: str, attr_name: str, new_value: str) -> dict:
        url = "https://content-api-sandbox.wildberries.ru/content/v2/cards/update"
        r = requests.post(url=url, headers=HEADERS, json={"nmID": prd_id, "vendorCode": vendor_code,
                                                          attr_name: new_value})
        return r.json()

    @cache(CATEGORIES_URL)
    def get_categories(self):
        return requests.get(url=CATEGORIES_URL, headers=HEADERS)

    def get_orders(self) -> dict:  # Нужно использовать продовый токен (не из тестового контура)
        fbs_orders = self._get_fbs()
        dbs_orders = self._get_dbs()
        self_pick_up_orders = self._get_self_pick_up()

        return {"fbs_orders": fbs_orders, "dbs_orders": dbs_orders, "self_pick_up_orders": self_pick_up_orders}

    @cache(COMISSION_URL)
    def get_comission(self):  # Нужно использовать продовый токен (не из тестового контура)
        return requests.get(url=COMISSION_URL, headers=HEADERS)

    @cache(PRICES_URL)
    def _get_prices(self):
        return requests.get(url=PRICES_URL, headers=HEADERS, params={"limit": 1000})

    def _get_stocks(self, warehouse_id: str, skus: str):
        url = f"https://marketplace-api.wildberries.ru/api/v3/stocks/{warehouse_id}"
        r = requests.post(url=url, headers=HEADERS, json=skus)
        json = r.json()
        return json

    @cache(WAREHOUSES_URL)
    def _get_warehouses(self):
        return requests.get(url=WAREHOUSES_URL, headers=HEADERS)

    @cache(FBS_URL)
    def _get_fbs(self):
        return requests.get(url=FBS_URL, headers=HEADERS)

    @cache(DBS_URL)
    def _get_dbs(self):
        return requests.get(url=DBS_URL, headers=HEADERS)

    @cache(SELF_PICK_UP_URL)
    def _get_self_pick_up(self):
        return requests.get(url=SELF_PICK_UP_URL, headers=HEADERS)


if __name__ == "__main__":
    wb = API_WB()
    print(wb.check_creds())
    print(wb.get_prds())
    print(wb.get_prd(12345678))
    print(wb.set_prd(12345678, "qwerty", "length", "100"))
    print(wb.get_categories())
    print(wb.get_orders())
    print(wb.get_comission())
