import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv

# ── Configuration ──────────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

EMOJIS = [
    "🇬",   # regional_indicator_g
    "🇦",   # regional_indicator_a
    "🇾",   # regional_indicator_y
    "🇵",   # regional_indicator_p
    "🇴",   # regional_indicator_o
    "🇷",   # regional_indicator_r
    "🇳",   # regional_indicator_n
    "⚫",   # black_circle
    "🟠",   # orange_circle
    "🍆",   # eggplant
    "🩲",   # briefs
    "💦",   # sweat_drops
    "🦧",   # orangutan
    "🐒",   # monkey
    "🦍",   # gorilla
]

DELAI_ENTRE_REACTIONS = 0.5

# ── Setup du bot ───────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True  # Nécessaire pour lire les messages

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 {len(synced)} commande(s) slash synchronisée(s)")
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation : {e}")


@bot.tree.command(name="singe", description="Singifie le dernier message 🐒")
@app_commands.describe(nombre=f"Nombre de messages à remonter (défaut: 1, max: 10)")
async def singe(interaction: discord.Interaction, nombre: int = 1):
    """Réagit au(x) dernier(s) message(s) avec une série d'emojis prédéfinis."""
    print(f"[CMD] /singe reçu", flush=True)

    # Validation du paramètre
    if nombre < 1 or nombre > 10:
        await interaction.response.send_message(
            "⚠️ Le nombre doit être entre **1** et **10**.", ephemeral=True
        )
        return

    # Récupération des derniers messages du canal
    await interaction.response.defer(ephemeral=True)

    try:
        messages = []
        async for msg in interaction.channel.history(limit=nombre + 5):
            # On ignore les messages de bots et la commande elle-même
            if not msg.author.bot:
                messages.append(msg)
            if len(messages) >= nombre:
                break

        if not messages:
            await interaction.followup.send(
                "❌ Aucun message trouvé dans ce canal.", ephemeral=True
            )
            return

        # Application des réactions sur chaque message trouvé
        total_reactions = 0
        for msg in messages:
            for emoji in EMOJIS:
                try:
                    await msg.add_reaction(emoji)
                    total_reactions += 1
                    await asyncio.sleep(DELAI_ENTRE_REACTIONS)
                except discord.errors.Forbidden:
                    await interaction.followup.send(
                        "❌ Je n'ai pas la permission d'ajouter des réactions ici.",
                        ephemeral=True,
                    )
                    return
                except discord.errors.HTTPException as e:
                    print(f"Erreur HTTP lors de l'ajout de réaction : {e}")

        # Confirmation discrète (visible uniquement par l'utilisateur)
        msg_info = f"message de **{messages[0].author.display_name}**" if nombre == 1 else f"**{len(messages)}** messages"
        await interaction.followup.send(
            f"🐒 Réactions ajoutées sur le {msg_info} ! ({total_reactions} emojis posés)",
            ephemeral=True,
        )

    except discord.errors.Forbidden:
        await interaction.followup.send(
            "❌ Je n'ai pas accès à l'historique de ce canal.", ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Une erreur est survenue : `{e}`", ephemeral=True
        )


# ── Lancement ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN)