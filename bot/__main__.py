import sys
import logging
from .bot import run_discord_bot
import os


def setup_logging():
	cwd = os.getcwd()
	handler = logging.FileHandler(filename='{}/discord.log'.format(cwd), encoding='utf-8', mode='w')
	handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

	logger = logging.getLogger('discord')
	logger.setLevel(logging.INFO)
	logger.addHandler(handler)
	
	logger = logging.getLogger('bot')
	logger.setLevel(logging.INFO)
	logger.addHandler(handler)

setup_logging()
sys.exit(run_discord_bot())
