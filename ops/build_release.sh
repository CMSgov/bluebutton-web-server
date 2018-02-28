#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="Blue Button API"
BUILD_MESSAGE=""
GITHUB_REPO="CMSgov/bluebutton-web-server"

usage() {
    cat <<EOF >&2
Start a new $PROJECT_NAME release.

Usage: $(basename "$0") [-ch] [-t previous-tag new-tag]

Options:
  -c    wait for confirmation before committing and pushing to GitHub
  -h    print this help text and exit
  -t    manually specify tags
  -p    automatically push new tags to origin.
EOF
}

CONFIRM=
MANUAL_TAGS=
AUTO_PUSH=
while getopts ":chtp" opt; do
    case "$opt" in
        c)
            CONFIRM=1
            ;;
        t)
            MANUAL_TAGS=1
            ;;
	p)
	    AUTO_PUSH=1
	    ;;
        h)
            usage
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

shift $((OPTIND-1))

if [ $# -lt 2 ] && [ -n "$MANUAL_TAGS" ]; then
  usage
  exit 1
fi

# fetch tags before any tag lookups so we have the most up-to-date list
# and generate the correct next release number
git fetch --tags

if [ -n "$MANUAL_TAGS" ]; then
  PREVTAG="$1"
  NEWTAG="$2"
  PREVRELEASENUM=${PREVTAG//^r/}
  NEWRELEASENUM=${NEWTAG//^r/}
else
  PREVTAG=$(git tag | sort -n | tail -1)
  if [ ! -n "$PREVTAG" ]; then
      PREVTAG="r0"
      PREVRELEASENUM=0
  else
      PREVRELEASENUM=$(git tag | grep '^r[0-9]' | sed 's/^r//' | sort -n | tail -1)
  fi
  NEWRELEASENUM=$(($PREVRELEASENUM + 1))
  PREVTAG="r$PREVRELEASENUM"
  NEWTAG="r$NEWRELEASENUM"
fi

git checkout -b "release-$NEWRELEASENUM"

git tag -a -m"$PROJECT_NAME release $NEWTAG" -s "$NEWTAG"

if [ -n "$AUTO_PUSH" ]; then
    git push --tags

    git push origin "release-$NEWRELEASENUM"
fi

echo "Release $NEWTAG created."
echo
echo "Hotfixes should be made against release-$NEWRELEASENUM"
echo "Create PR at https://github.cms.gov/$GITHUB_REPO/compare/release-$NEWRELEASENUM?expand=1"
echo
echo $BUILD_MESSAGE
echo
