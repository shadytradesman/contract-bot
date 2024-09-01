import logging
import os
import random
import discord
from discord.ext import commands


logger = logging.getLogger('bot')
bot_invite_url = "https://discord.com/api/oauth2/authorize?client_id=944989207665967124&permissions=309237738560&scope=bot"
bot_repo_url = "https://github.com/shadytradesman/contract-bot"
TOKENS = {
		"prefix": "!!",
		"roll_seperator": "@",
		"exertion": "ex",
		"help": "help",
		"flip_high": "h",
		"flip_low": "l",
}

@commands.command(name='!')
async def roll_dice(ctx, *arg):
	logger.debug("rolling dice")
	exert = False
	label = None
	label_args = []
	if len(arg) == 1:
		if TOKENS['help'] in arg[0]:
			help_message_result = help_message()
			await respond_to_message(ctx, help_message_result)
			return
	elif len(arg) >= 2:
		if TOKENS['exertion'] == arg[1]:
			exert=True
			if len(arg) > 2:
				label_args = arg[2:]
		else:
			label_args = arg[1:]
		if label_args:
			label = " ".join(label_args)
	else:
		await respond_to_message(ctx, error_usage_message("did not recognize message format"))
		return

	roll_values = arg[0].split(TOKENS['roll_seperator'])
	if not roll_values[0].isdigit():
		await respond_to_message(ctx, error_usage_message("num dice not a number"))
		return
	num_dice = int(roll_values[0])
	if num_dice >= 50:
		await respond_to_message(ctx, error_usage_message("too many dice, use less than 50"))
		return

	if len(roll_values) > 1 and not roll_values[1].isdigit():
		await respond_to_message(ctx, error_usage_message("difficulty not a number"))
		return
	difficulty = int(roll_values[1]) if ((TOKENS['roll_seperator'] in arg[0]) and (roll_values[1].isdigit)) else 6

	msg = contract_roll(num_dice, difficulty, exert, label)
	await respond_to_message(ctx, msg)


@commands.command(name='!l')
async def roll_low(ctx):
	logger.debug("calling low")
	flip_results = flip(ctx, False)
	await respond_to_message(ctx, flip_results)

@commands.command(name='!h')
async def roll_high(ctx):
	logger.debug("calling high")
	flip_results = flip(ctx, True)
	await respond_to_message(ctx, flip_results)

@commands.command(name='! help')
async def help(ctx):
	help_message_result = help_message()
	await respond_to_message(ctx, help_message_result)

def help_message():
	help_lines = []
	help_lines.append("**Welcome to The Contract's Dice Rolling Bot!**")
	help_lines.append("This bot can help you roll dice for the game The Contract https://www.TheContractRPG.com/ ")
	help_lines.append("Contribute to my source code: {}".format(bot_repo_url))
	help_lines.append("Add this bot to your server: {}".format(bot_invite_url))
	help_lines.append(usage_message())
	return "\n".join(help_lines)

def error_usage_message(error=None):
	if error:
		return "Error - {}\n{}".format(error, usage_message())
	return usage_message()

def usage_message():
	usage_lines = []
	usage_lines.append("**Usage:**")
	usage_lines.append("`{} {}` Display help".format(TOKENS["prefix"], TOKENS["help"]))
	usage_lines.append("`{} 3` Roll 3 dice difficulty 6".format(TOKENS["prefix"]))
	usage_lines.append("`{} 4{}8` Roll 4 dice difficulty 8".format(TOKENS["prefix"], TOKENS["roll_seperator"]))
	usage_lines.append("`{} 5 {}` Roll 5 dice difficulty 6 and exert".format(TOKENS["prefix"], TOKENS["exertion"]))
	usage_lines.append("`{}{}` Flip a coin calling 'high'".format(TOKENS["prefix"], TOKENS["flip_high"]))
	usage_lines.append("`{}{}` Flip a coin calling 'low'".format(TOKENS["prefix"], TOKENS["flip_low"]))
	return "\n".join(usage_lines)

async def respond_to_message(ctx, response):
	channel = ctx.message.channel
	author = ctx.message.author
	await channel.send("**<@{}>** {}".format(author.id, response))

def flip(ctx, is_high):
	result = random.randint(1, 10)
	success = (is_high and result >= 6) or ((not is_high) and result <= 5)
	return "rolled high/low calling **{}**\n`{}`\nOutcome: **{}**".format("high" if is_high else "low", result, "SUCCESS" if success else "FAILURE")


def contract_roll( num_dice, difficulty=6, exert=False, label_text=None):
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
	response = []
	response.append("rolled {} dice at Difficulty {} {}".format(num_dice, difficulty, gt_9_diff_text))
	response.append("{}`{}`".format(exert_text, results))
	response.append("\({}\) Outcome: **{}**".format(label_text, outcome) if label_text is not None else "Outcome: **{}**".format(outcome))
	return "\n".join(response)


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.add_command(roll_dice)
bot.add_command(roll_low)
bot.add_command(roll_high)
bot.run(os.environ["BOT_PASSWORD"])
