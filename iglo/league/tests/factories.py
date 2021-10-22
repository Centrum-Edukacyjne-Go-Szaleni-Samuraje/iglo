import datetime
import string

import factory

from league.models import Member, Player, Group, Season, Game, Round


class PlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Player

    nick = factory.Sequence(lambda n: f"player-{n}")
    rank = "9d"


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

    name = factory.Sequence(lambda n: string.ascii_uppercase[n])
    season = factory.SubFactory(SeasonFactory)


class MemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Member

    player = factory.SubFactory(PlayerFactory)
    order = factory.Sequence(lambda n: n)


class RoundFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Round

    group = factory.SubFactory(GroupFactory)
    number = factory.Sequence(lambda n: n)


class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Game

    round = factory.LazyAttribute(lambda g: RoundFactory(group=g.group))
    group = factory.SubFactory(GroupFactory)
    black = factory.SubFactory(MemberFactory)
    white = factory.SubFactory(MemberFactory)
