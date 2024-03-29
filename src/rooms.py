from src.game import Game
from src.responses import ResponseEvent, build_response
from src.websockets import EnhancedWebscoket


class WebsocketRoom:
    clients = None
    name = None
    limit = 2
    game: Game = None

    def __init__(self, data):
        if isinstance(data, str):
            self.name = data
        if isinstance(data, dict):
            self.name = data.get('create_room')
        self.clients = set()

    def start_new_game(self):
        self.game = Game(self.clients)

    def add_client(self, client: EnhancedWebscoket):
        self.clients.add(client)

    def remove_client(self, client: EnhancedWebscoket):
        self.clients.remove(client)

    @property
    def is_full(self):
        return self.client_count >= self.limit

    @property
    def client_count(self):
        return len(self.clients)

    def __contains__(self, item):
        return item in self.clients

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return hash(self) != hash(other)

    def __str__(self):
        return f'<WebSocketRoom {self.name}>'


class WebsocketRoomManager:
    rooms = dict()

    def get_room(self, name: str) -> WebsocketRoom:
        return self.rooms.get(name, None)

    def create_room(self, room: WebsocketRoom) -> None:
        self.rooms[room.name] = room

    async def join_room(self, name, client: EnhancedWebscoket) -> WebsocketRoom:
        if self.room_exists(name) and not self.client_in_room(name, client):
            room = self.rooms.get(name)
            room.clients.add(client)
            return room
        else:
            await client.send_json({
                'message': f"Room {name} does not exist or you are already in it"
            })
            return

    def remove_room(self, room: WebsocketRoom) -> None:
        del self.rooms[room.name]

    def room_exists(self, name: str) -> bool:
        return bool(self.get_room(name))

    def client_in_room(self, name: str, client: EnhancedWebscoket):
        try:
            return client in self.rooms.get(name).clients
        except:
            return False

    def remove_client_from_all_rooms(self, client: EnhancedWebscoket) -> None:
        for room in self.rooms.values():
            if client in room.clients:
                room.remove_client(client)

    def __contains__(self, item):
        if isinstance(item, WebsocketRoom):
            return item.name in self.rooms
        return item in self.rooms

    @property
    def all_rooms(self) -> dict:
        return build_response(
            event_type=ResponseEvent.GET_ALL_ROOMS,
            data={'rooms': [{
                'name': x.name,
                'current_clients': x.client_count,
                'limit': x.limit,
                'is_full': x.is_full
            } for x in self.rooms.values()]}
        )


room_manager = WebsocketRoomManager()
