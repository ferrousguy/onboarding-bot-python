import discord
from discord.ext import commands
from discord import app_commands
import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

if BOT_TOKEN is None:
	raise ValueError("DISCORD_TOKEN environment variable not set")
	
# Define the scope for Google Sheets API
SCOPES = [
	"https://www.googleapis.com/auth/spreadsheets",
	"https://www.googleapis.com/auth/drive"
]

class GoogleSheetsManager:
	def __init__(self):
		self.credentials = None
		self.spreadsheet = None
		self.worksheet = None
		self._initialize_google_sheets()
	
	def _initialize_google_sheets(self):
		"""Initialize Google Sheets connection with service account credentials."""
		try:
			# Try to load credentials from environment variable
			service_account_info = os.getenv("GOOGLE_CREDENTIALS")
			if service_account_info:
				import json
				service_account_dict = json.loads(service_account_info)
				self.credentials = Credentials.from_service_account_info(
					service_account_dict, scopes=SCOPES
				)
			else:
				# Fall back to credentials file
				credentials_path = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
				self.credentials = Credentials.from_service_account_file(
					credentials_path, scopes=SCOPES
				)
			
			# Connect to Google Sheets
			self.client = gspread.authorize(self.credentials)
			
			# Get spreadsheet by ID or create it if needed
			spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
			if spreadsheet_id:
				self.spreadsheet = self.client.open_by_key(spreadsheet_id)
			else:
				spreadsheet_name = os.getenv("GOOGLE_SHEET_NAME", "Discord Onboarding Data")
				try:
					self.spreadsheet = self.client.open(spreadsheet_name)
				except gspread.exceptions.SpreadsheetNotFound:
					self.spreadsheet = self.client.create(spreadsheet_name)
					print(f"Created new spreadsheet: {spreadsheet_name}")
					print(f"Spreadsheet ID: {self.spreadsheet.id}")
					print("Please set the GOOGLE_SHEET_ID environment variable to this value")
			
			# Get worksheet or create it
			worksheet_name = os.getenv("GOOGLE_WORKSHEET_NAME", "User Data")
			try:
				self.worksheet = self.spreadsheet.worksheet(worksheet_name)
			except gspread.exceptions.WorksheetNotFound:
				self.worksheet = self.spreadsheet.add_worksheet(
					title=worksheet_name, rows=1000, cols=10
				)
				
				# Initialize header row
				self.worksheet.append_row([
					"Discord ID", 
					"Username", 
					"Country", 
					"Interests", 
					"Platforms", 
					"Timestamp"
				])
				
			print(f"Connected to Google Sheets: {self.spreadsheet.title} / {self.worksheet.title}")
			
		except Exception as e:
			print(f"Error initializing Google Sheets: {e}")
			raise

	def add_user_data(self, discord_id, username, country, interests, platforms):
		"""Add a new row with user data to the spreadsheet."""
		try:
			from datetime import datetime
			timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			
			# Add the row to the spreadsheet
			self.worksheet.append_row([
				discord_id,
				username,
				country,
				interests,
				platforms,
				timestamp
			])
			return True
		except Exception as e:
			print(f"Error adding user data: {e}")
			return False
		
	def get_all_users(self):
		"""Get all user data from the worksheet."""
		try:
			# Get all records (excluding header row)
			return self.worksheet.get_all_records()
		except Exception as e:
			print(f"Error getting user data: {e}")
			return []

# Initialize the Google Sheets manager
sheets_manager = GoogleSheetsManager()

# Store user data temporarily during onboarding process
user_data_store = {}

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
intents.members = True
intents.message_content = True
intents.reactions = True
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
		
		# Update the temporary data store
		if user_id in user_data_store:
			user_data_store[user_id]["interests"] = selected_interests
		
		view = PlatformSelectView()
		await interaction.response.edit_message(
			content="Saved your interests. Now, what platforms are you working with?", 
			view=view
		)

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
		username = interaction.user.display_name
		
		# Complete the user data and save to Google Sheets
		if user_id in user_data_store:
			user_data = user_data_store[user_id]
			user_data["platforms"] = selected_platforms
			
			# Save to Google Sheets
			success = sheets_manager.add_user_data(
				discord_id=user_id,
				username=username,
				country=user_data["country"],
				interests=user_data["interests"],
				platforms=selected_platforms
			)
			
			if success:
				# Clean up the temporary storage
				user_data_store.pop(user_id, None)
				await interaction.response.edit_message(
					content=f"Your onboarding is complete!\nThank you for sharing your information.", 
					view=None
				)
			else:
				await interaction.response.edit_message(
					content="There was an error saving your information. Please try again or contact an administrator.",
					view=None
				)
		else:
			await interaction.response.edit_message(
				content="Your session has expired. Please restart the onboarding process with /onboarding.",
				view=None
			)

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
	
	# Store initial data in the temporary store
	user_data_store[user_id] = {
		"country": country,
		"interests": "",
		"platforms": ""
	}

	view = InvolvementSelectView()
	await interaction.response.send_message(
		content=f"You selected **{country}**. Now, what are you interested in? (Select all that apply)",
		view=view,
		ephemeral=True
	)

# --- On Ready ---
@bot.event
async def on_ready():
	print(f"Logged in as {bot.user} (ID: {bot.user.id})")
	print(f"Bot is a member of the following guilds:")
	for guild in bot.guilds:
		print(f"{guild.name} (ID: {guild.id})")
		
	try:
		guild = discord.Object(id=878003622917587034)
		synced = await bot.tree.sync(guild=guild)
		print(f"Synced {len(synced)} commands to guild {guild.id}")
	except Exception as e:
		print(e)

bot.run(BOT_TOKEN)