gonogo () {
    STEP=$1
    result=$?
    if [[ $result == 0 ]]; then
        echo "🔵 OK: $STEP"
        return 0
    else
        echo "⛔ BADNESS: $STEP - $result"
        exit 1
    fi
}