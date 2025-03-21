import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
import io
import csv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_PATH = "./data/database.sqlite"

if BOT_TOKEN is None:
	raise ValueError("DISCORD_TOKEN environment variable not set")

# Ensure data directory exists
if not os.path.exists("data"):
	os.makedirs("data")

# Setup SQLite database
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()
cursor.execute("""
	CREATE TABLE IF NOT EXISTS users (
		discordId TEXT PRIMARY KEY,
		country TEXT NOT NULL,
		interests TEXT NOT NULL,
		platforms TEXT NOT NULL
	)
""")
conn.commit()

# Define static data
countries = [
	"Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
	"Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
	"Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia",
	"Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica",
	"Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt",
	"El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon",
	"Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana",
	"Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel",
	"Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Korea, North", "Korea, South", "Kuwait",
	"Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg",
	"Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico",
	"Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru",
	"Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Macedonia", "Norway", "Oman", "Pakistan",
	"Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar",
	"Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino",
	"Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
	"Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland",
	"Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia",
	"Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay",
	"Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

communityInvolvementOptions = [
	{ "label": "Get feedback", "value": "feedback", "description": "Get advice and guidance on your app's design, paywall strategy, or anything else" },
	{ "label": "Get product and content updates", "value": "updates", "description": "Stay up-to-date with Adapty features and learning materials" },
	{ "label": "Learn new monetization strategies", "value": "learn", "description": "Learn insights about creating a sustainable app business" },
	{ "label": "Promote my app", "value": "promote", "description": "Share your work with our community of app makers" },
	{ "label": "Get support", "value": "support", "description": "Chat with our support team about Adapty SDK or products" },
	{ "label": "Network with others", "value": "network", "description": "Learn and grow with your fellow app builders" },
	{ "label": "Other", "value": "other", "description": "Drop it in the #community-chat channel" }
]

platformOptions = [
	{ "label": "iOS - Swift", "value": "iOS - Swift" },
	{ "label": "Android - Kotlin", "value": "Android - Kotlin" },
	{ "label": "React Native", "value": "React Native" },
	{ "label": "Flutter or Flutterflow", "value": "Flutter" },
	{ "label": "Unity", "value": "Unity" }
]

# Create the bot with the required intents
intents = discord.Intents.default()
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Autocomplete for country ---
async def country_autocomplete(interaction: discord.Interaction, current: str):
	current_lower = current.lower()
	suggestions = [country for country in countries if current_lower in country.lower()]
	return [app_commands.Choice(name=country, value=country) for country in suggestions[:25]]

# --- Define Select Menus using discord.ui ---

class InvolvementSelect(discord.ui.Select):
	def __init__(self):
		options = []
		for option in communityInvolvementOptions:
			options.append(discord.SelectOption(
				label=option["label"],
				value=option["value"],
				description=option["description"]
			))
		super().__init__(placeholder="Select your interests (multiple allowed)",
						 min_values=1, max_values=len(options), options=options)
	
	async def callback(self, interaction: discord.Interaction):
		selected_interests = ",".join(self.values)
		user_id = str(interaction.user.id)
		cursor.execute("UPDATE users SET interests = ? WHERE discordId = ?", (selected_interests, user_id))
		conn.commit()
		view = PlatformSelectView()
		await interaction.response.edit_message(content="Saved your interests. Now, what platforms are you working with?", view=view)

class InvolvementSelectView(discord.ui.View):
	def __init__(self, timeout=180):
		super().__init__(timeout=timeout)
		self.add_item(InvolvementSelect())

class PlatformSelect(discord.ui.Select):
	def __init__(self):
		options = []
		for option in platformOptions:
			options.append(discord.SelectOption(label=option["label"], value=option["value"]))
		super().__init__(placeholder="Select the platforms you're working with",
						 min_values=1, max_values=len(options), options=options)
	
	async def callback(self, interaction: discord.Interaction):
		selected_platforms = ",".join(self.values)
		user_id = str(interaction.user.id)
		cursor.execute("UPDATE users SET platforms = ? WHERE discordId = ?", (selected_platforms, user_id))
		conn.commit()
		await interaction.response.edit_message(content=f"Your onboarding is complete!\nPlatforms: {selected_platforms}", view=None)

class PlatformSelectView(discord.ui.View):
	def __init__(self, timeout=180):
		super().__init__(timeout=timeout)
		self.add_item(PlatformSelect())

# --- Slash Commands ---

# /onboarding command with autocomplete for country
@bot.tree.command(name="onboarding", description="Start the onboarding process")
@app_commands.describe(country="Type to search for your country")
@app_commands.autocomplete(country=country_autocomplete)
async def onboarding(interaction: discord.Interaction, country: str):
	user_id = str(interaction.user.id)
	# Insert or update the user record in the database
	cursor.execute(
		"INSERT OR REPLACE INTO users (discordId, country, interests, platforms) VALUES (?, ?, ?, ?)",
		(user_id, country, "", "")
	)
	conn.commit()
	view = InvolvementSelectView()
	await interaction.response.send_message(content=f"You selected **{country}**. Now, what are you interested in? (Select all that apply)", view=view, ephemeral=True)

# /view_users command for admins only
@bot.tree.command(name="view_users", description="View all onboarded users (Admin only)")
async def view_users(interaction: discord.Interaction):
	# Check if the user has administrator permissions
	if not interaction.user.guild_permissions.administrator:
		await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
		return
	cursor.execute("SELECT * FROM users")
	rows = cursor.fetchall()
	if not rows:
		await interaction.response.send_message("No users found in the database.", ephemeral=True)
		return
	embed = discord.Embed(title="Onboarded Users", color=0x0099ff)
	description_lines = []
	for row in rows:
		discord_id, country, interests, platforms = row
		description_lines.append(f"👤 <@{discord_id}> - **{country}** - **Interests:** {interests} - **Platforms:** {platforms}")
	description = "\n".join(description_lines)
	if len(description) > 4096:
		description = description[:4093] + "..."
	embed.description = description
	embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
	embed.timestamp = discord.utils.utcnow()
	
	# Create CSV content in memory
	csv_buffer = io.StringIO()
	writer = csv.writer(csv_buffer)
	writer.writerow(["Discord ID", "Country", "Interests", "Platforms"])
	for row in rows:
		writer.writerow(row)
	csv_buffer.seek(0)
	file = discord.File(fp=io.BytesIO(csv_buffer.read().encode()), filename="user_data.csv")
	
	await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

# --- On Ready ---
@bot.event
async def on_ready():
	print(f"Logged in as {bot.user} (ID: {bot.user.id})")
	try:
		synced = await bot.tree.sync()
		print(f"Synced {len(synced)} commands")
	except Exception as e:
		print(e)

bot.run(BOT_TOKEN)