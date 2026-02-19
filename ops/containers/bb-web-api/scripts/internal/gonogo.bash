gonogo () {
    STEP=$1
    result=$?
    if [[ $result == 0 ]]; then
        echo "$STEP: OK"
        return 0
    else
        echo "$STEP: ERR $result"
        exit -1
    fi
}