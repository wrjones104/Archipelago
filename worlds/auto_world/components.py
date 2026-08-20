from worlds.LauncherComponents import Component, Type, components, launch


def run_client(*args: str) -> None:
    from .client import main
    launch(main, name="AutoWorld Bot Manager", args=args)


components.append(
    Component(
        "AutoWorld Bot Manager",
        func=run_client,
        game_name="Auto World",
        component_type=Type.CLIENT,
        supports_uri=True,
        cli=True,
        description="Autonomous testing bots and live Web Dashboard for Archipelago.",
    )
)
