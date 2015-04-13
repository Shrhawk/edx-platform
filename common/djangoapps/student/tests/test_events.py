# -*- coding: utf-8 -*-
"""
Test that various events are fired for models in the student app.
"""
from django.test import TestCase

from django_countries.fields import Country

from student.models import PasswordHistory, USER_SETTINGS_CHANGED_EVENT_NAME
from student.tests.factories import UserFactory
from student.tests.tests import UserSettingsEventTestMixin


class TestUserProfileEvents(UserSettingsEventTestMixin, TestCase):
    """
    Test that we emit field change events when UserProfile models are changed.
    """
    def setUp(self):
        super(TestUserProfileEvents, self).setUp()
        self.table = 'auth_userprofile'
        self.user = UserFactory.create()
        self.profile = self.user.profile
        self.reset_tracker()

    def test_change_one_field(self):
        """
        Verify that we emit an event when a single field changes on the user
        profile.
        """
        self.profile.year_of_birth = 1900
        self.profile.save()
        self.assert_user_setting_event_emitted(setting='year_of_birth', old=None, new=self.profile.year_of_birth)

        # Verify that we remove the temporary `_changed_fields` property from
        # the model after we're done emitting events.
        with self.assertRaises(AttributeError):
            getattr(self.profile, '_changed_fields')

    def test_change_many_fields(self):
        """
        Verify that we emit one event per field when many fields change on the
        user profile in one transaction.
        """
        self.profile.gender = u'o'
        self.profile.bio = 'test bio'
        self.profile.save()
        self.assert_user_setting_event_emitted(setting='bio', old=None, new=self.profile.bio)
        self.assert_user_setting_event_emitted(setting='gender', old=u'm', new=u'o')

    def test_unicode(self):
        """
        Verify that the events we emit can handle unicode characters.
        """
        old_name = self.profile.name
        self.profile.name = u'Dånîél'
        self.profile.save()
        self.assert_user_setting_event_emitted(setting='name', old=old_name, new=self.profile.name)

    def test_country(self):
        """
        Verify that we properly serialize the JSON-unfriendly Country field.
        """
        self.profile.country = Country(u'AL', 'dummy_flag_url')
        self.profile.save()
        self.assert_user_setting_event_emitted(setting='country', old=None, new=self.profile.country)

    def test_excluded_field(self):
        """
        Verify that we don't emit events for ignored fields.
        """
        self.profile.meta = {u'foo': u'bar'}
        self.profile.save()
        self.assert_no_events_were_emitted()


class TestUserEvents(UserSettingsEventTestMixin, TestCase):
    """
    Test that we emit field change events when User models are changed.
    """
    def setUp(self):
        super(TestUserEvents, self).setUp()
        self.user = UserFactory.create()
        self.reset_tracker()
        self.table = 'auth_user'

    def test_change_one_field(self):
        """
        Verify that we emit an event when a single field changes on the user.
        """
        old_username = self.user.username
        self.user.username = u'new username'
        self.user.save()
        self.assert_user_setting_event_emitted(setting='username', old=old_username, new=self.user.username)

    def test_change_many_fields(self):
        """
        Verify that we emit one event per field when many fields change on the
        user in one transaction.
        """
        old_email = self.user.email
        old_is_staff = self.user.is_staff
        self.user.email = u'foo@bar.com'
        self.user.is_staff = True
        self.user.save()
        self.assert_user_setting_event_emitted(setting='email', old=old_email, new=self.user.email)
        self.assert_user_setting_event_emitted(setting='is_staff', old=old_is_staff, new=self.user.is_staff)

    def test_password(self):
        """
        Verify that password values are not included in the event payload.
        """
        self.user.password = u'new password'
        self.user.save()
        self.assert_user_setting_event_emitted(setting='password', old=None, new=None)

    def test_related_fields_ignored(self):
        """
        Verify that we don't emit events for related fields.
        """
        self.user.passwordhistory_set.add(PasswordHistory(password='new_password'))
        self.user.save()
        self.assert_no_events_were_emitted()
