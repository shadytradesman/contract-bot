import logging
import os
import random
from venv import create

import discord
from discord.ext import commands
from discord.ext.commands import command, before_invoke

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

@commands.command(name='!help')
async def call_for_help(ctx):
	help_message_result = help_message()
	await respond_to_message(ctx, help_message_result)

async def invalid_usage(ctx, error):
	await respond_to_message(ctx, error_usage_message(error))

async def roll_dice(ctx, dice, diff, *arg):
	logger.debug("rolling dice")
	exert = False
	label = None
	exert_or_labels = arg[0]


	if len(exert_or_labels) == 1:
		if TOKENS['help'] in exert_or_labels:
			help_message_result = help_message()
			await respond_to_message(ctx, help_message_result)
			return
		elif TOKENS['exertion'] in exert_or_labels:
			exert = True
	elif len(exert_or_labels) >= 2:
		label_args = []
		if TOKENS['exertion'] == exert_or_labels[1]:
			exert=True
			if len(exert_or_labels) > 2:
				label_args = exert_or_labels[2:]
		else:
			label_args = exert_or_labels[1:]
		if label_args:
			label = " ".join(label_args)
	num_dice = dice
	if num_dice >= 50:
		await respond_to_message(ctx, error_usage_message("too many dice, use less than 50"))
		return

	msg = contract_roll(dice, diff, exert, label)
	await respond_to_message(ctx, msg)


@commands.command(name='!l')
async def roll_low(ctx):
	logger.debug("calling low")
	flip_results = flip(False)
	await respond_to_message(ctx, flip_results)

@commands.command(name='!h')
async def roll_high(ctx):
	logger.debug("calling high")
	flip_results = flip(True)
	await respond_to_message(ctx, flip_results)

@commands.command(name='! help')
async def help_selection(ctx):
	help_message_result = help_message()
	await respond_to_message(ctx, help_message_result)

def help_message():
	help_lines = ["**Welcome to The Contract's Dice Rolling Bot!**",
                  "This bot can help you roll dice for the game The Contract https://www.TheContractRPG.com/ ",
                  "Contribute to my source code: {}".format(bot_repo_url),
                  "Add this bot to your server: {}".format(bot_invite_url), usage_message()]
	return "\n".join(help_lines)

def error_usage_message(error=None):
	if error:
		return "Error - {}\n{}".format(error, usage_message())
	return usage_message()

def usage_message():
	usage_lines = ["**Usage:**",
				   "`{}{}` Display help".format(TOKENS["prefix"], TOKENS["help"]),
				   "`{}3` Roll 3 dice default difficulty 6".format(TOKENS["prefix"]),
				   "`{}4{}8` Roll 4 dice difficulty 8".format(TOKENS["prefix"], TOKENS["roll_seperator"]),
				   "`{}5 {}` Roll 5 dice default difficulty 6 and exert".format(TOKENS["prefix"], TOKENS["exertion"]),
				   "`{}5 {} to slay the dragon` Roll 5 dice default difficulty 6 and exert using an action label".format(TOKENS["prefix"], TOKENS["exertion"]),
				   "`{}{}` Flip a coin calling 'high'".format(TOKENS["prefix"], TOKENS["flip_high"]),
				   "`{}{}` Flip a coin calling 'low'".format(TOKENS["prefix"], TOKENS["flip_low"]),
				   ]
	return "\n".join(usage_lines)

async def respond_to_message(ctx, response):
	channel = ctx.message.channel
	author = ctx.message.author
	await channel.send("**<@{}>** {}".format(author.id, response))

def flip(is_high):
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


class CommandHelper:
	def __init__(self, dice_diff, num_dice, difficulty):
		@commands.command(name=dice_diff)
		async def d_command(ctx, *args):
			await dice_roll(ctx, num_dice, difficulty, args)
		self.command = d_command

async def dice_roll(ctx, dice, diff, args):
	await roll_dice(ctx, dice, diff, args)


def create_roll_combinations(dice_bot):
	min_dice = 1
	max_dice = 50
	min_diff = 1
	max_diff = 15

	for dice in range(min_dice,max_dice):
		dice_diff = "!{}".format(dice)
		default_difficulty = 6
		obj = CommandHelper(dice_diff, dice, default_difficulty)
		dice_bot.add_command(obj.command)

		for diff in range(min_diff,max_diff):
			dice_diff = "!{}@{}".format(dice, diff)
			obj = CommandHelper(dice_diff, dice, diff)
			dice_bot.add_command(obj.command)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.add_command(roll_low)
bot.add_command(roll_high)
bot.add_command(call_for_help)
create_roll_combinations(bot)

@bot.event
async def on_command_error(ctx, error):
	command_from_user = list(ctx.invoked_with)
	if command_from_user[0] != '!':
		return

	contextual_error = ""
	if not command_from_user[1].isdigit():
		contextual_error = contextual_error + "\nnumber of dice expected, input not a valid number"

	if TOKENS['roll_seperator'] in command_from_user:
		roll = ctx.invoked_with[1:].split('@')
		dice = roll[0]
		diff = roll[1]

		if not dice.isdigit():
			contextual_error = contextual_error + "\ndice is not a number"
		if int(dice) > 49:
			contextual_error = contextual_error + "\ntoo many dice rolled, maximum is 49"
		if not diff.isdigit():
			contextual_error = contextual_error + "\ndifficulty is not a number"
		if int(diff) > 14:
			contextual_error = contextual_error + "\ndifficulty is not a valid number, maximum is 14"

	contextual_error = contextual_error + "\n"
	await invalid_usage(ctx, contextual_error)

bot.run(os.environ["BOT_PASSWORD"])
