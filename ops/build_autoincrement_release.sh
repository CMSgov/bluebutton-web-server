#!/usr/bin/env bash

set -euo pipefail

# Change this value if testing against a fork
#
GITHUB_REPO="CMSgov/bluebutton-web-server"

# Test running from root of repository
#
if [[ ! -f "LICENSE" ]]; then
    echo "Please run script from the root of repository: ./ops/build_autoincrement_release.sh"
    exit 1
fi

# Test running from master branch
#
if [[ "$(git branch --show-current)" != "master" ]]; then
    echo "Please run script from the master branch of repository: git checkout master"
fi

# Test GitHub access token
#
if [[ -z "${GITHUB_ACCESS_TOKEN}" ]]; then
    echo "Please set your GitHub access token: export GITHUB_ACCESS_TOKEN=\"XXXSAMPLETOKENVALUEXXX\""
    exit 1
fi

if [[ ! "$(curl -s -H "Accept: application/vnd.github.v3+json" \
                   -H "Authorization: token ${GITHUB_ACCESS_TOKEN}" \
                    "https://api.github.com/user" | grep login)" ]]; then
    echo "Please check your token, GitHub API did not detect an authenticated user!"
    exit 1
fi

# Test GitHub and local tags are in sync
#
git pull --quiet --all --tags
LOCAL_TAGS="$(git tag | sort -u -V)"
REMOTE_TAGS="$(git ls-remote --quiet --tags | grep -o 'r[0-9]\{1,\}' | sort -u -V)"

if [[ "${LOCAL_TAGS}" != "${REMOTE_TAGS}" ]]; then
    echo "Please reconcile your local repository tags, they do not match tags on the remote repository!"
    exit 1
fi

# Determine if new release tag is needed
#
PREV_RELEASE_TAG="$(git describe --tags --abbrev=0)"
NEW_RELEASE_TAG="r$((${PREV_RELEASE_TAG:1} + 1))"
NEW_RELEASE_DATE="$(date +%Y-%m-%d)"
NEW_RELEASE_HISTORY="$(git log --pretty=format:'- %s' ${PREV_RELEASE_TAG}..HEAD)"

if [[ -z "${NEW_RELEASE_HISTORY}" ]]; then
   echo "No commits detected since previous release, no need for a new release, exiting."
   exit 0
fi

# Create and push new release tag
#
git tag -a -s -m "Blue Button API release $NEW_RELEASE_TAG" "$NEW_RELEASE_TAG"
git push --quiet --tags

# Create GitHub release template
#
GITHUB_RELEASE_PAYLOAD="$(mktemp /tmp/$(basename $0).XXXXXX)"

cat << "EOF" > "${GITHUB_RELEASE_PAYLOAD}"
{
    "tag_name": "NEW_RELEASE_TAG",
    "name": "NEW_RELEASE_TAG",
    "body": "NEW_RELEASE_TAG - NEW_RELEASE_DATE\n================\nNEW_RELEASE_HISTORY",
    "draft": false,
    "prerelease": false
}
EOF

sed -i "s/NEW_RELEASE_TAG/${NEW_RELEASE_TAG}/g" "${GITHUB_RELEASE_PAYLOAD}"
sed -i "s/NEW_RELEASE_DATE/${NEW_RELEASE_DATE}/g" "${GITHUB_RELEASE_PAYLOAD}"
sed -i "s/NEW_RELEASE_HISTORY/${NEW_RELEASE_HISTORY//$'\n'/'\\n'}/g" "${GITHUB_RELEASE_PAYLOAD}"

# Create GitHub release via API request
#
GITHUB_RELEASE_STATUS="$(mktemp /tmp/$(basename $0).XXXXXX)"

curl -s -X POST -H "Accept: application/vnd.github.v3+json" \
                -H "Authorization: token ${GITHUB_ACCESS_TOKEN}" \
                "https://api.github.com/repos/${GITHUB_REPO}/releases" \
                --data-binary "@${GITHUB_RELEASE_PAYLOAD}" > "${GITHUB_RELEASE_STATUS}"

# Verify GitHub release
#
if [[ "$(grep 'errors' ${GITHUB_RELEASE_STATUS})" ]]; then
    echo "Error during release creation, dumping debug output!"
    echo "Release JSON payload:"
    cat "${GITHUB_RELEASE_PAYLOAD}"
    rm "${GITHUB_RELEASE_PAYLOAD}"
    echo "Release API status:"
    cat "${GITHUB_RELEASE_STATUS}"
    rm "${GITHUB_RELEASE_STATUS}"
    exit 1
else
    echo "Release created successfully: https://github.com/${GITHUB_REPO}/releases/tag/${NEW_RELEASE_TAG}"
    rm "${GITHUB_RELEASE_PAYLOAD}"
    rm "${GITHUB_RELEASE_STATUS}"
    exit 0
fi