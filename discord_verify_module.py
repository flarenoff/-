import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Получение токена из переменных окружения
TOKEN = os.getenv('DISCORD_TOKEN')

# Настройка интентов
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True

# Создание клиента бота
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self._users = {}  # {login: password}
        self.discord_users = {} # {discord_id: login}
        self.video_hosting_name = 'Floxarion'
        self.users_file = 'users.txt'

    async def setup_hook(self) -> None:
        # Синхронизируем слэш команды
        await self.tree.sync()
    
    def load_users(self):
        """Загрузка пользователей из файла users.txt"""
        try:
            with open(self.users_file, 'r') as f:
                for line in f:
                    if ":" in line:
                        login, password = line.strip().split(":")
                        self._users[login] = password
        except FileNotFoundError:
            print(f"Файл {self.users_file} не найден.")
        except Exception as e:
            print(f"Ошибка при загрузке пользователей: {e}")
    
    async def sync_commands(self):
        """Синхронизация команд"""
        await self.tree.sync()

client = MyClient(intents=intents)

@client.tree.command(name='login', description='Войти в свой аккаунт.')
async def login(interaction: discord.Interaction, login: str, password: str):
    """Команда для аутентификации пользователя"""
    if login in client._users and client._users[login] == password:
        client.discord_users[interaction.user.id] = login
        await interaction.response.send_message(f'Приветствую, {login}! Вы успешно залогинились на {client.video_hosting_name}.', ephemeral=True)
    else:
        await interaction.response.send_message('Неверный логин или пароль. Пожалуйста, попробуйте снова.', ephemeral=True)
    # Синхронизируем команды после изменения
    await client.sync_commands()


@client.tree.command(name='whoami', description='Узнать под каким логином вы залогинились.')
async def whoami(interaction: discord.Interaction):
    """Команда для показа логина пользователя"""
    if interaction.user.id in client.discord_users:
        login = client.discord_users[interaction.user.id]
        await interaction.response.send_message(f'Вы залогинены как: {login}', ephemeral=True)
    else:
        await interaction.response.send_message('Вы не залогинены. Пожалуйста, используйте команду /login', ephemeral=True)
    # Синхронизируем команды после изменения
    await client.sync_commands()

@client.event
async def on_ready():
    client.load_users()
    print(f'Logged in as {client.user} (ID: {client.user.id})')

client.run(TOKEN)
