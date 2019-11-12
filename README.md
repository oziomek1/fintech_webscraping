## Smartkarma scrapers

[Google slides](https://docs.google.com/presentation/d/1qDctQJKeNblTY-VLhLrOSro3o8CPq8iXkTqUX5kMW6w/edit#slide=id.g6fc5646b42_0_41)

There are two version of Smartkarma scrapers available:

* #### script

This is a simple script, consisting of python selenium framework functions. This script suppose to be simple to understand and run without in depth analysis of code.

To run - go to `script` directory and execute:

`python selenium_scraper_simple.py`

The script should start scraping the Smartkarma website and printing the current operations to the console.

* #### extended
Extended version of scraper organises code in classes. This suppose to be easier to work for advanced users. Code is designed to help develop scraper and adding new features in the future.

To run - go to `extended` directory and execute:

`python selenium_scraper.py`

### Both scrapers shares very similar list options:

Default options:

```python
options = ['--headless']
```
Scrapes the website in headless mode, without opening the chrome browser itself.
If the user removes this option: `options = []` then the browser runs automatically and the process of iterating through website is visible.

```python
settings = {
	'primary_timeout': 5,
	'secondary_timeout': 2,
	'scroll_iterations': 2,
}
```
Description:
- `'primary_timeout': 5` - sets the default timeout for finding elements on whole website to 5 seconds
- `'secondary_timeout': 2` - sets the default timeout for finding elements on part of a website to 2 seconds. Scrapers are designed to first get "areas", for example the author area at Smartkarma website and then scraping the values from them. Limitting the ```secondary_timeout``` makes the scraper works faster
- `'scroll_iterations': 2` - set the default number of "scrolls down" over the website. This behaviour emulates single scrolling down the page in every iteration.

```python
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
```
Smartkarma provides sectors for insights. However sectors are hardly accessible by scraping. As a result, simpler and faster approach is to provide links postfixes to search for insights for each category.
The scrapers iterates through every single sector and looks for insights to scrapes. In output file, the data is assigned to sectors.


### Scrapers output

Currently both scrapers saves output with data of scraped insights to local json file, named `output.json`. The structure of a single file entry is presented below

```python
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
```
Structure elements description:
- url - link of scraped insight
- sector_name - sector of insight
- author - author of insight
- author_role - role of author
- entity - entity of insight
- vertical - vertical of insight
- title - title of insight
- views - number of views of insight
- date - creation date of insight
- text - text inside the insight
