#!/usr/bin/env bash

# a global hash map holding commit hash to pr link (derived from ref names) pairs
declare -A hash2namesref=( ["k1"]="v1")

# populate global hash map hash2namesref with 
# key value pairs as <commit hash> to <hueristically derived pr link>
# which are derived from git log --pretty=format:'%H %d' output
get_hash2pr_map() {
    commit_hash_refnames_regex="^([a-f0-9]{40})[[:blank:]]*(.*)"
    refnames_pr_id_regex="^\(.*/pr/([0-9]+).*\)"
    GIT_LOG_LHASH2REFNAMES="$(mktemp /tmp/$(basename $0).XXXXXX.h2refnames)"
    git log --pretty=format:'%H %d' ${COMMIT_RANGE} > ${GIT_LOG_LHASH2REFNAMES}
    while read -r line || [ -n "$line" ]; do
        line=$(echo "$line" | xargs)
        if [[ $line =~ $commit_hash_refnames_regex ]];
        then
            hash=${BASH_REMATCH[1]}
            nmref=${BASH_REMATCH[2]}
            pr_link=""
            # echo "MATCH: " "hash=" "$hash" "nmref=" "$nmref"
            if [[ $nmref =~ $refnames_pr_id_regex ]];
            then
                pr_link="(#${BASH_REMATCH[1]})"
                # echo "PR LINK:" "$pr_link" 
            fi
            hash2namesref["$hash"]="$pr_link"
        else
            echo "Warning: malformed git log record skipped, expecting <commit hash> [<ref names>]"
            echo "Record=" "$line"
        fi
    done < "${GIT_LOG_LHASH2REFNAMES}"
}

# return release history string with '\n' delimited
generate_release_history() {
    commit_hash_subj_regex="^([a-f0-9]{40})[[:blank:]]+(.+)(\(\#[0-9]+\))?"
    GIT_LOG_LHASH2SUBJ="$(mktemp /tmp/$(basename $0).XXXXXX.h2subj)"
    git log --pretty=format:'%H %s' ${COMMIT_RANGE} > ${GIT_LOG_LHASH2SUBJ}
    rel_hist=""
    while read -r line || [ -n "$line" ]; do
        line=$(echo "$line" | xargs)
        if [[ $line =~ $commit_hash_subj_regex ]];
        then
            hash=${BASH_REMATCH[1]}
            subj=${BASH_REMATCH[2]}
            pr_link=${BASH_REMATCH[3]}
            release_entry="- ${subj}"
            if [ -z "${pr_link}" ];
            then
                pr_link="${hash2namesref[$hash]}"
                release_entry="- ${subj} ${pr_link}"
            fi
            rel_hist="${rel_hist}\n${release_entry}"
        else
            echo "Warning: malformed git log record skipped, expecting <commit hash> <subject title> [<pr link>]"
            echo "Record=" "$line"
        fi
    done < "${GIT_LOG_LHASH2SUBJ}"
    echo "${rel_hist}"
}

# args:
# $1 - ${NEW_RELEASE_TAG}
# $2 - ${NEW_RELEASE_DATE}
# $3 - ${NEW_RELEASE_HISTORY}
write_release_note() {
    GITHUB_RELEASE_PAYLOAD="$(mktemp /tmp/$(basename $0).XXXXXX)"
    echo "{" > "${GITHUB_RELEASE_PAYLOAD}"
    echo '"tag_name":' "\"$1\"," >> "${GITHUB_RELEASE_PAYLOAD}"
    echo '"name":' "\"$1\"," >> "${GITHUB_RELEASE_PAYLOAD}"
    echo '"body":' "\"$1 - $2\n================\n$3\"," >> "${GITHUB_RELEASE_PAYLOAD}"
    echo '"draft": false,' >> "${GITHUB_RELEASE_PAYLOAD}"
    echo '"prerelease": false' >> "${GITHUB_RELEASE_PAYLOAD}"
    echo "}" >> "${GITHUB_RELEASE_PAYLOAD}"
}

