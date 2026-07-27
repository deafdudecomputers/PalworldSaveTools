from PySide6.QtWidgets import QMenu, QMenuBar
from PySide6.QtGui import QAction
from i18n import t
from palworld_aio import constants
class MenuFactory:
    @staticmethod
    def create_action(text, callback, parent=None):
        action = QAction(text, parent)
        action.triggered.connect(callback)
        return action
    @staticmethod
    def create_menu(parent, title, items):
        menu = QMenu(title, parent)
        for item in items:
            if item is None:
                menu.addSeparator()
            elif isinstance(item, tuple):
                text, callback = item
                menu.addAction(MenuFactory.create_action(text, callback, parent))
            elif isinstance(item, QMenu):
                menu.addMenu(item)
        return menu
class ContextMenuBuilder:
    def __init__(self, parent=None):
        self.parent = parent
        self.menu = QMenu(parent)
    def add_action(self, text, callback):
        self.menu.addAction(MenuFactory.create_action(text, callback, self.parent))
        return self
    def add_separator(self):
        self.menu.addSeparator()
        return self
    def build(self):
        return self.menu
def create_player_context_menu(parent, handlers):
    builder = ContextMenuBuilder(parent)
    builder.add_action(t('deletion.ctx.add_exclusion'), handlers.get('add_exclusion', lambda: None))
    builder.add_action(t('deletion.ctx.remove_exclusion'), handlers.get('remove_exclusion', lambda: None))
    builder.add_action(t('deletion.ctx.delete_player'), handlers.get('delete_player', lambda: None))
    builder.add_action(t('player.rename.menu'), handlers.get('rename_player', lambda: None))
    builder.add_action(t('player.viewing_cage.menu'), handlers.get('unlock_viewing_cage', lambda: None))
    builder.add_action(t('player.unlock_technologies.menu'), handlers.get('unlock_technologies', lambda: None))
    builder.add_separator()
    builder.add_action(t('player.inventory.menu'), handlers.get('edit_inventory', lambda: None))
    builder.add_separator()
    builder.add_action(t('deletion.ctx.delete_guild'), handlers.get('delete_guild', lambda: None))
    builder.add_action(t('guild.rename.menu'), handlers.get('rename_guild', lambda: None))
    builder.add_action(t('guild.unlock_lab_research.menu'), handlers.get('unlock_lab_research', lambda: None))
    builder.add_action(t('guild.menu.set_level'), handlers.get('set_guild_level', lambda: None))
    builder.add_action(t('button.import'), handlers.get('import_base', lambda: None))
    return builder.build()
def create_guild_context_menu(parent, handlers):
    builder = ContextMenuBuilder(parent)
    builder.add_action(t('deletion.ctx.add_exclusion'), handlers.get('add_exclusion', lambda: None))
    builder.add_action(t('deletion.ctx.remove_exclusion'), handlers.get('remove_exclusion', lambda: None))
    builder.add_action(t('deletion.ctx.delete_guild'), handlers.get('delete_guild', lambda: None))
    builder.add_action(t('guild.rename.menu'), handlers.get('rename_guild', lambda: None))
    builder.add_action(t('guild.menu.set_level'), handlers.get('set_guild_level', lambda: None))
    builder.add_action(t('button.import'), handlers.get('import_base', lambda: None))
    return builder.build()
def create_base_context_menu(parent, handlers):
    builder = ContextMenuBuilder(parent)
    builder.add_action(t('deletion.ctx.add_exclusion'), handlers.get('add_exclusion', lambda: None))
    builder.add_action(t('deletion.ctx.remove_exclusion'), handlers.get('remove_exclusion', lambda: None))
    builder.add_action(t('deletion.ctx.delete_base'), handlers.get('delete_base', lambda: None))
    builder.add_action(t('export.base'), handlers.get('export_base', lambda: None))
    builder.add_action(t('import.base'), handlers.get('import_base', lambda: None))
    builder.add_action(t('clone.base'), handlers.get('clone_base', lambda: None))
    return builder.build()
def create_guild_member_context_menu(parent, handlers):
    builder = ContextMenuBuilder(parent)
    builder.add_action(t('guild.ctx.make_leader'), handlers.get('make_leader', lambda: None))
    builder.add_action(t('guild.unlock_lab_research.menu'), handlers.get('unlock_lab_research', lambda: None))
    builder.add_separator()
    builder.add_action(t('deletion.ctx.add_exclusion'), handlers.get('add_exclusion', lambda: None))
    builder.add_action(t('deletion.ctx.remove_exclusion'), handlers.get('remove_exclusion', lambda: None))
    builder.add_action(t('deletion.ctx.delete_player'), handlers.get('delete_player', lambda: None))
    builder.add_action(t('player.rename.menu'), handlers.get('rename_player', lambda: None))
    builder.add_action(t('player.inventory.menu'), handlers.get('edit_inventory', lambda: None))
    return builder.build()