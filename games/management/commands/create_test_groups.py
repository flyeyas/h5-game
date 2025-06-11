from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from games.models import Game, Category, Advertisement


class Command(BaseCommand):
    help = 'Create 20 test user groups with appropriate permissions for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing test groups (groups containing "Test" in their names)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview mode - show what would be created without actually creating data'
        )

    def handle(self, *args, **options):
        """Main handler function"""
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('Starting bulk creation of test user groups'))
        self.stdout.write('='*60)

        # Clear existing test groups if specified
        if options['clear']:
            self._clear_test_groups(options['dry_run'])

        # Create test user groups
        self._create_test_groups(options['dry_run'])

        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('User group creation task completed'))
        self.stdout.write('='*60)

    def _clear_test_groups(self, dry_run=False):
        """Clear existing test user groups"""
        self.stdout.write('\n' + '-'*40)
        self.stdout.write('Clearing existing test user groups...')
        self.stdout.write('-'*40)

        # Find groups containing "Test" in their names
        test_groups = Group.objects.filter(name__icontains='Test')

        if not test_groups.exists():
            self.stdout.write(self.style.WARNING('No test user groups found to clear'))
            return

        self.stdout.write(f'Found {test_groups.count()} test user groups:')
        for group in test_groups:
            self.stdout.write(f'  - {group.name}')

        if not dry_run:
            with transaction.atomic():
                deleted_count = test_groups.delete()[0]
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted {deleted_count} test user groups')
                )
        else:
            self.stdout.write(
                self.style.WARNING('Preview mode: Would delete the above user groups')
            )

    def _create_test_groups(self, dry_run=False):
        """Create test user groups"""
        self.stdout.write('\n' + '-'*40)
        self.stdout.write('Creating test user groups...')
        self.stdout.write('-'*40)

        # Define 20 test user group configurations
        group_configs = self._get_group_configurations()

        created_groups = []
        skipped_groups = []

        if not dry_run:
            with transaction.atomic():
                for config in group_configs:
                    result = self._create_single_group(config)
                    if result['created']:
                        created_groups.append(result['group_name'])
                    else:
                        skipped_groups.append(result['group_name'])
        else:
            # Preview mode
            self.stdout.write(self.style.WARNING('Preview mode: Will create the following user groups:'))
            for config in group_configs:
                self.stdout.write(f'  - {config["name"]}')
                self.stdout.write(f'    Description: {config["description"]}')
                self.stdout.write(f'    Permissions count: {len(config["permissions"])}')
                self.stdout.write('')

        # Output result summary
        if not dry_run:
            self._print_creation_summary(created_groups, skipped_groups)

    def _get_group_configurations(self):
        """Get user group configuration list"""
        # Get permission objects for assignment
        permissions = self._get_permissions()

        return [
            {
                'name': 'Super Admin Test Group',
                'description': 'Super administrator group with all permissions',
                'permissions': permissions['all']
            },
            {
                'name': 'Game Admin Test Group',
                'description': 'Administrator group responsible for game content management',
                'permissions': permissions['game_admin']
            },
            {
                'name': 'Category Admin Test Group',
                'description': 'Administrator group responsible for game category management',
                'permissions': permissions['category_admin']
            },
            {
                'name': 'Advertisement Admin Test Group',
                'description': 'Administrator group responsible for advertisement management',
                'permissions': permissions['ad_admin']
            },
            {
                'name': 'Content Editor Test Group',
                'description': 'Editor group responsible for content editing',
                'permissions': permissions['content_editor']
            },
            {
                'name': 'Game Developer Test Group',
                'description': 'Game development personnel group',
                'permissions': permissions['game_developer']
            },
            {
                'name': 'Data Analyst Test Group',
                'description': 'Data analyst group responsible for data analysis',
                'permissions': permissions['data_analyst']
            },
            {
                'name': 'Customer Service Test Group',
                'description': 'Customer service personnel group',
                'permissions': permissions['customer_service']
            },
            {
                'name': 'QA Tester Test Group',
                'description': 'Software testing personnel group',
                'permissions': permissions['tester']
            },
            {
                'name': 'Operations Test Group',
                'description': 'Website operations personnel group',
                'permissions': permissions['operator']
            },
            {
                'name': 'Content Moderator Test Group',
                'description': 'Content moderation personnel group',
                'permissions': permissions['moderator']
            },
            {
                'name': 'Finance Team Test Group',
                'description': 'Financial management personnel group',
                'permissions': permissions['finance']
            },
            {
                'name': 'Technical Support Test Group',
                'description': 'Technical support personnel group',
                'permissions': permissions['tech_support']
            },
            {
                'name': 'Marketing Team Test Group',
                'description': 'Marketing personnel group',
                'permissions': permissions['marketing']
            },
            {
                'name': 'Product Manager Test Group',
                'description': 'Product management personnel group',
                'permissions': permissions['product_manager']
            },
            {
                'name': 'UI/UX Designer Test Group',
                'description': 'UI/UX designer group',
                'permissions': permissions['designer']
            },
            {
                'name': 'Intern Test Group',
                'description': 'Intern user group',
                'permissions': permissions['intern']
            },
            {
                'name': 'External Partner Test Group',
                'description': 'External partner group',
                'permissions': permissions['partner']
            },
            {
                'name': 'Guest Access Test Group',
                'description': 'Temporary guest access group',
                'permissions': permissions['guest']
            },
            {
                'name': 'System Monitor Test Group',
                'description': 'System monitoring personnel group',
                'permissions': permissions['monitor']
            }
        ]

    def _get_permissions(self):
        """Get various permission combinations"""
        # Get all permissions
        all_permissions = list(Permission.objects.all())

        # Get games app related permissions
        games_ct = ContentType.objects.get_for_model(Game)
        category_ct = ContentType.objects.get_for_model(Category)
        ad_ct = ContentType.objects.get_for_model(Advertisement)

        game_permissions = list(Permission.objects.filter(content_type=games_ct))
        category_permissions = list(Permission.objects.filter(content_type=category_ct))
        ad_permissions = list(Permission.objects.filter(content_type=ad_ct))

        # Get user and group management permissions
        from django.contrib.auth.models import User
        user_ct = ContentType.objects.get_for_model(User)
        group_ct = ContentType.objects.get_for_model(Group)

        user_permissions = list(Permission.objects.filter(content_type=user_ct))
        group_permissions = list(Permission.objects.filter(content_type=group_ct))

        # Get basic view permissions
        view_permissions = list(Permission.objects.filter(codename__startswith='view_'))

        return {
            'all': all_permissions,
            'game_admin': game_permissions + category_permissions,
            'category_admin': category_permissions,
            'ad_admin': ad_permissions,
            'content_editor': game_permissions + category_permissions,
            'game_developer': game_permissions,
            'data_analyst': view_permissions,
            'customer_service': view_permissions,
            'tester': view_permissions,
            'operator': game_permissions + ad_permissions,
            'moderator': game_permissions + category_permissions,
            'finance': ad_permissions,
            'tech_support': view_permissions,
            'marketing': ad_permissions + view_permissions,
            'product_manager': game_permissions + category_permissions + view_permissions,
            'designer': view_permissions,
            'intern': view_permissions[:5],  # Limit permission count
            'partner': view_permissions,
            'guest': view_permissions[:3],   # Minimum permissions
            'monitor': view_permissions
        }

    def _create_single_group(self, config):
        """Create a single user group"""
        group_name = config['name']

        # Check if user group already exists
        if Group.objects.filter(name=group_name).exists():
            self.stdout.write(
                self.style.WARNING(f'User group "{group_name}" already exists, skipping creation')
            )
            return {'created': False, 'group_name': group_name}

        try:
            # Create user group
            group = Group.objects.create(name=group_name)

            # Assign permissions
            if config['permissions']:
                group.permissions.set(config['permissions'])

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created user group: {group_name} (Permissions count: {len(config["permissions"])})'
                )
            )

            return {'created': True, 'group_name': group_name}

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create user group "{group_name}": {str(e)}')
            )
            return {'created': False, 'group_name': group_name}

    def _print_creation_summary(self, created_groups, skipped_groups):
        """Print creation result summary"""
        self.stdout.write('\n' + '-'*40)
        self.stdout.write('Creation Result Summary:')
        self.stdout.write('-'*40)

        self.stdout.write(f'Successfully created user groups: {len(created_groups)}')
        self.stdout.write(f'Skipped user groups: {len(skipped_groups)}')

        if created_groups:
            self.stdout.write('\nSuccessfully created user groups:')
            for i, group_name in enumerate(created_groups, 1):
                self.stdout.write(f'  {i:2d}. {group_name}')

        if skipped_groups:
            self.stdout.write('\nSkipped user groups:')
            for i, group_name in enumerate(skipped_groups, 1):
                self.stdout.write(f'  {i:2d}. {group_name}')

        # Verify data
        self._verify_created_groups()

    def _verify_created_groups(self):
        """Verify created user group data"""
        self.stdout.write('\n' + '-'*40)
        self.stdout.write('Data Verification:')
        self.stdout.write('-'*40)

        # Count test user groups
        test_groups = Group.objects.filter(name__icontains='Test')
        self.stdout.write(f'Total test user groups in database: {test_groups.count()}')

        # Check permission assignments
        groups_with_permissions = 0
        total_permissions = 0

        for group in test_groups:
            permission_count = group.permissions.count()
            if permission_count > 0:
                groups_with_permissions += 1
                total_permissions += permission_count

        self.stdout.write(f'User groups with permissions: {groups_with_permissions}')
        self.stdout.write(f'Total permission assignments: {total_permissions}')

        if groups_with_permissions > 0:
            avg_permissions = total_permissions / groups_with_permissions
            self.stdout.write(f'Average permissions per group: {avg_permissions:.1f}')

        self.stdout.write('\nVerification completed! You can view the results at:')
        self.stdout.write('http://127.0.0.1:8000/en/admin/auth/group/')
        self.stdout.write('http://127.0.0.1:8000/admin/auth/group/')  # Alternative URL
