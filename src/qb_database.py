from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import sqlalchemy as db
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from operator import attrgetter
from collections import namedtuple

engine = db.create_engine("sqlite:////__env__/qb_database.db")
Base = declarative_base(engine)


def db_session():
    return sessionmaker(bind=engine, autoflush=True)()


def init_db():
    Base.metadata.create_all()


class Server(Base):
    __tablename__ = "servers"
    server_id = db.Column(db.Integer, primary_key=True)
    gm_role = db.Column(db.Integer, nullable=True)

    def __init__(self, server_id):
        self.server_id = server_id


class Game(Base):
    __tablename__ = "games"
    channel_id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("servers.server_id"),
                          nullable=True)
    owner_id = db.Column(db.Integer)
    game_name = db.Column(db.Unicode(256), nullable=True)
    last_interaction = db.Column(db.DateTime, onupdate=func.now())

    def __init__(self, channel_id, server_id, owner_id, game_name=None):
        self.channel_id = channel_id
        self.server_id = server_id
        self.owner_id = owner_id
        self.game_name = game_name


class Player(Base):
    __tablename__ = "players"
    user_id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey("games.channel_id"),
                           primary_key=True)
    score = db.Column(db.Integer)
    captain_id = db.Column(db.Integer, db.ForeignKey("teams.captain_id"),
                           nullable=True)

    def __init__(self, user_id, channel_id, score=0, captain_id=None):
        self.user_id = user_id
        self.channel_id = channel_id
        self.score = score
        self.captain_id = captain_id


class Team(Base):
    __tablename__ = "teams"
    captain_id = db.Column(db.Integer, db.ForeignKey("games.user_id"),
                           primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey("games.channel_id"),
                           primary_key=True)
    score = db.Column(db.Integer)
    team_name = db.Column(db.Unicode(256), nullable=True)

    def __init__(self, captain_id, channel_id, score=0, team_name=None):
        self.captain_id = captain_id
        self.channel_id = channel_id
        self.score = score
        self.team_name = team_name


class QuizBotDatabaseException(Exception):

    def __init__(self, message, payload):
        self.message = message
        self.payload = payload


PlayerEntry = namedtuple("PlayerEntry", ["score", "captain_id", "modified"])
TeamEntry = namedtuple("TeamEntry", ["score", "team_name", "modified"])
TeamScore = namedtuple("TeamScore", ["score", "breakdown"])
PlayerScore = namedtuple("PlayerScore", ["player_id", "name"])


