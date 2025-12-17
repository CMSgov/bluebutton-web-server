from django.db import models
import datetime
import hashlib
from django.db import IntegrityError


# We want to be able to salt some values, so that they cannot
# be recovered into their original form via brute force.
SALT = "this-should-be-a-random-salt-and-a-secret-from-the-env"

# Kinda... elch. It creates a global dictionary where tuples
# are stored; if they exist, we don't try and re-write them
# to the database.
in_dictionary = {}


def add_salt(s):
    s = f'{s}{SALT}'
    shake = hashlib.shake_128(s.encode('utf-8'))
    return shake.hexdigest(8)


class EventCounter(models.Model):
    source_hash = models.BigIntegerField()
    event_hash = models.BigIntegerField()
    timestamp = models.DateTimeField(default=datetime.datetime.now)

    @classmethod
    def log(cls, source, event, salted=False):
        # If we want things salted, then we should add some salt befre
        # the value is hashed. That way, it can't be brute-forced later.
        if salted:
            event = f'{event}{SALT}'
        source_shake = hashlib.shake_128(f'{source}'.encode('utf-8'))
        # Use 64 bits of the 128-bit hash. Make sure we're signed, or it
        # won't fit in the 64-bit signed range in the DB.
        source_h = int.from_bytes(source_shake.digest(8), 'big', signed=True)
        event_shake = hashlib.shake_128(f'{event}'.encode('utf-8'))
        event_h = int.from_bytes(event_shake.digest(8), 'big', signed=True)

        # If they asked for it to be salted, we also do not want to plaintext
        # the dictionary entry, later. Replace the event name with a few bytes
        # of the digest from the salted version. This is effectively a unique
        # mapping, but also quite random. In short: once you salt something,
        # there is no getting back what the source value was. This is good for
        # names, identifiers, etc. that we want to track uniquely, but don't want
        # to store in the DB in a way that the source text could ever be recovered.
        if salted:
            event = event_shake.hexdigest(8)

        # There is no making the hashes portable between different
        # implementations. We can only require integers of a given bit-width.
        cls.objects.create(
            source_hash=source_h,
            event_hash=event_h,
        )

        # Add everything to the dictionary, or try to.
        # Do a fast in-memory check, so we don't have to hit the DB
        # unless absolutely necessary. With multiple instances, we still
        # have to make sure the integrity error is handled at the DB level,
        # but at least each instance is smart about not re-logging to the dictionary.
        hash_tuple = (source_h, event_h)
        if in_dictionary.get(hash_tuple):
            pass
        else:
            try:
                # Note that create()/throw is faster than get_or_create(),
                # because the latter is 2x DB hits.
                in_dictionary[hash_tuple] = True
                EventDictionary.objects.create(
                    source_hash=source_h,
                    event_hash=event_h,
                    source_name=source,
                    event_name=event
                )
            except IntegrityError:
                # we explicitly only want to add things to the dictionary once.
                pass


class EventDictionary(models.Model):
    # We want the pair on source/event hash to be unique
    source_hash = models.BigIntegerField()
    event_hash = models.BigIntegerField()
    source_name = models.TextField()
    event_name = models.TextField()
    timestamp = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        unique_together = ('source_hash', 'event_hash',)

# Perhaps these are all at the front of the app, at startup-time,
# and there's a similar pattern as above: @classmethod that
# makes sure to only add once.


class EventSummary(models.Model):
    # A short tag representing the summary; e.g. BB2_V3_ENDPOINTS_SUM
    metric_tag = models.TextField()
    # A plain-language description of the metric
    metric_description = models.TextField()
    # The value associated with this metric
    # Assume it might be big.
    metric_value = models.BigIntegerField()
