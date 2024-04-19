from robocorp.tasks import task
from botscraper import NewsBot

@task
def run_news_scraper():
    # Create an instance of NewsBot
    bot = NewsBot()
    # Run the scraper
    bot.run()