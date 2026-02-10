#!/usr/bin/python3 -u
import logging
import os
from pathlib import Path

import discord
from discord import Member, Message, Reaction, TextChannel, User

TOKEN = os.environ["DISCORD_TOKEN"]
GENERAL_CHANNEL_NAME = os.getenv("DISCORD_GENERAL_CHANNEL_NAME", "general")
LOG_FILE_PATH = os.getenv("DISCORD_LOG_FILE_PATH", Path(__file__).resolve().parent / "discord.log")


class MyClient(discord.Client):
    def init(self) -> None:
        self.rsvp_message_id_to_ctf_channel_id: dict[int, int] = {}

    async def on_ready(self) -> None:
        print("Logged on as", self.user)

    async def on_message(self, message: Message) -> None:
        if self.user is None:
            return
        if message.guild is None:
            return
        client_member = message.guild.get_member(self.user.id)
        if client_member is None:
            return
        # don't respond to ourselves
        if message.author == client_member:
            return
        if type(message.channel) != TextChannel:
            return
        if type(message.author) != Member:
            return
        if not message.content.startswith("-"):
            return

        commands = message.content.split(" ", 1)

        if message.content.startswith("-create"):
            if len(commands) == 2:
                rsvp = f"#{message.channel.name} ({commands[1]}) に参加する人はリアクションしてください"
            elif len(commands) == 1:
                rsvp = f"#{message.channel.name} に参加する人はリアクションしてください"

            channel_id = message.channel.id

            await message.channel.set_permissions(client_member, read_messages=True)
            await message.channel.set_permissions(message.guild.default_role, read_messages=False)

            # Reset previous permissions
            for member in message.channel.members:
                if member == client_member:
                    continue
                await message.channel.set_permissions(member, overwrite=None)

            general_channel = discord.utils.get(message.guild.text_channels, name=GENERAL_CHANNEL_NAME)
            if type(general_channel) != TextChannel:
                return
            rsvp_message = await general_channel.send(rsvp)
            self.rsvp_message_id_to_ctf_channel_id[rsvp_message.id] = channel_id
            await rsvp_message.add_reaction("👍")

        elif message.content.startswith("-over"):
            await message.channel.send(f"おつかれさまでした")
            await message.channel.set_permissions(message.guild.default_role, read_messages=True)

        elif message.content.startswith("-join"):
            if len(commands) != 2:
                return
            channel = discord.utils.get(message.guild.text_channels, name=commands[1])
            if type(channel) != TextChannel:
                return
            await channel.set_permissions(message.author, read_messages=True)

        elif message.content.startswith("-exit"):
            await message.channel.set_permissions(message.author, overwrite=None)

        elif message.content.startswith("-help"):
            await message.channel.send(
                """```-create [<ctf name>]
-over
-join <ctf channel>
-exit```"""
            )

    async def on_reaction_add(self, reaction: Reaction, user: Member | User) -> None:
        if reaction.message.author != self.user:
            return
        if type(user) != Member:
            return
        message_id = reaction.message.id
        if message_id not in self.rsvp_message_id_to_ctf_channel_id:
            return
        ctf_channel_id = self.rsvp_message_id_to_ctf_channel_id[message_id]
        if reaction.message.guild is None:
            return
        ctf_channel = reaction.message.guild.get_channel(ctf_channel_id)
        if type(ctf_channel) != TextChannel:
            return
        await ctf_channel.set_permissions(user, read_messages=True)


def main() -> None:
    handler = logging.FileHandler(filename=LOG_FILE_PATH, encoding="utf-8", mode="a")
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    # intents.reactions = True
    client = MyClient(intents=intents)
    client.init()
    client.run(TOKEN, log_handler=handler)


if __name__ == "__main__":
    main()
