import datetime
import string

import factory
from django.db.models.signals import post_save

from accounts.factories import UserFactory
from league.models import Member, Player, Group, Season, Game, Round


class PlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Player
    user = factory.SubFactory(UserFactory)
    nick = factory.Sequence(lambda n: f"player-{n}")
    rank = 1000
    igor_history = []


class SeasonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Season

    number = factory.Sequence(lambda n: n)
    start_date = factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=7))
    end_date = factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=7 * 6))
    promotion_count = 1
    players_per_group = 3


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: string.ascii_uppercase[n % len(string.ascii_uppercase)])
    season = factory.SubFactory(SeasonFactory)


class MemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Member

    player = factory.SubFactory(PlayerFactory)
    order = factory.Sequence(lambda n: n)
    group = factory.SubFactory(GroupFactory)


class RoundFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Round

    group = factory.SubFactory(GroupFactory)
    number = factory.Sequence(lambda n: n)


@factory.django.mute_signals(post_save)
class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Game

    round = factory.LazyAttribute(lambda g: RoundFactory(group=g.group))
    group = factory.SubFactory(GroupFactory)
    black = factory.SubFactory(MemberFactory)
    white = factory.SubFactory(MemberFactory)
    sgf = factory.django.FileField(filename='file.sgf')
