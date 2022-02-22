import sys
import logging
import discord
from .bot import run_discord_bot

def setup_logging():
	handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
	handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

	logger = logging.getLogger('discord')
	logger.setLevel(logging.INFO)
	logger.addHandler(handler)
	
	logger = logging.getLogger('bot')
	logger.setLevel(logging.INFO)
	logger.addHandler(handler)

setup_logging()
sys.exit(run_discord_bot())
