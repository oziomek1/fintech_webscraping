from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json
import time

from collections import namedtuple


options_list = ['--headless']
settings = {
	'primary_timeout': 5,
	'secondary_timeout': 2,
	'scroll_iterations': 2,
}
chrome_options = webdriver.ChromeOptions()
scraped_insights = []

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
links_elements_for_sectors = {}

page_data = namedtuple(
	'page_data',
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
)


for option in options_list:
	chrome_options.add_argument(option)
base_link = 'https://www.smartkarma.com/insights'
driver = webdriver.Chrome(chrome_options=chrome_options)
driver.get(base_link)
main_window = driver.current_window_handle


def safe_casting(val, to_type, default=None):
	"""Cast string to desired type"""
	try:
		return to_type(val)
	except (ValueError, TypeError):
		return default


def safe_json(value):
	"""Save data to json"""
	with open('output.json', 'w') as outfile:
		json.dump(value, outfile)
	print('[INSIGHTS SAVED]')


def scroll_page(scroll_iterations=settings['scroll_iterations']):
	"""
	Scroll page to gather more links

	Arguments:
	scroll_iterations -- Key-down press action counter
	"""
	for scroll_iteration in range(scroll_iterations):
		driver.find_element_by_tag_name('body').send_keys(Keys.END)
		time.sleep(1)


def wait_for_element_presence_and_get(driver=driver, timeout=settings['secondary_timeout'], xpath='//div'):
	"""
	Wait for single web element to present

	Arguments:
	timeout -- maximum timeout for element presence
	xpath -- path of website element

	Returns single element
	"""
	return WebDriverWait(driver, timeout).until(
		EC.presence_of_element_located((By.XPATH, xpath))
	)


def wait_for_elements_presence_and_get(driver=driver, timeout=settings['secondary_timeout'], xpath='//div'):
	"""
	Wait for multiple web elements to present

	Arguments:
	timeout -- timeout for all elements presence
	xpath -- path of website element

	Returns list of elements
	"""
	return WebDriverWait(driver, timeout).until(
		EC.presence_of_all_elements_located((By.XPATH, xpath))
	)


def convert_views_and_date(views_and_date):
	"""Resolve views number and date from single string"""
	views_and_date_separated = views_and_date.text.split(',')
	views = safe_casting(views_and_date_separated[0].split()[0], int, 0)
	date = views_and_date_separated[1]
	return views, date

print('initialization...')
for sector_name, sector_postfix in sectors.items():
	"""ITERATE THROUGH SECTORS"""
	driver.get(base_link + sector_prefix + sector_postfix)

	"""IMMITATE SCROLLING DOWN TO RELOAD INSIGHTS LIST"""
	scroll_page(scroll_iterations=settings['scroll_iterations'])

	"""FIND INSIGHTS LINKS ON MAIN PAGE"""
	list_of_elements = wait_for_elements_presence_and_get(
		driver=driver,
		timeout=settings['primary_timeout'],
		xpath='//a[contains(@class, "sk-insight-snippet__headline")]',
	)
	links_elements_for_sectors[sector_name] = [element.get_attribute('href') for element in list_of_elements]
	print(sector_name, '# of links to scrape:', len(links_elements_for_sectors[sector_name]))


for sector_name in sectors.keys():
	print('Links in sector:', sector_name, len(links_elements_for_sectors[sector_name]))

	"""ITERATE OVER FOUND LINKS"""
	for index, link in enumerate(links_elements_for_sectors[sector_name]):
		print(index, link)
		try:
			print('\n', index)
			driver.execute_script("window.open('" + link + "', 'new_window')")

			driver.switch_to_window(driver.window_handles[-1])
			"""SCRAPE THE INSIGHT PAGE"""

			"""AUTHOR"""
			author_section = wait_for_element_presence_and_get(
				driver=driver,
				timeout=settings['primary_timeout'],
				xpath='//div[contains(@class, "sk-insight-longform__compact-header__author")]',
			)
			author = wait_for_element_presence_and_get(
				driver=author_section,
				timeout=settings['secondary_timeout'],
				xpath='.//a[contains(@class, "item-snippet__text")]',
			)
			author_role = wait_for_element_presence_and_get(
				driver=author_section,
				timeout=settings['secondary_timeout'],
				xpath='.//div[contains(@class, "item-snippet__text")]',
			)
			print('saved author', end='')

			"""ENTITY"""
			entity_section = wait_for_element_presence_and_get(
				driver=driver,
				timeout=settings['primary_timeout'],
				xpath='//div[contains(@class, "sk-insight-longform__compact-header__entity")]',
			)
			entity = wait_for_element_presence_and_get(
				driver=entity_section,
				timeout=settings['secondary_timeout'],
				xpath='.//a[starts-with(@href, "/entities")]',
			)
			vertical = wait_for_element_presence_and_get(
				driver=entity_section,
				timeout=settings['secondary_timeout'],
				xpath='.//a[starts-with(@href, "/verticals")]',
			)
			print(';\tsaved entity', end='')

			"""HEADLINE"""
			headline_section = wait_for_element_presence_and_get(
				driver=driver,
				timeout=settings['primary_timeout'],
				xpath='//div[contains(@class, "sk-insight-longform__title-container")]',
			)
			title = wait_for_element_presence_and_get(
				driver=headline_section,
				timeout=settings['secondary_timeout'],
				xpath='.//h1[contains(@class, "insight-content__headline")]',
			)
			views_and_date = wait_for_element_presence_and_get(
				driver=headline_section,
				timeout=settings['secondary_timeout'],
				xpath='.//div[contains(@class, "insight-content__meta +print-hidden")]',
			)
			views, date = convert_views_and_date(views_and_date)
			print(';\tsaved date', end='')

			"""CONTENT"""
			content = WebDriverWait(driver, settings['primary_timeout']).until(
				EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "insight-content__content")]')))
			print(';\tsaved content', end='')


			"""STORE NAMEDTUPLE"""
			insight_data = page_data(
				url=link,
				sector_name=sector_name,
				author=author.text,
				author_role=author_role.text,
				entity=entity.text,
				vertical=vertical.text,
				title=title.text,
				views=views,
				date=date,
				text=content.text,
			)
			scraped_insights.append(insight_data._asdict())
			print(';\t[INSIGHT SCRAPED AND STORED]')

			driver.switch_to.window(main_window)
		except TimeoutException as ex:
			print("\n[TIMEOUT]" + str(ex) + ': withdrawing current #' + str(index) + ' insight\tcontinue with next insight...')
			driver.switch_to.window(main_window)
			continue

driver.quit()

safe_json(scraped_insights)
