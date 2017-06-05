import sys
import math
import random

# Send your busters out into the fog to trap ghosts and bring them home!

busters_per_player = int(input())  # the amount of busters you control
ghost_count = int(input())  # the amount of ghosts on the map
my_team_id = int(input())  # if this is 0, your base is on the top left of the map, if it is one, on the bottom right

ghosts = {}
captured_ghosts = []
busters = [{},{}]


square_length = 1500
plateau = []
filtered_plateau = []

for j in range(math.ceil(9000/square_length)):
    plateau.append([0 for i in range(math.ceil(16000/square_length))])

def update_plateau():
    for buster in busters[my_team_id].values():
        x = int(buster.x / square_length)
        y = int(buster.y / square_length)
        plateau[y][x] = 1

    filtered_plateau.clear()
    for j in range(math.ceil(9000/square_length)):
        line = []
        filtered_plateau.append(line)
        for i in range(math.ceil(16000/square_length)):
            count = 0
            if plateau[j][i] == 0:
                for dj, di in [(-1,0),(1,0),(0,-1),(0,1)]:
                    if 0 <= j+dj < len(plateau) and 0 <= i+di < len(plateau[0]):
                        if plateau[j+dj][i+di] == 0:
                            count += 1
                for dj, di in [(-1,-1),(1,1),(-1,1),(1,-1)]:
                    if 0 <= j+dj < len(plateau) and 0 <= i+di < len(plateau[0]):
                        if plateau[j+dj][i+di] == 0:
                            count += 0
            line.append(count)


def dist(v1, v2):
    dx = v1.x-v2.x
    dy = v1.y-v2.y
    return math.sqrt(dx*dx+dy*dy)

class Action:
    def __init__(self, action):
        self.action = action

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return str(self.action)

class Move(Action):
    def __init__(self, x, y):
        Action.__init__(self, "MOVE")
        self.x = x
        self.y = y

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return Action.__repr__(self) + " " + str(self.x) + " " + str(self.y)

class Bust(Action):
    def __init__(self, gid):
        Action.__init__(self, "BUST")
        self.gid = gid

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return Action.__repr__(self) + " " + str(self.gid)

class Release(Action):
    def __init__(self):
        Action.__init__(self, "RELEASE")

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return Action.__repr__(self)

class Stun(Action):
    def __init__(self, eid):
        Action.__init__(self, "STUN")
        self.eid = eid

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return Action.__repr__(self) + " " + str(self.eid)
    
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Entity(Vector):
    def __init__(self, eid, x, y):
        Vector.__init__(self, x, y)
        self.eid = eid
        self.ia = IA(self)
        self.out_of_date = False
        
    def update(self, x, y):
        self.x = x
        self.y = y
        self.out_of_date = False
        
    def get_action(self):
        self.out_of_date = True
        return(self.ia.get_action())

class Ghost(Entity):
    def __init__(self, eid, x, y, nb_traps, state):
        Entity.__init__(self, eid, x, y)
        self.nb_traps = nb_traps
        self.life = state
        self.ia = Fuyard(self)
        ghosts[self.eid] = self
        
    def update(self, x, y, nb_traps):
        Entity.update(self, x, y)
        self.nb_traps = nb_traps
        self.life = self.life - self.nb_traps

class Buster(Entity):
    def __init__(self, eid, x, y, team, state, gid):
        Entity.__init__(self, eid, x, y)
        self.team = team
        self.carry = state == 1
        self.stuned = state == 2
        self.stuned_turns = 0
        self.gid = gid
        self.stun = 0
        self.bust = state == 3
        self.busting_gid = None
        busters[self.team][self.eid] = self
        
    def update(self, x, y, state, value):
        Entity.update(self, x, y)
        self.carry = state == 1
        self.stuned = state == 2
        self.bust = state == 3
        if not self.bust:
            self.busting_gid = None
        if self.stuned:
            self.stuned_turns = value
            self.gid = None
        else:
            self.stuned_turns = 0
            self.gid = value
        if self.stun > 0:
            self.stun = self.stun - 1

homes = [Vector(0,0),Vector(16000,9000)]


class IA:
    def __init__(self, entity, default_ia=None):
        self.entity = entity
        if default_ia == None:
            default_ia = self
        self.default_ia = default_ia

    def get_action(self):
        return Move(8000, 4500)