class CachedGame():
    players = dict()
    teams = dict()

    def __init__(self, channel_id):
        self.session = db_session()
        # Load game if available
        if game_entry := self.session.query(Game).filter(
                    Game.channel_id == channel_id
                ).one_or_none():
            self.channel_id = game_entry.channel_id
            self.server_id = game_entry.server_id
            self.owner_id = game_entry.owner_id
            self.game_name = game_entry.game_name
            # Load Players
            for player_entry in self.session.query(Player).filter(
                Player.channel_id == self.channel_id
            ).all():
                self.players[player_entry.user_id] = PlayerEntry(
                    player_entry.score, player_entry.captain_id, False
                )
            # Load Teams
            for team_entry in self.session.query(Team).filter(
                Team.channel_id == self.channel_id
            ).all():
                self.teams[team_entry.captain_id] = TeamEntry(
                    team_entry.score, team_entry.team_name, False
                )
            # Get GM role
            if server_entry := self.session.query(Server).filter(
                        Server.server_id == self.server_id
                    ).one_or_none():
                self.gm_role = server_entry.gm_role
            else:
                raise QuizBotDatabaseException(
                    "server not found for given server_id",
                    self.server_id
                )

        else:
            raise QuizBotDatabaseException(
                "game not found for given channel_id",
                channel_id
            )

        self.modified = False
        self.game_state_modified = False

    def _writeback_(self, force_writeback=False):
        if not self.modified and not force_writeback:
            return
        # Writeback Game State
        if self.game_state_modified or force_writeback:
            if self.session.query(Game).filter(
                        Game.channel_id == self.channel_id
                    ).one_or_none():
                self.session.query(Game).filter(
                    Game.channel_id == self.channel_id
                ).update(
                    {"owner_id": self.owner_id,
                     "game_name": self.game_name},
                    synchronize_session="evaluate"
                )
            else:
                raise QuizBotDatabaseException(
                    "game not found for given channel_id",
                    self.channel_id
                )
            self.game_state_modified = False
        # Writeback Players
        for (user_id, player_entry) in self.players.items():
            if player_entry.modified:
                if self.session.query(Player).filter(
                            Player.user_id == user_id,
                            Player.channel_id == self.channel_id
                        ).one_or_none():
                    self.session.query(Player).filter(
                        Player.user_id == user_id
                    ).update(
                        {"score": player_entry.score,
                         "captain_id": player_entry.captain_id},
                        synchronize_session="evaluate"
                    )
                else:
                    self.session.merge(
                        Player(
                            user_id,
                            self.channel_id,
                            player_entry.score,
                            player_entry.captain_id
                        )
                    )
            self.players[user_id].modified = False
        # Delete Removed Players
        for player in self.players.query(Player.user_id).filter(
            Player.channel_id == self.channel_id
        ).all():
            if player.user_id not in self.players:
                self.session.query(Player).filter(
                    Player.user_id == player.user_id,
                    Player.channel_id == self.channel_id
                ).delete()
        # Writeback Teams
        for (captain_id, team_entry) in self.teams.item():
            if self.session.query(Team).filter(
                        Team.captain_id == captain_id,
                        Player.channel_id == self.channel_id
                    ).one_or_none():
                self.session.query(Team).filter(
                    Team.captain_id == captain_id
                ).update(
                    {"score": team_entry.score,
                     "team_name": team_entry.team_name},
                    synchronize_session="evaluate"
                )
            else:
                self.session.merge(
                    Team(
                        captain_id,
                        self.channel_id,
                        team_entry.score,
                        team_entry.team_name
                    )
                )
            self.playteamsers[captain_id].modified = False
        # Delete Removed Teams
        for team in self.players.query(Team.captain_id).filter(
            Team.channel_id == self.channel_id
        ).all():
            if team.captain_id not in self.teams:
                self.session.query(Team).filter(
                    Team.captain_id == team.captain_id,
                    Team.channel_id == self.channel_id
                ).delete()
        self.modified = False

    def get_score(self, player_id):
        if player_id in self.players:
            player_entry = self.players[player_id]
            if player_entry.captain_id:
                team_score = self.teams[player_entry.captain_id].score
            else:
                team_score = None
            return (player_entry.score, team_score)
        else:
            return None

    def set_score(self, player_id, score):
        if player_id in self.players:
            player_entry = self.players[player_id]
            if player_entry.captain_id:
                team_entry = self.teams[player_entry.captain_id]
                diff = score - player_entry.score
                team_entry.score += diff
                team_entry.modified = True
                team_score = team_entry.score
            else:
                team_score = None
            player_entry.score = score
            player_entry.modified = True
            return (player_entry.score, team_score)
        else:
            return None

    def get_player_score(self, player_id):
        if player_id in self.players:
            return self.players[player_id].score
        else:
            return None

    def set_player_score(self, player_id, score):
        if player_id in self.players:
            player_entry = self.players[player_id]
            player_entry.score = score
            player_entry.modified = True
            return player_entry.score
        else:
            return None

    def get_team_score(self, captain_id):
        if captain_id in self.teams:
            return self.teams[captain_id].score
        else:
            return None

    def set_team_score(self, captain_id, score):
        if captain_id in self.teams:
            team_entry = self.teams[captain_id]
            team_entry.score = score
            team_entry.modified = True
            return team_entry.score
        else:
            return None

    def add_score(self, player_id, score):
        self.set_score(player_id, self.get_score(player_id) + score)

    def add_player_score(self, player_id, score):
        self.set_player_score(
            player_id,
            self.get_player_score(player_id) + score
        )

    def add_team_score(self, captain_id, score):
        self.set_team_score(
            captain_id,
            self.get_team_score(captain_id) + score
        )

    def get_scores(self):
        teams = {}
        # Get teams
        for (captain_id, team_entry) in self.teams.items():
            teams[captain_id] = TeamScore(team_entry.score, [])
        # Add players
        for (player_id, (score, captain_id)) in self.players.items():
            if captain_id:
                teams[captain_id].breakdown.append(
                    PlayerScore(player_id, score)
                )
            else:
                teams[player_id] = TeamScore(
                    score,
                    [PlayerScore(player_id, score)]
                )
        # Sort scores
        teams = [(t, s, sorted(p, attrgetter("score"), True))
                 for (t, (s, p)) in teams.items()]
        return sorted(teams, attrgetter("score"), True)

    def add_player(self, player_id):
        if player_id not in self.players:
            self.players[player_id] = PlayerEntry(0, None, True)
            return player_id
        else:
            return None

    def del_player(self, player_id):
        if player_id in self.teams:
            self.del_team(player_id)
        try:
            del self.players[player_id]
            return player_id
        except KeyError:
            return None

    def get_player_team(self, player_id):
        if player_id in self.players:
            return self.players[player_id].captain_id
        else:
            return None

    def set_player_team(self, player_id, captain_id):
        if player_id in self.players and captain_id in self.teams:
            self.players[player_id].captain_id = captain_id
            return player_id
        else:
            return None

    def add_team(self, captain_id):
        if captain_id in self.players and captain_id not in self.teams:
            self.players[captain_id].captain_id = captain_id
            self.teams[captain_id] = TeamEntry(0, None, True)
        else:
            return None

    def del_team(self, captain_id):
        if captain_id in self.teams:
            del self.team[captain_id]
            for player in self.players:
                if player.captain_id == captain_id:
                    player.captain_id = None
            return captain_id
        else: 
            return None

    def get_team_name(self, captain_id):
        return self.teams[captain_id].team_name

    def set_team_name(self, captain_id, team_name):
        if len(team_name) <= 256:
            self.teams[captain_id].team_name = team_name
        else:
            raise ValueError('team_name too long')

    def get_captain_id(self, team_name):
        for captain_id, team_entry in self.teams.items():
            if team_entry.team_name == team_name:
                return captain_id
        return None

    def update_team_captain(self, old_captain_id, new_captain_id):
        if old_captain_id in self.teams \
                and new_captain_id not in self.teams \
                and new_captain_id in self.players \
                and self.players[new_captain_id].captain_id == old_captain_id:
            self.team[new_captain_id] = self.teams[old_captain_id]
            del self.team[old_captain_id]
            for player in self.players:
                if player.captain_id == old_captain_id:
                    player.captain_id = new_captain_id
            self.team[new_captain_id].modified = True
            return new_captain_id
        else:
            return None

    def get_owner_id(self):
        return self.owner_id

    def set_owner_id(self, owner_id):
        self.owner_id = owner_id

    def get_game_name(self):
        return self.game_name

    def set_game_name(self, game_name):
        if len(game_name) <= 256:
            self.game_name = game_name
        else:
            raise ValueError('game_name too long')

    def __del__(self):
        self._writeback_(True)
