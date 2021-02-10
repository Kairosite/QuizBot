from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import sqlalchemy as db
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from operator import itemgetter

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
                self.players[player_entry.user_id] = (
                    player_entry.score, player_entry.captain_id, False
                )
            # Load Teams
            for team_entry in self.session.query(Team).filter(
                Team.channel_id == self.channel_id
            ).all():
                self.teams[team_entry.captain_id] = (
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
        for (user_id, (score, captain_id, modified)) in filter(
                lambda x: x[1][2], self.players):
            if self.session.query(Player).filter(
                        Player.user_id == user_id
                    ).one_or_none():
                self.session.query(Player).filter(
                    Player.user_id == user_id
                ).update(
                    {"score": score,
                     "captain_id": captain_id},
                    synchronize_session="evaluate"
                )
            else:
                self.session.merge(
                    Player(user_id, self.channel_id, score, captain_id)
                )
            self.players[user_id] = (score, captain_id, False)
        # Writeback Teams
        for (captain_id, (score, team_name, modified)) in filter(
                lambda x: x[1][2], self.teams):
            if self.session.query(Team).filter(
                        Team.captain_id == captain_id
                    ).one_or_none():
                self.session.query(Team).filter(
                    Team.captain_id == captain_id
                ).update(
                    {"score": score,
                     "team_name": team_name},
                    synchronize_session="evaluate"
                )
            else:
                self.session.merge(
                    Team(captain_id, self.channel_id, score, team_name)
                )
            self.playteamsers[captain_id] = (score, team_name, False)
        self.modified = False

    def get_scores(self):
        teams = {}
        # Get teams
        for (captain_id, (score, n, m)) in self.teams.items():
            teams[captain_id] = (score, [])
        # Add players
        for (player_id, (score, captain_id)) in self.players.items():
            if captain_id:
                teams[captain_id][1].append((player_id, score))
            else:
                teams[player_id] = (score, [(player_id, score)])
        # Sort scores
        teams = [(t, s, sorted(p, itemgetter(1), True))
                 for (t, (s, p)) in teams.items()]
        return sorted(teams, itemgetter(1), True)

    def __del__(self):
        self._writeback_(True)
