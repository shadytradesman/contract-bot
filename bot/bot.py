import logging
import os
import random
import discord
from discord.ext import commands

logger = logging.getLogger('bot')
bot_invite_url = "https://discord.com/oauth2/authorize?client_id=944989207665967124"
bot_repo_url = "https://github.com/shadytradesman/contract-bot"
bot_info_url = "https://thecontractrpg.com/info/discord-bot/"
TOKENS = {
		"prefix": "!!",
		"roll_seperator": "@",
		"exertion": "ex",
		"help": "help",
		"flip_high": "h",
		"flip_low": "l",
}

MIN_DICE = 1
MAX_DICE = 49
MIN_DIFFICULTY = 4
MAX_DIFFICULTY = 15
DEFAULT_DIFFICULTY = 6

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_command_error(ctx, _error):
	command_from_user = ctx.invoked_with
	if command_from_user[0] != '!':
		return

	difficulty = None
	if TOKENS['roll_seperator'] in command_from_user:
		roll = command_from_user[1:].split('@')
		num_dice = roll[0]
		difficulty = roll[1]
	else:
		roll = command_from_user[1:].split(' ')
		num_dice = roll[0]

	contextual_error = ""
	if not num_dice.isdigit():
		contextual_error = contextual_error + "\nDice is not a number."
	elif int(num_dice) > MAX_DICE:
		contextual_error = contextual_error + "\nToo many dice rolled, maximum is {}.".format(MAX_DICE)
	if difficulty is not None and not difficulty.isdigit():
		contextual_error = contextual_error + "\nDifficulty is not a number."
	elif difficulty is not None and (int(difficulty) > MAX_DIFFICULTY):
		contextual_error = contextual_error + "\nDifficulty is not a valid number, maximum is {}.".format(MAX_DIFFICULTY)
	elif difficulty is not None and (int(difficulty) < MIN_DIFFICULTY):
		contextual_error = contextual_error + "\nDifficulty is not a valid number, minimum is {}.".format(MIN_DIFFICULTY)

	if len(contextual_error) == 0:
		contextual_error = "Incorrect usage, please try again."

	contextual_error = contextual_error + "\n"
	await invalid_usage(ctx, contextual_error)


@bot.command(name='!l')
async def roll_low(ctx):
	logger.debug("calling low")
	flip_results = flip(False)
	await respond_to_message(ctx, flip_results)


@bot.command(name='!h')
async def roll_high(ctx):
	logger.debug("calling high")
	flip_results = flip(True)
	await respond_to_message(ctx, flip_results)


@bot.command(name='!L')
async def roll_low(ctx):
	logger.debug("calling low")
	flip_results = flip(False)
	await respond_to_message(ctx, flip_results)


@bot.command(name='!H')
async def roll_high(ctx):
	logger.debug("calling high")
	flip_results = flip(True)
	await respond_to_message(ctx, flip_results)


@bot.command(name='!help')
async def call_for_help(ctx):
	await respond_to_message(ctx, help_message())


async def invalid_usage(ctx, error):
	await respond_to_message(ctx, error_usage_message(error))


def help_message():
	help_lines = [
		"**Welcome to The Contract's Dice Rolling Bot!**",
		"This bot can help you roll dice for the game [The Contract RPG](https://www.TheContractRPG.com/) ",
		"Contribute to my source code: [click here]({})".format(bot_repo_url),
		"Add this bot to your server: [click here]({})".format(bot_invite_url),
		"Read the Privacy Policy: [click here]({})".format(bot_info_url),
		usage_message(),
	]
	return "\n".join(help_lines)


def error_usage_message(error=None):
	if error:
		return "Error - {}\n{}".format(error, usage_message())
	return usage_message()


def usage_message():
	usage_lines = [
		"**Usage:**",
		"`{}{}` Display help".format(TOKENS["prefix"], TOKENS["help"]),
		"`{}3` Roll 3 dice default Difficulty 6".format(TOKENS["prefix"]),
		"`{}4{}8` Roll 4 dice Difficulty 8".format(TOKENS["prefix"], TOKENS["roll_seperator"]),
		"`{}5 {}` Roll 5 dice default Difficulty 6 and exert".format(TOKENS["prefix"], TOKENS["exertion"]),
		"`{}5 Shaggy initiative` Roll 5 dice default Difficulty 6 and label `Shaggy initiative`".format(TOKENS["prefix"]),
		"`{}5 {} to sneak under the cameras` Roll 5 dice default Difficulty 6 and exert using a label for the roll".format(TOKENS["prefix"], TOKENS["exertion"]),
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


async def roll_dice(ctx, dice, diff, *arg):
	logger.debug("rolling dice")
	exert = False
	label = None
	user_args = arg[0]

	if TOKENS['exertion'] in user_args:
		exert = True

	args_without_exertion = [x for x in user_args if x != TOKENS['exertion']]
	if args_without_exertion:
		label = " ".join(args_without_exertion)

	msg = contract_roll(dice, diff, exert, label)
	await respond_to_message(ctx, msg)


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


# This class allows each registered command to have a different reference, allowing the automated generation of
# Discord bot commands.
class CommandHelper:
	def __init__(self, command_name, num_dice, difficulty):
		@commands.command(name=command_name)
		async def d_command(ctx, *args):
			await roll_dice(ctx, num_dice, difficulty, args)
		self.command = d_command


def create_roll_combinations(dice_bot):
	for dice in range(MIN_DICE, MAX_DICE + 1):
		user_command = "!{}".format(dice)
		obj = CommandHelper(user_command, dice, DEFAULT_DIFFICULTY)
		dice_bot.add_command(obj.command)

		for diff in range(MIN_DIFFICULTY, MAX_DIFFICULTY + 1):
			user_command = "!{}@{}".format(dice, diff)
			obj = CommandHelper(user_command, dice, diff)
			dice_bot.add_command(obj.command)


create_roll_combinations(bot)
bot.run(os.environ["BOT_PASSWORD"])
