import logging
import os
import random

import discord

logger = logging.getLogger('bot')
bot_invite_url = "https://discord.com/api/oauth2/authorize?client_id=944989207665967124&permissions=309237738560&scope=bot"
bot_repo_url = "https://github.com/shadytradesman/contract-bot"
DEFAULT_TOKENS = {
		"prefix": "!!",
		"roll_seperator": "@",
		"exertion": "ex",
		"help": "help",
		"flip_high": "h",
		"flip_low": "l",
}


class ContractClient(discord.Client):

	def __init__(self, tokens=DEFAULT_TOKENS):
		self.tokens = tokens
		super().__init__()

	async def on_ready(self):
		logger.info('Logged on as {0}!'.format(self.user))

	async def on_message(self, message):
		if message.content.startswith(self.tokens["prefix"]):
			response = self.get_response_for_message(message)
			logger.debug('Responding to message {} with {}'.format(message.content, response))
			await self.respond_to_message(message, response)
	
	def get_response_for_message(self, message):
		content = message.content[len(self.tokens["prefix"]):]
		words = content.split(" ")
		if len(words) == 0:
			return self.error_usage_message()
		first_word_parts = words[0].split(self.tokens["roll_seperator"])
		if len(first_word_parts) > 2: 
			return self.error_usage_message("only use one {} when rolling.".format(self.tokens["roll_seperator"]))
		if first_word_parts[0] == self.tokens["help"]
			return self.help_message()
		if first_word_parts[0] in (self.tokens["flip_high"], self.tokens["flip_low"]):
			return self.flip(is_high=first_word_parts[0] == self.tokens["flip_high"])
		if first_word_parts[0].isdigit():
			return self.roll_dice_response(message, parsed_message=[first_word_parts, *words[1:]])
		return self.error_usage_message("did not recognize message format.")

	def flip(self, is_high=True):
		result = random.randint(1, 10)
		success = (is_high && result >= 6) || ((not is_high) && result <= 5)
		return "rolled high/low calling **{}**\n{}`{}`\n{}Outcome: **{}**".format("high" if is_high else "low", result, "SUCCESS" if success else "FAILURE")

	def help_message(self):
		help_lines = []
		help_lines.append("**Welcome to The Contract's Dice Rolling Bot!**")
		help_lines.append("This bot can help you roll dice for the game The Contract https://www.TheContractRPG.com/ ")
		help_lines.append("Contribute to my source code: {}".format(bot_repo_url))
		help_lines.append("Add this bot to your server: {}".format(bot_invite_url))
		help_lines.append(self.usage_message())
		return "\n".join(help_lines)

	def error_usage_message(self, error=None):
		if error:
			return "Error - {}\n{}".format(error, self.usage_message())
		return self.usage_message()

	def usage_message(self):
		usage_lines = []
		usage_lines.append("**Usage:**")
		usage_lines.append("`{}{}` Display help".format(self.tokens["prefix"], self.tokens["help"]))
		usage_lines.append("`{}3` Roll 3 dice difficulty 6".format(self.tokens["prefix"]))
		usage_lines.append("`{}4{}8` Roll 4 dice difficulty 8".format(self.tokens["prefix"], self.tokens["roll_seperator"]))
		usage_lines.append("`{}5 {}` Roll 5 dice difficulty 6 and exert".format(self.tokens["prefix"], self.tokens["exertion"]))
		usage_lines.append("`{}3 init` Roll 3 dice difficulty 6 and label 'init'".format(self.tokens["prefix"]))
		usage_lines.append("`{}4{}7 {} blue` Roll 4 dice difficulty 7, exert, and label 'blue'".format(self.tokens["prefix"], self.tokens["roll_seperator"], self.tokens["exertion"]))
		usage_lines.append("`{}{}` Flip a coin calling 'high'".format(self.tokens["prefix"], self.tokens["flip_high"]))
		usage_lines.append("`{}{}` Flip a coin calling 'low'".format(self.tokens["prefix"], self.tokens["flip_low"]))
		return "\n".join(usage_lines)

	def roll_dice_response(self, message, parsed_message):
		first_word_tokens = parsed_message[0]
		for token in first_word_tokens:
			if not token.isdigit():
				return self.error_usage_message("{} is not a number".format(token))
		num_dice = int(first_word_tokens[0])
		if num_dice >= 50:
			return "Error - please roll fewer than 50 dice"
		difficulty = int(first_word_tokens[1]) if len(first_word_tokens) > 1 else 6
		exert = False
		label = None
		if len(parsed_message) > 1:
			for token in parsed_message[1:]:
				if token == self.tokens["exertion"]:
					exert = True
				else:
					label = token
		
		
		return self.contract_roll(num_dice=num_dice, difficulty=difficulty, exert=exert, label=label)

	def contract_roll(self, num_dice, difficulty=6, exert=False, label=None):
		gt_9_diff_text = ""
		if difficulty > 9:
			difference = difficulty - 9
			num_dice -= max(difference, 0)
			difficulty = 9
			gt_9_diff_text = "(Difficulty > 9 decreases dice)"
		results = [random.randint(1, 10) for x in range(num_dice)]
		results.sort(reverse=True)
		outcome = 0
		for res in results:
			if res >= difficulty:
				outcome += 1
			if res == 10:
				outcome += 1
			if res == 1:
				outcome -= 1
		if exert:
			outcome += 1
		exert_text = "*Exerting* " if exert else ""
		label_text = "({}) ".format(label) if label else ""
		return "rolled {} dice at Difficulty {} {}\n{}`{}`\n{}Outcome: **{}**".format(num_dice, difficulty, gt_9_diff_text, exert_text, results, label_text, outcome)
		

	async def respond_to_message(self, message, response):
		channel = message.channel
		author = message.author
		await channel.send("**<@{}>** {}".format(author.id, response))
		

def run_discord_bot():
	client = ContractClient()
	client.run(os.environ["BOT_PASSWORD"])
	return 0
