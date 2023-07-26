#!/usr/bin/python3 -u
import logging
import os

import discord

TOKEN = os.environ["TOKEN"]
GENERAL_CHANNEL_NAME = "general"
LOG_FILE_NAME = "discord.log"


class MyClient(discord.Client):
    def init(self):
        self.cfp_message_id_to_ctf_channel_id = {}

    async def on_ready(self):
        print("Logged on as", self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if not message.content.startswith("-"):
            return

        commands = message.content.split(" ", 1)

        if message.content.startswith("-create"):
            if len(commands) == 2:
                cfp = f"#{message.channel.name} ({commands[1]}) に参加する人はリアクションしてください"
            elif len(commands) == 1:
                cfp = f"#{message.channel.name} に参加する人はリアクションしてください"

            channel_id = message.channel.id

            await message.channel.set_permissions(self.user, read_messages=True)
            await message.channel.set_permissions(message.guild.default_role, read_messages=False)

            # Reset previous permissions
            for member in message.channel.members:
                if member == self.user:
                    continue
                await message.channel.set_permissions(member, overwrite=None)

            general_channel = discord.utils.get(message.guild.channels, name=GENERAL_CHANNEL_NAME)
            cfp_message = await general_channel.send(cfp)
            self.cfp_message_id_to_ctf_channel_id[cfp_message.id] = channel_id
            await cfp_message.add_reaction("👍")

        elif message.content.startswith("-over"):
            await message.channel.send(f"おつかれさまでした")
            await message.channel.set_permissions(message.guild.default_role, read_messages=True)

        elif message.content.startswith("-join"):
            if len(commands) != 2:
                return
            channel = discord.utils.get(message.guild.channels, name=commands[1])
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

    async def on_reaction_add(self, reaction, user):
        if reaction.message.author != self.user:
            return
        message_id = reaction.message.id
        if message_id not in self.cfp_message_id_to_ctf_channel_id:
            return
        ctf_channel_id = self.cfp_message_id_to_ctf_channel_id[message_id]
        ctf_channel = reaction.message.guild.get_channel(ctf_channel_id)
        await ctf_channel.set_permissions(user, read_messages=True)


def main():
    handler = logging.FileHandler(filename=LOG_FILE_NAME, encoding="utf-8", mode="a")
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    # intents.reactions = True
    client = MyClient(intents=intents)
    client.init()
    client.run(TOKEN, log_handler=handler)


if __name__ == "__main__":
    main()
