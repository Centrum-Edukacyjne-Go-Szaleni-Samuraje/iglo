from django.core.management import BaseCommand, CommandParser, CommandError

from accounts.models import UserRole, User


class Command(BaseCommand):
    help = 'Manage user roles'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('action', choices=['grant', 'refuse'])
        parser.add_argument('user_email', type=str, help='User email')
        parser.add_argument('role', type=str, help='Role')

    def handle(self, *args, **options):
        action = options['action']
        email = options['user_email']
        role_str = options['role']
        try:
            role = UserRole.from_str(role_str)
        except KeyError:
            raise CommandError(f'Role: {role_str} does not exist')
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email: {email} does not exist')
        if action == 'grant':
            user.grant_role(role)
            print(f'[{role.label}] granted to [{user}]')
        elif action == 'refuse':
            user.refuse_role(role)
            print(f'[{role.label}] refused to [{user}]')

        user = User.objects.get(email__iexact=email)
        print(f'[{user}] roles: {user.roles}')
