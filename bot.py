import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import json
from datetime import date
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
STREAKS_FILE = "streaks.json"

# ── Streak helpers ─────────────────────────────────────────────────────────────

def load_streaks() -> dict:
    """Charge le fichier de streaks, retourne un dict vide si absent."""
    if not os.path.exists(STREAKS_FILE):
        return {}
    with open(STREAKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_streaks(data: dict) -> None:
    """Sauvegarde le dict de streaks dans le fichier JSON."""
    with open(STREAKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def increment_streak(user_id: int) -> dict:
    """
    Incrémente le compteur d'utilisations pour user_id.
    Retourne les infos de streak : total, streak_actuel, record.
    """
    streaks = load_streaks()
    key = str(user_id)
    today = str(date.today())

    entry = streaks.get(key, {
        "total": 0,
        "streak": 0,
        "last_date": None,
        "record": 0,
    })

    # Mise à jour du streak journalier
    last = entry.get("last_date")
    if last == today:
        # Déjà singifié aujourd'hui → on incrémente quand même le streak
        entry["streak"] += 1
    else:
        # Nouveau jour → streak repart à 1
        entry["streak"] = 1
    entry["last_date"] = today

    entry["total"] += 1

    # Mise à jour du record
    if entry["streak"] > entry.get("record", 0):
        entry["record"] = entry["streak"]

    streaks[key] = entry
    save_streaks(streaks)
    return entry


def streak_message(entry: dict, display_name: str) -> str:
    """Génère le message de streak à afficher publiquement."""
    total   = entry["total"]
    streak  = entry["streak"]
    record  = entry["record"]

    # Emoji selon le palier de streak
    if streak >= 50:
        flame = "🔥🔥🔥"
    elif streak >= 20:
        flame = "🔥🔥"
    elif streak >= 5:
        flame = "🔥"
    else:
        flame = "🐒"

    record_str = f" *(nouveau record !)*" if streak == record and streak > 1 else f" *(record : {record})*" if record > 1 else ""
    return (
        f"{flame} **{display_name}** a singifié ! "
        f"| Streak : **{streak}**{record_str} "
        f"| Total : **{total}** singification{'s' if total > 1 else ''}"
    )


# ── Setup du bot ───────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 {len(synced)} commande(s) slash synchronisée(s)")
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation : {e}")


@bot.tree.command(name="singe", description="Singifie le dernier message d'un membre 🐒")
@app_commands.describe(membre="Le membre dont le dernier message sera singifié")
async def singe(interaction: discord.Interaction, membre: discord.Member):
    """Réagit au dernier message du membre ciblé avec une série d'emojis prédéfinis."""
    print(f"[CMD] /singe reçu par {interaction.user} → cible : {membre}", flush=True)

    # On ne peut pas se singifier soi-même (optionnel, décommenter si souhaité)
    # if membre == interaction.user:
    #     await interaction.response.send_message("⚠️ Tu ne peux pas te singifier toi-même !", ephemeral=True)
    #     return

    # On refuse de singifier un bot
    if membre.bot:
        await interaction.response.send_message(
            "⚠️ Impossible de singifier un bot.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        # Recherche du dernier message non-bot du membre dans le canal
        target_msg = None
        async for msg in interaction.channel.history(limit=200):
            if msg.author == membre and not msg.author.bot:
                target_msg = msg
                break

        if target_msg is None:
            await interaction.followup.send(
                f"❌ Aucun message récent de **{membre.display_name}** trouvé dans ce canal.",
                ephemeral=True,
            )
            return

        # Application des réactions
        for emoji in EMOJIS:
            try:
                await target_msg.add_reaction(emoji)
                await asyncio.sleep(DELAI_ENTRE_REACTIONS)
            except discord.errors.Forbidden:
                await interaction.followup.send(
                    "❌ Je n'ai pas la permission d'ajouter des réactions ici.",
                    ephemeral=True,
                )
                return
            except discord.errors.HTTPException as e:
                print(f"Erreur HTTP lors de l'ajout de réaction : {e}")

        # ── Streak ────────────────────────────────────────────────────────────
        entry = increment_streak(interaction.user.id)

        # ── Message public ────────────────────────────────────────────────────
        annonce = (
            f"🐒 **{interaction.user.display_name}** a singifié **{membre.display_name}** !\n"
            f"{streak_message(entry, interaction.user.display_name)}"
        )
        await interaction.channel.send(annonce)

        # Confirmation éphémère (visible uniquement par l'utilisateur)
        await interaction.followup.send(
            f"✅ Le dernier message de **{membre.display_name}** a été singifié ({len(EMOJIS)} emojis posés).",
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


@bot.tree.command(name="singe_stats", description="Affiche les stats de singification 🦍")
@app_commands.describe(membre="Membre dont voir les stats (toi par défaut)")
async def singe_stats(interaction: discord.Interaction, membre: discord.Member = None):
    """Affiche le total et le streak d'un membre."""
    cible = membre or interaction.user
    streaks = load_streaks()
    entry = streaks.get(str(cible.id))

    if not entry:
        await interaction.response.send_message(
            f"🐒 **{cible.display_name}** n'a encore jamais singifié.", ephemeral=False
        )
        return

    await interaction.response.send_message(
        f"📊 Stats de **{cible.display_name}** :\n"
        f"• Total : **{entry['total']}** singification{'s' if entry['total'] > 1 else ''}\n"
        f"• Streak actuel : **{entry['streak']}**\n"
        f"• Record de streak : **{entry['record']}**",
        ephemeral=False,
    )


# ── Lancement ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN)