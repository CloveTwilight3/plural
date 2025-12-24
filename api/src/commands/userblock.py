from asyncio import gather

from plural.errors import InteractionError

from src.core.models import env
from src.discord import (
    ApplicationCommandOptionType,
    ApplicationIntegrationType,
    InteractionContextType,
    ApplicationCommand,
    SlashCommandGroup,
    Interaction,
    Embed,
    User
)


userblock = SlashCommandGroup(
    name='userblock',
    description='Manage user access to the bot (admin only)',
    contexts=InteractionContextType.ALL(),
    integration_types=ApplicationIntegrationType.ALL()
)


def _check_admin(interaction: Interaction) -> None:
    """Check if the user is an admin"""
    if interaction.author_id not in env.admins:
        raise InteractionError(
            '❌ You do not have permission to use this command.'
        )


@userblock.command(
    name='add',
    description='Add a user to the blacklist/whitelist',
    options=[
        ApplicationCommand.Option(
            type=ApplicationCommandOptionType.USER,
            name='user',
            description='The user to add',
            required=True)],
    contexts=InteractionContextType.ALL(),
    integration_types=ApplicationIntegrationType.ALL())
async def slash_userblock_add(
    interaction: Interaction,
    user: User
) -> None:
    _check_admin(interaction)
    
    from src.user_access import user_access_manager
    
    mode = await user_access_manager.get_mode()
    added = await user_access_manager.add_user(user.id)
    
    if added:
        action = 'blacklisted' if mode == 'blacklist' else 'whitelisted'
        await interaction.response.send_message(embeds=[Embed.success(
            f'User <@{user.id}> (`{user.id}`) has been {action}.'
        )])
    else:
        await interaction.response.send_message(embeds=[Embed.warning(
            f'User <@{user.id}> (`{user.id}`) is already in the list.'
        )])


@userblock.command(
    name='remove',
    description='Remove a user from the blacklist/whitelist',
    options=[
        ApplicationCommand.Option(
            type=ApplicationCommandOptionType.USER,
            name='user',
            description='The user to remove',
            required=True)],
    contexts=InteractionContextType.ALL(),
    integration_types=ApplicationIntegrationType.ALL())
async def slash_userblock_remove(
    interaction: Interaction,
    user: User
) -> None:
    _check_admin(interaction)
    
    from src.user_access import user_access_manager
    
    removed = await user_access_manager.remove_user(user.id)
    
    if removed:
        await interaction.response.send_message(embeds=[Embed.success(
            f'User <@{user.id}> (`{user.id}`) has been removed from the list.'
        )])
    else:
        await interaction.response.send_message(embeds=[Embed.warning(
            f'User <@{user.id}> (`{user.id}`) was not in the list.'
        )])


@userblock.command(
    name='list',
    description='List all users in the blacklist/whitelist',
    contexts=InteractionContextType.ALL(),
    integration_types=ApplicationIntegrationType.ALL())
async def slash_userblock_list(
    interaction: Interaction
) -> None:
    _check_admin(interaction)
    
    from src.user_access import user_access_manager
    
    users = await user_access_manager.list_users()
    mode = await user_access_manager.get_mode()
    
    if not users:
        await interaction.response.send_message(embeds=[Embed(
            title=f'📋 The {mode} is empty',
            color=0x69ff69
        )])
        return
    
    # Build user list with proper formatting
    user_list_parts = []
    current_part = []
    current_length = 0
    
    for uid in users:
        line = f'• <@{uid}> (`{uid}`)\n'
        line_length = len(line)
        
        # Discord embed description limit is 4096 characters
        if current_length + line_length > 4000:
            user_list_parts.append(''.join(current_part))
            current_part = [line]
            current_length = line_length
        else:
            current_part.append(line)
            current_length += line_length
    
    if current_part:
        user_list_parts.append(''.join(current_part))
    
    # Send first embed
    embeds = [Embed(
        title=f'📋 {mode.title()} ({len(users)} users)',
        description=user_list_parts[0],
        color=0x69ff69
    )]
    
    await interaction.response.send_message(embeds=embeds)
    
    # Send additional embeds if needed
    for part in user_list_parts[1:]:
        await interaction.followup.send(embeds=[Embed(
            description=part,
            color=0x69ff69
        )])


@userblock.command(
    name='mode',
    description='Toggle between blacklist and whitelist mode',
    contexts=InteractionContextType.ALL(),
    integration_types=ApplicationIntegrationType.ALL())
async def slash_userblock_mode(
    interaction: Interaction
) -> None:
    _check_admin(interaction)
    
    from src.user_access import user_access_manager
    
    current_mode = await user_access_manager.get_mode()
    new_mode = 'whitelist' if current_mode == 'blacklist' else 'blacklist'
    await user_access_manager.set_mode(new_mode)
    
    await interaction.response.send_message(embeds=[Embed.success(
        title='Mode Changed',
        message=(
            f'Access control mode changed from **{current_mode}** to **{new_mode}**.\n\n'
            f'**{new_mode.title()} mode:** ' + (
                'Only users in the list can use the bot.'
                if new_mode == 'whitelist' else
                'Everyone except users in the list can use the bot.'
            )
        )
    )])


@userblock.command(
    name='clear',
    description='Clear all users from the list',
    contexts=InteractionContextType.ALL(),
    integration_types=ApplicationIntegrationType.ALL())
async def slash_userblock_clear(
    interaction: Interaction
) -> None:
    _check_admin(interaction)
    
    from src.user_access import user_access_manager
    
    count = await user_access_manager.clear_users()
    
    await interaction.response.send_message(embeds=[Embed.success(
        f'Cleared {count} user(s) from the list.'
    )])