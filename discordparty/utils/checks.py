def has_permission_or_role(ctx):
    for r in ctx.author.roles:
        if r.name == 'houseparty-admin':
            return True
    return ctx.author.guild_permissions.administrator