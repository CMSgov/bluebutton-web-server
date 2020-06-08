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

    # Position mappings. Note is minus one from PDF document position.
    CHAR_POSITION_C = [0]
    CHAR_POSITION_N = [3, 6, 9, 10]
    CHAR_POSITION_A = [1, 4, 7, 8]
    CHAR_POSITION_AN = [2, 5]

    msg = ""
    # Check length
    if len(mbi) != 11:
        msg = "Invalid length = {}".format(len(mbi))
        return False, msg

    # Iterate over character positions:
    for pos in range(0, len(mbi)):
        # Validate type C
        if pos in CHAR_POSITION_C and not mbi[pos] in CHAR_TYPE_C:
            msg = "Invalid char in pos = {}".format(pos)
            return False, msg

        # Validate type N
        if pos in CHAR_POSITION_N and not mbi[pos] in CHAR_TYPE_N:
            msg = "Invalid char in pos = {}".format(pos)
            return False, msg

        # Validate type A (exception for 2nd position = "S")
        if (pos in CHAR_POSITION_A and not mbi[pos] in CHAR_TYPE_A) and (pos == 1 and mbi[pos] != "S"):
            msg = "Invalid char in pos = {}".format(pos)
            return False, msg

        # Validate type AN
        if pos in CHAR_POSITION_AN and (not mbi[pos] in CHAR_TYPE_A + CHAR_TYPE_N):
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
    return len(mbi) == 11 and mbi[1] == "S"
