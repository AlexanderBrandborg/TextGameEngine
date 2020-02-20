import json
import os

class Notifyer():
    def __init__(self):
        self.subscribers = []

    def add_subscriber(self, subscriber):
        self.subscribers.append(subscriber)

    def notify(self, triggerId):
        for sub in self.subscribers:
            sub.notify(triggerId)

global_characters = []
global_items = []
global_notifyer = Notifyer()


class State():
    def __init__(self, id, desc, entry_condition, reactive_items):
        self.id = id
        self.desc = desc
        self.neighbours = []
        self.entry_condition = entry_condition
        self.reactive_items = reactive_items

    def add_neighbour(self, neighbour):
        self.neighbours.append(neighbour)


class StateMachine():
    def __init__(self, state_dto):
        self.states = [State(s["id"], "\n".join(s["lines"]), s["entry_condition"], s["reactive_items"]) for s in state_dto]
        for dto, state in zip(state_dto, self.states):
            for n in dto["neighbours"]:
                state.add_neighbour(next(x for x in self.states if x.id == n))

        self.current_state = self.states[0]
        global_notifyer.add_subscriber(self)

    def get_desc(self):
        return self.current_state.desc

    def trigger(self, item_id):
        trigger_id = self.current_state.reactive_items[str(item_id)]
        global_notifyer.notify(trigger_id)

    def notify(self, trigger_id):
        new_state = next(x for x in self.current_state.neighbours if x.entry_condition == trigger_id)
        if new_state:
            self.current_state = new_state


class Item():
    def __init__(self, id, item_name, desc):
        self.id = id
        self.name = item_name
        self.desc = desc


class Portal():
    def __init__(self, name, room_id, trigger_id, open):
        self.name = name
        self.room_id = room_id
        self.trigger_id = trigger_id
        self.open = open
        global_notifyer.add_subscriber(self)

    def notify(self, trigger_id):
        if trigger_id == self.trigger_id:
            self.open = True


class Character():
    def __init__(self, id, name, desc, states):
        self.id = id
        self.name = name
        self.desc = desc
        self.state_machine = StateMachine(states)

    def look(self):
        return self.desc

    def talk(self):
        return self.state_machine.get_desc()

    def use(self, player, item_name):
        item_id = next((x.id for x in global_items if x.name == item_name and x.id in player.inventory), None)
        if item_id != None:
            self.state_machine.trigger(item_id)



class Room():
    def __init__(self, id, entryText, desc, neighbours, items_ids, characters_ids):
        self.id = id
        self.entryText = entryText
        self.desc = desc
        self.neighbours = [Portal(x["name"], x["roomId"], x["triggerId"], x["open"]) for x in neighbours]
        self.items_ids = items_ids
        self.characters_ids = characters_ids

    def enter_room(self):
        return self.entryText

    def get_character(self, name):
        character = next((x for x in global_characters if x.name == name), None)
        if character and character.id in self.characters_ids:
            return character
        else:
            raise Exception("Character doesn't exists in this room")


    def take_item(self, item_name):
        item_id = next((x.id for x in global_items if x.name == item_name), None)
        if item_id in self.items_ids:
            self.items_ids.remove(item_id)
            return True
        else:
            print("You can't find a {} in this room".format(item_name))
            return False

    def enter(self, portal_name):
            portal = next(x for x in self.neighbours if x.name == portal_name)
            if portal.open:
                return portal.room_id

class Player():
    def __init__(self):
        self.inventory = []

    def add_to_inventory(self, item_name):
        item_id = next((x.id for x in global_items if x.name == item_name), None)
        if item_id != None:
            self.inventory.append(item_id)
            print("You have aquired a {}".format(item_name))

    def remove_from_inventory(self, item_name):
        item_id = next((x.id for x in global_items if x.name == item_name), None)
        if item_id:
            self.inventory.remove(item_id)

def main():
    with open("game.json") as layout_file:
        layout = json.load(layout_file)

    print(layout["title"])
    print("Press any key to start")
    input()

    rooms = []
    for roomDto in layout["rooms"]:
        r = Room(roomDto["id"],
                roomDto["entryText"],
                roomDto["description"],
                roomDto["neighbours"],
                roomDto["items"],
                roomDto["characters"])
        rooms.append(r)

    room = rooms[0]

    characters = []
    for c in layout["characters"]:
        character = Character(c["id"], c["name"], c["description"], c["states"])
        characters.append(character)
    global_characters.extend(characters)

    active_characters = [x for x in characters if x.id in room.characters_ids]

    entering = True
    player = Player()
    global_items.extend([Item(x["id"], x["name"], x["description"]) for x in layout["items"]])

    os.system('cls')
    while(True):
        if entering:
            entering = False
            print(room.enter_room())

        inpt = input()
        verbs = ["look",  "talk", "take", "use", "go"]
        comps = [x.lower() for x in inpt.split()]
        if comps[0] in verbs:
            if comps[0] == "look":
                if len(comps) == 1:
                    print(room.desc)
                elif len(comps) == 2:
                    char_name = comps[1]
                    char = next((x for x in active_characters if x.name == char_name), None)
                    if not char:
                        print("Character {} doesn't exist".format(char_name))
                    else:
                        print(char.look())

            elif comps[0] == "talk":
                char_name = comps[1]
                char = next((x for x in active_characters if x.name == char_name), None)
                if not char:
                    print("Character {} doesn't exist".format(char_name))
                else:
                    print(char.talk())

            elif comps[0] == "take":
                item_name = comps[1]
                if room.take_item(item_name):
                    player.add_to_inventory(item_name)

            elif comps[0] == "use":
                item_name = comps[1]
                target = comps[2]
                character = room.get_character(target)
                character.use(player, item_name)

            elif comps[0] == "go":
                portal_name = comps[1]
                room_id = room.enter(portal_name)
                if room_id != None:
                    r = next(x for x in rooms if x.id == room_id)
                    if r:
                        room = r
                        entering = True

            else:
                print("I don't understand")



        else:
            print("I don't understand")


if __name__ == "__main__":
    main()