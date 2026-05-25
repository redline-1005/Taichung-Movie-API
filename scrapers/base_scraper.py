# scrapers/base_scraper.py
import abc

class BaseMovieScraper(abc.ABC):
    def __init__(self):
        self.theater_results = []
        self.showtime_results = []

    @abc.abstractmethod
    def fetch_theater_info(self):
        pass

    @abc.abstractmethod
    def fetch_showtimes(self, cinema_id):
        pass

    @abc.abstractmethod
    def parse_data(self, raw_content):
        pass