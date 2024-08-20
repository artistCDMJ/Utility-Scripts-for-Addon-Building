import bpy

def search_keymap_item(identifier, keymap_name):
    keyconfig = bpy.context.window_manager.keyconfigs.addon
    keymap = keyconfig.keymaps.get(keymap_name)

    if keymap is None:
        print(f"Keymap '{keymap_name}' not found.")
        return

    for keymap_item in keymap.keymap_items:
        if keymap_item.idname == identifier:
            print(f"Keymap: {keymap.name}")
            print(f"  Keymap Item: {keymap_item.idname}, Key: {keymap_item.type}, Action: {keymap_item.value}")
            return keymap_item

    print(f"Identifier '{identifier}' not found in keymap '{keymap_name}'.")

# Example usage
identifier = "view3d.brush_popup"
keymap_name = "Image Paint"
search_keymap_item(identifier, keymap_name)
