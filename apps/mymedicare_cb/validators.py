"""
  Validators for SLS user_info() return values.
"""


def is_mbi_format_valid(mbi):
    """
    Validate MBI ID format.

    This includes the BFD's special case of an "S" in the 2nd position
    denoting a synthetic MBI value.

    Reference for MBI ID format:
       https://www.cms.gov/Medicare/New-Medicare-Card/Understanding-the-MBI-with-Format.pdf
    """
    # Character types
    CHAR_TYPE_C = "123456789"
    CHAR_TYPE_N = "0123456789"
    # Type is alpha minus: S,L,O,I,B,Z
    CHAR_TYPE_A = "ACDEFGHJKMNPQRTUVWXY"
    CHAR_TYPE_AN = CHAR_TYPE_A + CHAR_TYPE_N

    # Position mapping list[0 thru 10]:
    VALID_VALUES_BY_POS = [CHAR_TYPE_C,
                           CHAR_TYPE_A + "S",
                           CHAR_TYPE_AN,
                           CHAR_TYPE_N,
                           CHAR_TYPE_A,
                           CHAR_TYPE_AN,
                           CHAR_TYPE_N,
                           CHAR_TYPE_A,
                           CHAR_TYPE_A,
                           CHAR_TYPE_N,
                           CHAR_TYPE_N]
    msg = ""
    # Check if NoneType.
    if mbi is None:
        return False, "Empty"

    # Check length.
    if len(mbi) != 11:
        msg = "Invalid length = {}".format(len(mbi))
        return False, msg

    # Check 11 character positions are valid.
    for pos in range(0, 11):
        if mbi[pos] not in VALID_VALUES_BY_POS[pos]:
            msg = "Invalid char in pos = {}".format(pos)
            return False, msg

    # Passes validation!
    return True, "Valid"


def is_mbi_format_synthetic(mbi):
    """
    Returns True if mbi format is synthetic.

    This is the case where there is an "S" in the 2nd position
    denoting a synthetic MBI value.
    """
    # Check if NoneType.
    if mbi is None:
        return None
    else:
        return len(mbi) == 11 and mbi[1] == "S"
