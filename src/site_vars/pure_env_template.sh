#!/usr/bin/env bash
export PB1=''
export PB2=''
export PB1_MGT=''
export PB2_MGT=''
export API_TOKEN=''
export API_TOKEN_S200=''
export REPLICATION_CUTOFF=''

LOCAL_IP=$(ip route get $(getent hosts $PB1 | awk '{ print $1 }') | awk '{ print $5; exit}')
export LOCAL_IP