class Explorateur(IA):
    def __init__(self, entity, default_ia=None):
        IA.__init__(self, entity, default_ia)
        self.x = entity.x
        self.y = entity.y

    def get_action(self):
        if self.entity.x == self.x and self.entity.y == self.y:
            self.x, self.y = self.choose_next_pos()
        return Move(self.x, self.y)

    def choose_next_pos(self):
        max_score = None
        max_x = random.randint(500,15500)
        max_y = random.randint(500,8500)
        for j in range(math.ceil(9000/square_length)):
            for i in range(math.ceil(16000/square_length)):
                if filtered_plateau[j][i] > 0:
                    v = Vector(min(15500,i*square_length+(square_length/2)),min(8500,j*square_length+(square_length/2)))
                    cout = 2100*filtered_plateau[j][i]-dist(v,self.entity)
                    if max_score == None or max_score < cout:
                        max_score = cout
                        max_x = v.x
                        max_y = v.y
        return (int(max_x),int(max_y))


class Agressif(IA):
    def get_action(self):
        if self.entity.stun == 0:
            for eid, buster in busters[not self.entity.team].items():
                if not buster.out_of_date:
                    if dist(self.entity, buster) < 1760 and not self.entity.carry:
                        self.entity.stun = 20
                        return Stun(eid)
        return self.default_ia.get_action()


class Fuyard(IA):
    def get_action(self):
        return Move(self.entity.x, self.entity.y)

class Captureur(Explorateur):
    def get_action(self):
        if self.entity.carry:
            home = homes[self.entity.team]
            if dist(self.entity, home) < 1600:
                del ghosts[self.entity.gid]
                return Release()
            else:
                return Move(home.x, home.y)
        if len(ghosts) == 0:
            return self.default_ia.get_action()
        min_dist = 16000*9000
        min_ghost = 0
        can_be_bust = []
        for gid, ghost in ghosts.items():
            if gid not in captured_ghosts and not ghost.out_of_date:
                d = dist(self.entity, ghost)
                if 900 < d < 1760:
                    can_be_bust.append(ghost)
                elif d >= 1760:
                    if min_dist > d:
                        min_dist = d
                        min_ghost = ghost
        if can_be_bust != []:
            if self.entity.busting_gid and ghosts[self.entity.busting_gid] in can_be_bust:
                return Bust(self.entity.busting_gid)
            else:
                can_be_bust = sorted(can_be_bust, key=lambda ghost: ghost.life)
                self.entity.busting_gid = can_be_bust[0].eid
                return Bust(can_be_bust[0].eid)
        self.entity.busting_gid = None
        if min_ghost == 0:
            return self.default_ia.get_action()
        return Move(min_ghost.x, min_ghost.y)

compos = {
    2:["ACE","ACE"],
    3:["ACE","ACE","ACE"],
    4:["ACE","ACE","ACE","ACE"],
    5:["ACE","ACE","ACE","ACE","ACE"]
}

def set_ia(buster):
    compo = compos[busters_per_player]
    num = len(busters[my_team_id])-1
    comportements = compo[num]
    ia = None
    for role in reversed(comportements):
        if role == "A":
            ia = Agressif(buster, ia)
        elif role == "C":
            ia = Captureur(buster, ia)
        elif role == "E":
            ia = Explorateur(buster, ia)
        elif role == "F":
            ia = Fuyard(buster, ia)

    ia.__name__ = comportements
    buster.ia = ia

def update_entity(eid, x, y, entity_type, state, value):
    if entity_type == -1:
        if eid in ghosts:
            ghosts[eid].update(x, y, value)
        else:
            Ghost(eid, x, y, value, state)
    else:
        if eid in busters[entity_type]:
            busters[entity_type][eid].update(x, y, state, value)
        else:
            buster = Buster(eid, x, y, entity_type, state, value)
            if entity_type == my_team_id:
                set_ia(buster)

# game loop
while True:
    entities = int(input())  # the number of busters and ghosts visible to you
    for i in range(entities):
        # entity_id: buster id or ghost id
        # y: position of this buster / ghost
        # entity_type: the team id if it is a buster, -1 if it is a ghost.
        # state: For busters: 0=idle, 1=carrying a ghost.
        # value: For busters: Ghost id being carried. For ghosts: number of busters attempting to trap this ghost.
        entity_id, x, y, entity_type, state, value = [int(j) for j in input().split()]
        update_entity(entity_id, x, y, entity_type, state, value)

    update_plateau()

    captured_ghosts = [ghost for ghost in ghosts.values() if ghost.life <= 0]

    for eid in sorted(busters[my_team_id].keys()):
        buster = busters[my_team_id][eid]
        print(str(buster.get_action()) + " " + buster.ia.__name__)

    for eid in sorted(busters[not my_team_id].keys()):
        buster = busters[not my_team_id][eid]
        buster.get_action()

    for gid in sorted(ghosts.keys()):
        ghost = ghosts[gid]
        ghost.get_action()

        # Write an action using print
        # To debug: print("Debug messages...", file=sys.stderr)

        # MOVE x y | BUST id | RELEASE
