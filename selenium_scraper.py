from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json
import time
from collections import namedtuple, defaultdict


class PageData(namedtuple(
	'PageData',
	[
		'url',
		'sector_name',
		'author',
		'author_role',
		'entity',
		'vertical',
		'title',
		'views',
		'date',
		'text',
	]
)):
    def to_dict(self):
        return self._asdict()

    @classmethod
    def from_dict(cls, dictionary):
        return cls(**dictionary)


class DriverWrapper:
	def __init__(self, options=None, starting_link='https://www.smartkarma.com/insights'):
		self.options_list = options
		self.options = webdriver.ChromeOptions()
		self._driver = None
		self._starting_link = starting_link

	def _apply_options(self):
		"""Apply web browser options before creation"""
		for option in self.options_list:
			self.options.add_argument(option)

	def create_driver(self):
		"""Create browser driver"""
		self._apply_options()
		self._driver = webdriver.Chrome(chrome_options=self.options)
		self.get_driver_link(self._starting_link)

	def get_current_window(self):
		return self._driver.current_window_handle

	def get_driver_link(self, link):
		"""Pass link to browser driver"""
		self._driver.get(link)

	def quit(self):
		"""Close web browser after scraping is finished"""
		if self._driver is not None:
			self._driver.quit()


class Scraper:
	def __init__(self, options=[], starting_link='https://www.smartkarma.com/insights', **settings):
		self.driver_wrapper = DriverWrapper(options, starting_link)
		self.driver_wrapper.create_driver()
		self._executor = Executor(self.driver_wrapper, self.return_driver_instance())
		self._data_processor = DataProcessor()
		self.settings = settings
		self.main_window = None
		self.scraped_websites = None
		self.stored_multiple_elements = defaultdict(list)
		self.stored_single_elements = defaultdict(list)
		self.timeouted_links = []

	def close_new_tab(self):
		self._executor.close_and_return_main_window(main_window=self.main_window)

	def get_current_driver_window(self):
		"""Assign current driver window to main window"""
		self.main_window = self.driver_wrapper.get_current_window()

	def get_multiple_elements(self, timeout, xpath, key=None, base_element=None, store_text=False):
		"""
		Get multiple elements by xpath and store to dictionary

		Arguments:
		timeout -- timeout for all elements presence
		xpath -- path of website elements
		key -- key to store elements in dictionary
		base_element -- parent element in html hierarchy
		"""
		multiple_elements = self._executor.wait_for_all_elements_presence_and_get(
			timeout=timeout, 
			xpath=xpath,
			base_element=base_element,
		)
		self.stored_multiple_elements[key] = [
			element.get_attribute('href') if store_text else element
			for element in multiple_elements
		]

	def get_single_element(self, timeout, xpath, key=None, base_element=None, store_text=False):
		"""
		Get single element by xpath and store to dictionary

		Arguments:
		timeout -- timeout element presence
		xpath -- path of website element
		key -- key to store element in dictionary
		base_element -- parent element in html hierarchy
		store_text -- define if storing text or element
		"""
		single_element = self._executor.wait_for_element_presence_and_get(
			timeout=timeout, 
			xpath=xpath, 
			base_element=base_element,
		)
		value_to_be_stored = single_element.text if store_text else single_element
		self.stored_single_elements[key].append(value_to_be_stored)
		return value_to_be_stored

	def get_single_element_to_resolve(self, timeout, xpath, key=None, base_element=None):
		"""
		Get single element by xpath and convert to views and date values

		Arguments:
		timeout -- timeout for all elements presence
		xpath -- path of website element
		key -- key to store element in dictionary
		base_element -- parent element in html hierarchy
		"""
		element_to_resolve = self._executor.wait_for_element_presence_and_get(
			timeout=timeout, 
			xpath=xpath, 
			base_element=base_element,
		)
		resolved_elements = self._data_processor.convert_views_and_date(element_to_resolve=element_to_resolve.text)
		for name, element in resolved_elements.items():
			self.stored_single_elements[name].append(element)
		return resolved_elements.values()

	def open_new_link(self, link):
		self.driver_wrapper.get_driver_link(link=link)

	def open_new_tab(self, link):
		self._executor.open_and_switch_window(link=link)

	def return_driver_instance(self):
		"""Return instance of current browser driver"""
		return self.driver_wrapper._driver

	def scroll_down(self, tag='body'):
		self._executor.scroll_down_page(self.settings['scroll_iterations'], tag=tag)


class Executor:
	def __init__(self, driver_wrapper, chrome_driver):
		self.driver_wrapper = driver_wrapper
		self.chrome_driver = chrome_driver

	def close_and_return_main_window(self, main_window):
		"""Close tab and return to main window"""
		self.chrome_driver.switch_to.window(main_window)

	def open_and_switch_window(self, link):
		"""Open new tab and switch to it from main window"""
		self.chrome_driver.execute_script("window.open('" + link + "', 'new_window')")
		self.chrome_driver.switch_to_window(self.chrome_driver.window_handles[-1])

	def scroll_down_page(self, scroll_iterations, tag='body'):
		"""
		Scroll page to gather more links

		Arguments:
		scroll_iterations -- Key-down press action counter
		tag -- page tag, default='body'
		"""
		for scroll_iteration in range(scroll_iterations):
			self.chrome_driver.find_element_by_tag_name(tag).send_keys(Keys.END)
			time.sleep(1)

	def wait_for_all_elements_presence_and_get(self, timeout=5, xpath='//div', base_element=None):
		"""
		Wait for multiple web elements to present
		
		Arguments:
		timeout -- timeout for all elements presence
		xpath -- path of website element
		
		Returns list of elements
		"""
		return WebDriverWait(base_element, timeout).until(
			EC.presence_of_all_elements_located((By.XPATH, xpath))
		)

	def wait_for_element_presence_and_get(self, timeout=5, xpath='//div', base_element=None):
		"""
		Wait for single web element to present

		Arguments:
		timeout -- maximum timeout for element presence
		xpath -- path of website element

		Returns single element
		"""
		return WebDriverWait(base_element, timeout).until(
			EC.presence_of_element_located((By.XPATH, xpath))
		)


