#!/bin/bash
cd /home/ubuntu
pg_login="postgres"
pg_pass="postpass"
pg_db_name="rmrk"
pg_host="localhost"
pg_connect="postgresql://$pg_login:$pg_pass@$pg_host/$pg_db_name"
home_dir="/home/ubuntu"

wget https://gateway.pinata.cloud/ipns/precon-lite.rmrk.link -O $home_dir/dump_vLite.dump
wget https://gateway.pinata.cloud/ipns/precon-mkt.rmrk.app -O $home_dir/dump_v1.dump
wget https://gateway.pinata.cloud/ipns/precon-rmrk2.rmrk.link -O $home_dir/dump_v2.dump

python3 $home_dir/rmrk2psql.py -i $home_dir/dump_vLite.dump -o $home_dir/output_vLite.sql -v
python3 $home_dir/rmrk2psql.py -i $home_dir/dump_v1.dump -o $home_dir/output_v1.sql -v
python3 $home_dir/rmrk2psql.py -i $home_dir/dump_v2.dump -o $home_dir/output_v2.sql -v

psql "$pg_connect" -f $home_dir/output_vLite.sql
psql "$pg_connect" -f $home_dir/output_v1.sql
psql "$pg_connect" -f $home_dir/output_v2.sql
