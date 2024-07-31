from datetime import (
    datetime,
    timezone,
    timedelta
)
import re
import warnings

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import (
    UserPasswordDescriptor,
    PastPassword,
    PasswordHasher,
)


class PasswordComplexityValidator:
    '''
    BB2-62 POAM strengthen blue button developer account authentication
    - increase password complexity
    '''

    def __init__(
            self,
            min_length_digit=1,
            min_length_alpha=1,
            min_length_special=1,
            min_length_lower=1,
            min_length_upper=1,
            special_characters="[~!{}@#$%^&*_+\":;()'[]"
    ):
        self.min_length_digit = min_length_digit
        self.min_length_alpha = min_length_alpha
        self.min_length_special = min_length_special
        self.min_length_lower = min_length_lower
        self.min_length_upper = min_length_upper
        self.special_characters = special_characters

        settings.PASSWORD_RULES[2]['regex'] = self.special_characters

        self.actual_params = [
            self.min_length_digit,
            self.min_length_alpha,
            self.min_length_special,
            self.min_length_lower,
            self.min_length_upper,
        ]

        password_requirements = []

        for rule in zip(settings.PASSWORD_RULES, self.actual_params):
            if rule[1]:
                password_requirements.append(rule[0]['help'].format(rule[1]))

        self.help_txt = "Your password must contaion at least {}.".format(', '.join(password_requirements))

    def validate(self, password, user=None):
        validation_errors = []
        for tuple in zip(settings.PASSWORD_RULES, self.actual_params):
            rule = tuple[0]
            min_len_required = tuple[1]
            p = re.compile(rule['regex'])
            actual_cnt = len(p.findall(password))
            if actual_cnt < min_len_required:
                validation_errors.append(ValidationError(
                    rule['msg'].format(min_len_required),
                    params={'min_length': min_len_required},
                    code=rule['name'],
                ))

        if validation_errors:
            raise ValidationError(validation_errors)

    def get_help_text(self):
        return self.help_txt