class DataProcessor:
	def convert_views_and_date(self, element_to_resolve):
		"""Resolve views number and date from single string"""
		views_and_date_separated = element_to_resolve.split(',')
		views = self.safe_casting(views_and_date_separated[0].split()[0], int, 0)
		date = views_and_date_separated[1]
		return {'views': views, 'date': date}

	def safe_casting(self, value, to_type, default=None):
		"""Cast string to desired type""" 
		try:
			return to_type(value)
		except (ValueError, TypeError):
			return default

	def safe_json(self, value, output_name='output.json'):
		"""Save data to json""" 
		with open(output_name, 'w') as outfile:
			json.dump(value, outfile)

base_link = 'https://www.smartkarma.com/insights'
options = []#['--headless']
settings = {
	'primary_timeout': 5,
	'secondary_timeout': 2,
	'scroll_iterations': 2,
}
sectors = {
	'consumer_discretionary': 'Consumer%20Discretionary',
	'consumer_staples': 'Consumer%20Staples',
	'energy': 'Energy',
	'financials': 'Financials',
	'health_care': 'Health%20Care',
	'industrials': 'Industrials',
	'information_technology': 'Information%20Technology',
	'materials': 'Materials',
	'real_estate': 'Real%20Estate',
	'telecommunication_services': 'Telecommunication%20Services',
	'utilities': 'Utilities'
}
sector_prefix = '?filters=sectors%3A'

scraped_insights = []

scraper = Scraper(options=options, **settings)
scraper.get_current_driver_window()

for sector_name, sector_postfix in sectors.items():
	scraper.open_new_link(base_link + sector_prefix + sector_postfix)
	scraper.get_multiple_elements(
		timeout=settings['primary_timeout'],
		xpath='//a[contains(@class, "sk-insight-snippet__headline")]',
		key=sector_name,
		base_element=scraper.return_driver_instance(),
		store_text=True,
	)

for sector_name in sectors.keys():
	print('Links in sector: ', sector_name, ':', len(scraper.stored_multiple_elements[sector_name]))

	for index, link in enumerate(scraper.stored_multiple_elements[sector_name]):
		print(index, link)
		try: 
			scraper.open_new_tab(link)

			"""AUTHOR"""
			author_section = scraper.get_single_element(
				timeout=settings['primary_timeout'],
				xpath='//div[contains(@class, "sk-insight-longform__compact-header__author")]',
				key='author_section',
				base_element=scraper.return_driver_instance(),
			)
			author = scraper.get_single_element(
				timeout=settings['secondary_timeout'],
				xpath='.//a[contains(@class, "item-snippet__text")]',
				key='author',
				base_element=author_section,
				store_text=True,
			)
			author_role = scraper.get_single_element(
				timeout=settings['secondary_timeout'],
				xpath='.//div[contains(@class, "item-snippet__text")]',
				key='author_role',
				base_element=author_section,
				store_text=True,
			)

			"""ENTITY"""
			entity_section = scraper.get_single_element(
				timeout=settings['primary_timeout'],
				xpath='//div[contains(@class, "sk-insight-longform__compact-header__entity")]',
				key='entity_section',
				base_element=scraper.return_driver_instance(),
			)
			entity = scraper.get_single_element(
				timeout=settings['secondary_timeout'],
				xpath='.//a[starts-with(@href, "/entities")]',
				key='entity',
				base_element=entity_section,
				store_text=True,
			)
			vertical = scraper.get_single_element(
				timeout=settings['secondary_timeout'],
				xpath='.//a[starts-with(@href, "/verticals")]',
				key='vertical',
				base_element=entity_section,
				store_text=True,
			)

			"""HEADLINE""" 
			headline_section = scraper.get_single_element(
				timeout=settings['primary_timeout'],
				xpath='//div[contains(@class, "sk-insight-longform__title-container")]',
				key='headline_section',
				base_element=scraper.return_driver_instance(),
			)
			title = scraper.get_single_element(
				timeout=settings['secondary_timeout'],
				xpath='.//h1[contains(@class, "insight-content__headline")]',
				key='title',
				base_element=headline_section,
				store_text=True,
			)
			views, date = scraper.get_single_element_to_resolve(
				timeout=settings['secondary_timeout'],
				xpath='.//div[contains(@class, "insight-content__meta +print-hidden")]',
				key='views_and_date',
				base_element=headline_section,
			)

			"""CONTENT"""
			content = scraper.get_single_element(
				timeout=settings['secondary_timeout'],
				xpath='//div[contains(@class, "insight-content__content")]',
				key='content',
				base_element=scraper.return_driver_instance(),
				store_text=True,
			) 
			scraper.close_new_tab()

			data = PageData(
				url=link,
				sector_name=sector_name,
				author=author,
				author_role=author_role,
				entity=entity,
				vertical=vertical,
				title=title,
				views=views,
				date=date,
				text=content,
			)
			scraped_insights.append(data._asdict())

			print('[SAVED] Insight with number #' + str(index) + ' in sector ' + sector_name + ' scraped')

		except TimeoutException as ex:
			scraper.timeouted_links.append(index)
			print('[TIMEOUT]' + str(ex), 'cannot store #' + str(index) + 'insight in sector ' + sector_name + '. Continue iterating...')
			scraper.close_new_tab()
			continue

scraper.driver_wrapper.quit()

scraper._data_processor.safe_json(scraped_insights)

