from steam_workshop import Collection
from os import path
import json
from subprocess import call


def fetch(workshop_id, update=True):
    collection = Collection(workshop_id).to_dict()
    with get_file(workshop_id, "r") as file:
        old_collection = json.load(file)

    removed = compare(old_collection, collection)
    added = compare(collection, old_collection)

    if update and (added or removed):
        update_json(workshop_id, collection)
        generate_message(added, removed)
        update_git()

    return {
        "added": added,
        "removed": removed
    }


def update_json(workshop_id, collection):
    with get_file(workshop_id, "w") as file:
        json.dump(collection, file, indent=2)


def compare(a, b):
    removed = {}
    # Check for removed items
    for key in a["items"].keys():
        if key not in b["items"].keys():
            removed[key] = a["items"][key]
    # Check for removed collections
    for key in a["collections"].keys():
        if key not in b["collections"].keys():
            removed[key] = a["collections"][key]

    return removed


def generate_message(added, removed):
    add_message = change_list(added, "Added")
    remove_message = change_list(removed, "Removed")

    # Format message
    message = f"{add_message} {remove_message}".replace("\n", "").replace("\r", "").strip()

    description = ""
    if len(message) > 72:
        description = message
        changes = []
        if added:
            count = len(added)
            changes.append(f"{count} {pluralise('addition', count)}")
        if removed:
            count = len(removed)
            changes.append(f"{len(removed)} {pluralise('removal', count)}")
        message = " and ".join(changes) + "."

    with open("./tracker/message.txt", "w") as file:
        file.write("\n".join([message, description]))


def pluralise(word, count):
    if count != 1:
        return word + "s"
    else:
        return word


def change_list(dictionary, prepend):
    message = ""
    if dictionary:
        message = prepend + " "
        for key in dictionary.keys():
            title = dictionary[key]["title"].replace("\"", "'")  # Inner/outer quote consistency
            message += f"\"{title}\", "
        message = f"{message[:-2]}."
    return message


def get_file(workshop_id, mode="r"):
    file = f"./tracker/{workshop_id}.json"
    if path.exists(file):
        return open(file, mode)
    else:
        with open(file, "w") as fp:
            json.dump({"items": {}, "collections": {}}, fp, indent=2)
    return open(file, mode)


def update_git():
    call("bash update_git.sh")