class PasswordReuseAndMinAgeValidator:
    '''
    BB2-62 POAM strengthen blue button developer account authentication
    - enforce min password age and re-use interval
    '''

    def __init__(self,
                 password_min_age=60 * 60 * 24,
                 password_reuse_interval=60 * 60 * 24 * 120,
                 password_expire=0):

        msg1 = "Invalid OPTIONS, password_min_age < password_reuse_interval expected, " \
               "but having password_min_age({}) >= password_reuse_interval({})"
        msg2 = "Invalid OPTIONS, password_expire < password_reuse_interval expected, " \
               "but having password_expire({}) >= password_reuse_interval({})"
        msg3 = "Invalid OPTIONS, password_min_age < password_expire expected, " \
               "but having password_expire({}) >= password_reuse_interval({})"

        check_opt_err = []
        if 0 < password_reuse_interval < password_min_age:
            check_opt_err.append(msg1.format(password_min_age, password_reuse_interval))
        if 0 < password_reuse_interval < password_expire:
            check_opt_err.append(msg2.format(password_expire, password_reuse_interval))
        if 0 < password_expire < password_min_age:
            check_opt_err.append(msg3.format(password_min_age, password_expire))
        if len(check_opt_err) > 0:
            raise ValueError(check_opt_err)

        self.password_min_age = password_min_age
        self.password_reuse_interval = password_reuse_interval
        self.password_expire = password_expire

    def validate(self, password, user=None):
        if not user or getattr(user, 'pk', None) is None or isinstance(getattr(user, 'pk', None), property):
            warnings.warn('Validating on invalid user: {}'.format(user))
            return

        #
        #                                                 |<--min password age-->|
        #                     |<------------no reuse window--------------------->|
        #  ------p0-----p1----+---p2-----p3----------p4---------p5---------------+
        #                                                                        ^
        #                                                                   cur_time_utc
        #  given new password p:
        #  (1) p's hash colides with any px in 'no reuse window' => validation fails
        #  (2) p's hash does not colide with any px in 'no reuse window'
        #      or the window is empty => further check 'min password age'
        #  (3) there are px in 'no reuse window' => if there is no px in 'min password age'
        #      like p5 => validation pass
        #  (4) no px in 'no reuse window' (hence no px in 'min password age'
        #      since it's asserted that password_min_age < password_reuse_interval) => pass validation
        #
        cur_time_utc = datetime.now(timezone.utc)
        for userpassword_desc in UserPasswordDescriptor.objects.filter(user=user):
            password_hash = userpassword_desc.create_hash(password)
            passwds = None
            try:
                if self.password_reuse_interval > 0:
                    # only check invalid reuse (colide) within reuse_interval
                    reuse_datetime = cur_time_utc - timedelta(0, self.password_reuse_interval)
                    passwds = PastPassword.objects.filter(
                        Q(date_created__gt=reuse_datetime), userpassword_desc=userpassword_desc
                    ).order_by('-date_created')
                else:
                    # no reuse_interval, check all past passwords for colide
                    passwds = PastPassword.objects.filter(
                        userpassword_desc=userpassword_desc
                    ).order_by('-date_created')

                for p in passwds:
                    if p.password == password_hash:
                        # check invalid re-use (colide) within password reuse interval
                        raise ValidationError(
                            ("You can not use a password that is already"
                             " used in this application within password re-use interval [days hh:mm:ss]: {}.")
                            .format(str(timedelta(seconds=self.password_reuse_interval))),
                            code='password_used'
                        )
            except PastPassword.DoesNotExist:
                pass

            if self.password_min_age > 0 and passwds is not None and passwds.first() is not None:
                if (datetime.now(timezone.utc)
                        - passwds.first().date_created).total_seconds() <= self.password_min_age:
                    # change password too soon
                    raise ValidationError(
                        "You can not change password that does not satisfy minimum password age [days hh:mm:ss]: {}."
                        .format(str(timedelta(seconds=self.password_min_age))),
                        code='password_used'
                    )

    def password_changed(self, password, user=None):

        if not user or getattr(user, 'pk', None) is None or isinstance(getattr(user, 'pk', None), property):
            warnings.warn('Change password on invalid user: {}'.format(user))
            return

        iter_val = PasswordHasher().iterations
        userpassword_desc = UserPasswordDescriptor.objects.filter(
            user=user,
            iterations=iter_val
        ).first()

        if not userpassword_desc:
            userpassword_desc = UserPasswordDescriptor()
            userpassword_desc.user = user
            userpassword_desc.save()

        password_hash = userpassword_desc.create_hash(password)

        # We are looking hash password in the database
        tz_now = datetime.now(timezone.utc)
        try:
            # with the timestamp now() this look up will certainly not able to get an entry
            # this is expected for new entry and re-use password (same user + password hash)
            # note, re use of user + password hash will satisfy re use interval first.
            PastPassword.objects.get(
                userpassword_desc=userpassword_desc,
                password=password_hash,
                date_created=tz_now
            )
        except PastPassword.DoesNotExist:
            past_password = PastPassword()
            past_password.userpassword_desc = userpassword_desc
            past_password.password = password_hash
            past_password.save()

    def get_help_text(self):
        help_msg = ('For security, you can not change your password again for [days hh:mm:ss]: {}, and'
                    ' your new password can not be identical to any of the '
                    'previously entered in the past [days hh:mm:ss] {}').format(
            str(timedelta(seconds=self.password_min_age)),
            str(timedelta(seconds=self.password_reuse_interval)))
        return help_msg

    def password_expired(self, user=None):
        passwd_expired = False
        if user.is_staff or user.is_superuser:
            # for staff and above do not enforce password expire
            return passwd_expired
        if self.password_expire <= 0:
            # password never expire, password_expire set to 0 or negative
            # effectively disable password expire
            return passwd_expired
        for userpassword_desc in UserPasswordDescriptor.objects.filter(user=user):
            passwds = None
            try:
                # only check invalid reuse within reuse_interval
                passwds = PastPassword.objects.filter(
                    userpassword_desc=userpassword_desc
                ).order_by('-date_created')
            except PastPassword.DoesNotExist:
                pass
            if passwds is not None and passwds.first() is not None:
                if (datetime.now(timezone.utc) - passwds.first().date_created).total_seconds() >= self.password_expire:
                    # the elapsed time since last password change / create is more than password_expire
                    passwd_expired = True
        return passwd_expired
