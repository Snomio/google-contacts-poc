#!/bin/bash

function do_help(){
cat << EOF
Usage: $0 <sync|syncdir|run|syncandrun|shell|phoneconf>"
    sync:   The sync command downloads locally the contacts
            In order to access the Google contacts the script
            needs the client secrets file. Such file can be obtained
            from the Google API console (https://console.developers.google.com/apis/ )
            The file can be generated creating an OAuth ID, selecting Application type = other

    syncdir:  The sync command downloads locally the gsuite contacts domain directory
            In order to access the Google contacts directory the script
            needs the client secrets file. Such file can be obtained
            from the Google API console (https://console.developers.google.com/apis/ )
            You need to activate  Admin SDK API.
            The file can be generated creating an OAuth ID, selecting Application type = other

    run:    The run command start the local http server serving the XML applications

    syncandrun: This commands first sync the data and then starts the server

    shell:  Run a bash sell into the container
    
    phoneconf: configure the Snom phone (PHONE_IP and APP_URL env. variables required
EOF
}

function bailout() {
    echo "ERROR: $@"
    exit 255
}

function phone_conf(){
    [[ "${PHONE_URL}x" == "x" ]] && bailout "missing PHONE_URL env. variable"
    [[ "${APP_URL}x" == "x" ]] && bailout "missing APP_URL env. variable"

    echo "Configuring the phone settings"
    curl -v -G --data-urlencode "settings=save" \
            --data-urlencode "dkey_directory=url ${APP_URL}/snom" \
            --data-urlencode "action_incoming_url=${APP_URL}/snom/lookup?number=\$remote"\
            ${PHONE_URL}/dummy.htm
}

case $1 in
    phoneconf)
        shift
        phone_conf
        ;;
    sync)
        shift
        python /data/sync.py --noauth_local_webserver $@
        ;;

    syncdir)
        shift
        python /data/sync_directory.py --noauth_local_webserver $@
        ;;

    run)
        shift
        cd /data/web && python /data/web/app.py $@
        ;;

    shell)
        bash
        ;;

    syncandrun)
        python /data/sync.py --noauth_local_webserver
        cd /data/web && python /data/web/app.py
        ;;

    *)
        echo "ERROR: you can use the following commands: sync, syncdir, run, shell"
        do_help
        ;;
esac
