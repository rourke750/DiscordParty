from ..mappings.mapping import DRole

def has_permission_or_role(ctx):
    for r in ctx.author.roles:
        if r.name == DRole.ADMIN_ROLE.value:
            return True
    return ctx.author.guild_permissions.administrator