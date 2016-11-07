import unittest

from bs4 import BeautifulSoup

from app.start import create_app


class TestAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

        with open('./tests/resources/styleguide.html', 'r', encoding='UTF-8') as file:
            cls.style_guide_html = file.read()

    def test_style_guide(self):
        flask_app = create_app(port=8080, environment="empty", working_dir="./", greedy_mode=True)
        flask_app.config.update(
            DEBUG=True,
            SECRET_KEY='secret_key')
        app = flask_app.test_client()

        response = app.get("/internal/style")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.style_guide_html.replace(' ', ''), response.data.decode().replace(' ', ''))

        soup = BeautifulSoup(response.data.decode(), 'html.parser')
        wells = soup.find_all("div", {"class": "well"})
        self.assertEqual(11, len(wells))