# helper to show usage
usage() {
    echo "Usage:"
    echo "build_autoincrement_release.sh [<commit range>]"
    echo ""
    echo "Example 1: build a release since last release tag"
    echo "build_autoincrement_release.sh"
    echo ""
    echo "Example 2: build a release between 2 commits or 2 tags - for testing usually"
    echo "below command builds r93 with pull requests between r91 and r92:"
    echo "build_autoincrement_release.sh 'r91..r92'"
}

set -eo pipefail

commit_range_regex="[a-z0-9]{1,40}\.\.[a-z0-9]{1,40}"
COMMIT_RANGE=""

# Parse command line option
if [ $# -eq 0 ];
then
    echo "Build auto increment release..."
else
    if [[ $1 =~ $commit_range_regex ]];
    then
        COMMIT_RANGE="$1"
    else
        usage
        exit
    fi
fi

# Detect if running from a fork
#
GITHUB_REPO="$(git ls-remote --quiet --get-url | grep -o '[^:/]\{1,\}/bluebutton-css')"

# Test running from root of repository
#
if [[ ! -f "gulpfile.js" ]]; then
    echo "Please run script from the root of repository: ./ops/build_autoincrement_release.sh"
    exit 1
fi

# Test running from master branch
#
if [[ "$(git branch --show-current)" != "master" ]]; then
    echo "Please run script from the master branch of repository: git checkout master"
    exit 1
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
REMOTE_TAGS="$(git ls-remote --quiet --tags | grep -o 'r[0-9]\{1,\}[-hotfix]*' | sort -u -V)"

if [[ "${LOCAL_TAGS}" != "${REMOTE_TAGS}" ]]; then
    echo "Please reconcile your local repository tags, they do not match tags on the remote repository!"
    exit 1
fi

# Determine if new release tag is needed
#
PREV_RELEASE_TAG="$(git describe --tags --abbrev=0)"
NEW_RELEASE_TAG="r$((${PREV_RELEASE_TAG:1} + 1))"
NEW_RELEASE_DATE="$(date +%Y-%m-%d)"

# if no commit range from command line then default to last release to HEAD
if [ -z "${COMMIT_RANGE}" ];
then
    COMMIT_RANGE="${PREV_RELEASE_TAG}..HEAD"
fi

# NEW_RELEASE_HISTORY="$(git log --pretty=format:'- %s %d' ${PREV_RELEASE_TAG}..HEAD)"
# generate hash map of <commit hash> to <pr link>
get_hash2pr_map

NEW_RELEASE_HISTORY=$(generate_release_history)

if [[ -z "${NEW_RELEASE_HISTORY}" ]]; then
   echo "No commits detected since previous release, no need for a new release, exiting."
   exit 0
fi

# Create and push new release tag
#
git tag -a -s -m "Blue Button CSS release $NEW_RELEASE_TAG" "$NEW_RELEASE_TAG"
git push --quiet --tags

# Create GitHub release template
#
write_release_note "${NEW_RELEASE_TAG}" "${NEW_RELEASE_DATE}" "${NEW_RELEASE_HISTORY}"

# Create GitHub release via API request
#
GITHUB_RELEASE_STATUS="$(mktemp /tmp/$(basename $0).XXXXXX)"

curl -s -X POST -H "Accept: application/vnd.github.v3+json" \
                -H "Authorization: token ${GITHUB_ACCESS_TOKEN}" \
                "https://api.github.com/repos/${GITHUB_REPO}/releases" \
                --data-binary "@${GITHUB_RELEASE_PAYLOAD}" > "${GITHUB_RELEASE_STATUS}"

# Verify GitHub release
if [[ "$(grep '"errors":' ${GITHUB_RELEASE_STATUS})" ]]; then
    echo "Error during release creation, dumping debug output!"
    echo "Release JSON payload:"
    cat "${GITHUB_RELEASE_PAYLOAD}"
    echo "Release API status:"
    cat "${GITHUB_RELEASE_STATUS}"
    rm "/tmp/$(basename $0)"*
    exit 1
else
    echo "Release created successfully: https://github.com/${GITHUB_REPO}/releases/tag/${NEW_RELEASE_TAG}"
    rm "/tmp/$(basename $0)"*
    exit 0
fi
