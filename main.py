import nextcord
import config
import matplotlib.pyplot as plt
from littlefield import Littlefield, MaterialsInfo
from nextcord.ext import commands, tasks
from nextcord import Intents, Interaction, SlashOption

intents = Intents.all()
intents.members = True

lf = Littlefield(config.TEAM_NAME, config.TEAM_PASSWORD, config.INSTITUTION)
lf_day = lf.live_day()

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    update_rich_presence.start()
    check_for_new_day.start()

@tasks.loop(seconds=20)
async def update_rich_presence():
    await bot.change_presence(activity=nextcord.Game(name="Updating..."))
    await bot.change_presence(activity=nextcord.Game(name=f"Cash: {lf.live_cash()}"))


@tasks.loop(seconds=20)
async def check_for_new_day():
    global lf_day
    if lf.live_day() != lf_day:
        lf_day = lf.live_day()
        channel = bot.get_channel(config.CHANNEL_ID)
        await channel.send(f"Day {lf_day} has started!")
    
@bot.command()
async def ping(ctx):
    print(ctx)


@bot.slash_command(guild_ids=[config.GUILD_ID])
async def cash(
    interaction: Interaction
):
    try:
        await interaction.response.send_message("Here is the cash graph:")
        plot = await plot_data(lf.cash(), 'Cash Flow', 'Day', 'Cash', 'cash_chart.png')
        await interaction.followup.send(file=plot)
    except FileNotFoundError:
        await interaction.response.send_message("The image file 'cash_chart.png' was not found.")

@bot.slash_command(guild_ids=[config.GUILD_ID])
async def queue_size(
    interaction: Interaction,
    station_number: int = SlashOption(name="station", description="The station number", required=True,
        choices={
            "Station 1": 1,
            "Station 2": 2,
            "Station 3": 3
        })
):
    try:
        await interaction.response.send_message("Here is the queue size graph for station " + str(station_number) + ":") 
        station = station_number == 1 and lf.station1 or station_number == 2 and lf.station2 or lf.station3
        plot = await plot_data(station.queue_size(), f"Station {station_number} Queue Size", 'Day', 'Jobs', 'queue_size_chart.png')
        await interaction.followup.send(file=plot)
    except FileNotFoundError:
        await interaction.response.send_message("The image file 'queue_size_chart.png' was not found.")

@bot.slash_command(guild_ids=[config.GUILD_ID])
async def utilization(
    interaction: Interaction,
    station_number: int = SlashOption(name="station", description="The station number", required=True,
        choices={
            "Station 1": 1,
            "Station 2": 2,
            "Station 3": 3
        })
):
    try:
        await interaction.response.send_message("Here is the utilization graph for station " + str(station_number) + ":")
        station = station_number == 1 and lf.station1 or station_number == 2 and lf.station2 or lf.station3
        plot = await plot_data(station.utilization(), f"Station {station_number} Utilization", 'Day', 'Utilization', 'utilization_chart.png')
        await interaction.followup.send(file=plot)
    except FileNotFoundError:
        await interaction.response.send_message("The image file 'utilization_chart.png' was not found.")

@bot.slash_command(guild_ids=[config.GUILD_ID])
async def inventory(
    interaction: Interaction,
):
    await interaction.response.send_message("Here is the inventory info:")
    info: MaterialsInfo = lf.materials.info()

    embed = nextcord.Embed(title="Materials", description="The current materials in the factory", color=0x00ff00)
    embed.add_field(name="Next Arrival ETA", value=info.next_arrival_eta or "N/A", inline=False)
    embed.add_field(name="Next Arrival Quantity", value=info.next_arrival_quantity or "N/A", inline=False)
    embed.add_field(name="Reorder Point", value=info.reorder_point or "N/A", inline=False)
    embed.add_field(name="Order Quantity", value=info.order_quantity or "N/A", inline=False)
    embed.add_field(name="Lead Time", value=info.lead_time or "N/A", inline=False)
    
    await interaction.followup.send(embed=embed)

    plot = await plot_data(lf.materials.inventory(), f"Inventory", 'Day', 'Quantity', 'inventory_chart.png')
    await interaction.followup.send(file=plot)

@bot.slash_command(guild_ids=[config.GUILD_ID])
async def incoming_jobs(
    interaction: Interaction,
):
    try:
        await interaction.response.send_message("Here is the incoming jobs graph:")
        plot = await plot_data(lf.orders.job_arrivals(), 'Incoming Jobs', 'Day', 'Jobs', 'incoming_jobs_chart.png')
        await interaction.followup.send(file=plot)
    except FileNotFoundError:
        await interaction.response.send_message("The image file 'incoming_jobs_chart.png' was not found.")

@bot.slash_command(guild_ids=[config.GUILD_ID])
async def lead_time(
    interaction: Interaction,
):
    try:
        await interaction.response.send_message("Here is the lead time graph:")
        print(lf.completed_jobs.lead_times())
        plot = await plot_data_multiple(lf.completed_jobs.lead_times(), 'Lead Time', 'Day', 'Time', 'lead_time_chart.png')
        await interaction.followup.send(file=plot)
    except FileNotFoundError:
        await interaction.response.send_message("The image file 'lead_time_chart.png' was not found.")

async def plot_data(data, title, x_label, y_label, file_name):
    x_values, y_values = zip(*data)
    plt.plot(x_values, y_values, linestyle='-', color='b')
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True)

    plt.savefig(file_name)
    plt.close()

    with open(file_name, 'rb') as image_file:
        return nextcord.File(image_file)

async def plot_data_multiple(data, title, x_label, y_label, file_name):
    for contract, _, points in data:
        x, y = zip(*points)
        plt.plot(x, y, label=contract)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.legend()
    plt.grid(True)

    plt.savefig(file_name)
    plt.close()

    with open(file_name, 'rb') as image_file:
        return nextcord.File(image_file)

bot.run(config.TOKEN)