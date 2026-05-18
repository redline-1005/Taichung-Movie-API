# base_scraper.py
# scrapers/base_scraper.py
import abc
from fake_useragent import UserAgent
import pandas as pd

class BaseMovieScraper(abc.ABC):
    def __init__(self):
        # 實作計畫書提到的假裝瀏覽器功能
        self.ua = UserAgent()
        self.headers = {'User-Agent': self.ua.random}
        self.theater_results = [] # 儲存影廳資訊
        self.showtime_results = [] # 儲存場次資訊

    @abc.abstractmethod
    def fetch_theater_info(self):
        """抓取該體系下所有影廳的資訊"""
        pass

    @abc.abstractmethod
    def fetch_showtimes(self, cinema_id):
        """根據影廳 ID 抓取該影廳的所有場次"""
        pass

    @abc.abstractmethod
    def parse_data(self, raw_content):
        """解析抓取回來的資料"""
        pass