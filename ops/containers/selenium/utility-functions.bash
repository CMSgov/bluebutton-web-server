#!/usr/bin/env bash

########################################
# Echo function that includes script name on each line for console log readability
echo_msg () {
	echo "$(basename $0): $*"
}

set_slsx () {
    export DJANGO_MEDICARE_SLSX_LOGIN_URI="https://test.medicare.gov/sso/authorize?client_id=bb2api"
    export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="https://test.accounts.cms.gov/health"
    export DJANGO_SLSX_TOKEN_ENDPOINT="https://test.medicare.gov/sso/session"
    export DJANGO_SLSX_SIGNOUT_ENDPOINT="https://test.medicare.gov/sso/signout"
    export DJANGO_SLSX_USERINFO_ENDPOINT="https://test.accounts.cms.gov/v1/users"
}

set_msls () {
    if [ "$TARGET_ENV" = "codebuild" ]; then
        # In codebuild, MSLSX would need to be available on the network
        export DJANGO_MEDICARE_SLSX_LOGIN_URI="http://mslsx:8080/sso/authorize?client_id=bb2api"
        export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="http://mslsx:8080/health"
        export DJANGO_SLSX_TOKEN_ENDPOINT="http://mslsx:8080/sso/session"
        export DJANGO_SLSX_SIGNOUT_ENDPOINT="http://mslsx:8080/sso/signout"
        export DJANGO_SLSX_USERINFO_ENDPOINT="http://mslsx:8080/v1/users"
    else
        export DJANGO_MEDICARE_SLSX_LOGIN_URI="http://localhost:8080/sso/authorize?client_id=bb2api"
        export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="http://localhost:8080/health"
        export DJANGO_SLSX_TOKEN_ENDPOINT="http://localhost:8080/sso/session"
        export DJANGO_SLSX_SIGNOUT_ENDPOINT="http://localhost:8080/sso/signout"
        export DJANGO_SLSX_USERINFO_ENDPOINT="http://localhost:8080/v1/users"
    fi
}