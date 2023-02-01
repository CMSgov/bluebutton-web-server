from waffle.models import AbstractUserFlag


class Flag(AbstractUserFlag):
    """ Custom version of waffle feature Flag model """
    """ This makes future extensions nicer """

    def is_active_for_user(self, user):
        # use app_user which is the owner of the current app
        if self.everyone:
            return True
        elif self.id is None:
            return False
        else:
            # checks if user is in flag.users
            return super(Flag, self).is_active_for_user(user) is not None
