import logging
import os
import random
import re
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
CONTRACT_ROLL_REGEX = re.compile('(\d+)(@(\d+))?$')
ARBITRARY_ROLL_REGEX = re.compile('(\d+)d(\d+)$')
HIGH_LOW_ROLL_REGEX = re.compile('[hHlL]$')


class RollError(Exception):
	pass


bot = commands.Bot()


@bot.slash_command(
	name="roll",
	description=f"Roll some dice. Type '{TOKENS['help']}' for more info"
)
async def roll_dice(ctx, message: discord.Option(str)):
	trimmed_message = message.strip()
	if trimmed_message == TOKENS["help"]:
		await ctx.send_response(help_message(), ephemeral=True)
		return
	try:
		roll_response = get_roll_response(trimmed_message)
		if roll_response is not None:
			await ctx.send_response(roll_response)
		else:
			response = "\n".join([
				"Invalid command: {}".format(trimmed_message.split()[0]),
				usage_message()
			])
			await ctx.send_response(response, ephemeral=True)
	except RollError as err:
		response = "\n".join([
			"Invalid command: {}".format(trimmed_message.split()[0]),
			"Reason: {}".format(err.args[0]),
		])
		await ctx.send_response(response, ephemeral=True)


def get_roll_response(command_from_user):
	tokens = command_from_user.split()
	roll_token = tokens[0].lower()
	m = CONTRACT_ROLL_REGEX.match(roll_token)
	if m:
		groups = m.groups()
		difficulty = int(groups[2] if groups[2] is not None else DEFAULT_DIFFICULTY)
		return get_contract_roll_response(
			num_dice=int(groups[0]),
			difficulty=difficulty,
			rest_of_message=tokens[1:] if len(tokens) > 1 else None)
	m = ARBITRARY_ROLL_REGEX.match(roll_token)
	if m:
		num_dice = m.group(1)
		dice_type = m.group(2)
		return get_general_roll_response(int(num_dice), int(dice_type))
	m = HIGH_LOW_ROLL_REGEX.match(roll_token)
	if m:
		return flip(is_high= roll_token.lower() == 'h')
	return None


def get_contract_roll_response(num_dice, difficulty, rest_of_message=None):
	if num_dice < MIN_DICE:
		raise RollError("Too few dice rolled. Minimum is {}.".format(MIN_DICE))
	if num_dice > MAX_DICE:
		raise RollError("Too many dice rolled. Maximum is {}.".format(MAX_DICE))
	if difficulty < MIN_DIFFICULTY:
		raise RollError("Difficulty is not a valid. Minimum is {}.".format(MIN_DIFFICULTY))
	if difficulty - 9 >= num_dice:
		raise RollError("Difficulty over 9 reduced dice rolled to zero. Outcome is 0.")
	if rest_of_message:
		use_exert = rest_of_message[0].lower() == TOKENS["exertion"]
		label = ' '.join(rest_of_message[1:]) if use_exert and len(rest_of_message) > 1 else ' '.join(rest_of_message)
	else:
		use_exert = None
		label = None
	return contract_roll(num_dice, difficulty, use_exert, label)


def get_general_roll_response(num_dice, dice_type):
	if num_dice < MIN_DICE:
		raise RollError("Too few dice rolled. Minimum is {}.".format(MIN_DICE))
	if num_dice > MAX_DICE:
		raise RollError("Too many dice rolled. Maximum is {}.".format(MAX_DICE))
	if dice_type < 2 or dice_type > 500:
		raise RollError("Dice must have between 2 and 500 sides")
	results = [random.randint(1, dice_type) for x in range(num_dice)]
	results.sort(reverse=True)
	outcome = sum(results)
	response = []
	response.append("Rolled {} {} with {} sides".format(num_dice, "die" if num_dice == 1 else "dice", dice_type))
	response.append("`{}`".format(results))
	if num_dice > 1:
		response.append("Sum: **{}**".format(outcome))
	if dice_type == 10:
		outcome = 0
		for res in results:
			if res >= DEFAULT_DIFFICULTY:
				outcome += 1
			if res == 10:
				outcome += 1
			if res == 1:
				outcome -= 1
		response.append("*Omit the 'd10' from your command to make a Contract roll. At Difficulty 6, this one's Outcome would have been {}*".format(outcome))
	return "\n".join(response)


def help_message():
	help_lines = [
		"**Welcome to The Contract's Dice Rolling Bot!**",
		"This bot can help you roll dice for the game [The Contract RPG](https://www.TheContractRPG.com/) ",
		"Contribute to my source code: [click here](<{}>)".format(bot_repo_url),
		"Add this bot to your server: [click here]({})".format(bot_invite_url),
		"Read the Privacy Policy: [click here]({})".format(bot_info_url),
		usage_message(),
	]
	return "\n".join(help_lines)


def usage_message():
	usage_lines = [
		"**Usage for /roll command:**",
		"* General",
		"  * `{}` Display help".format(TOKENS["help"]),
		"* Contract Rolls",
		"  * `3` Roll 3 dice at default Difficulty 6",
		"  * `4{}8` Roll 4 dice Difficulty 8".format(TOKENS["roll_seperator"]),
		"  * `5 {}` Roll 5 dice at default Difficulty 6 and exert".format(TOKENS["exertion"]),
		"  * `5 Shaggy initiative` Roll 5 dice at default Difficulty 6 and label `Shaggy initiative`",
		"  * `5 {} to sneak under the cameras` Roll 5 dice at default Difficulty 6 and exert using a label for the roll".format(TOKENS["exertion"]),
		"* General Rolls",
		"  * `4d6` Roll 4 6-sided dice",
		"  * `10d2` Roll 10 2-sided dice",
		"* Coins",
		"  * `{}` Flip a coin calling 'high'".format(TOKENS["flip_high"]),
		"  * `{}` Flip a coin calling 'low'".format(TOKENS["flip_low"]),
	]
	return "\n".join(usage_lines)


def flip(is_high):
	result = random.randint(1, 10)
	success = (is_high and result >= 6) or ((not is_high) and result <= 5)
	return "Rolled high/low calling **{}**\n`{}`\nOutcome: **{}**".format("high" if is_high else "low", result, "SUCCESS" if success else "FAILURE")


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
	response.append("Rolled {} {} at Difficulty {} {}".format(num_dice, "die" if num_dice == 1 else "dice", difficulty, gt_9_diff_text))
	response.append("{}`{}`".format(exert_text, results))
	response.append("\({}\) Outcome: **{}**".format(label_text, outcome) if label_text is not None else "Outcome: **{}**".format(outcome))
	return "\n".join(response)


def run_bot():
	print("Running bot")
	bot.run(os.environ["BOT_PASSWORD"])
