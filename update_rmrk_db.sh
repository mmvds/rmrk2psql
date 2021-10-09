#!/bin/bash
pg_login="<your_pg_login>"
pg_pass="<your_pg_password>"
pg_db_name="rmrk"
pg_host="localhost"
pg_connect="postgresql://$pg_login:$pg_pass@$pg_host/$pg_db_name"
home_dir="/home/ubuntu"
cd $home_dir

wget https://gateway.pinata.cloud/ipns/precon-lite.rmrk.link -O $home_dir/dump_vLite.dump
wget https://gateway.pinata.cloud/ipns/precon-mkt.rmrk.app -O $home_dir/dump_v1.dump
wget https://gateway.pinata.cloud/ipns/precon-rmrk2.rmrk.link -O $home_dir/dump_v2.dump

last_block_vLite=`psql "$pg_connect" -t -c "select lastBlock from lastblock_vlite;" | tr -d ' ' | head -1`
last_block_v1=`psql "$pg_connect" -t -c "select lastBlock from lastblock_v1;" | tr -d ' ' | head -1`
last_block_v2=`psql "$pg_connect" -t -c "select lastBlock from lastblock_v2;" | tr -d ' ' | head -1`

python3 $home_dir/rmrk2psql.py -i $home_dir/dump_vLite.dump -o $home_dir/output_vLite.sql -v -b $last_block_vLite
python3 $home_dir/rmrk2psql.py -i $home_dir/dump_v1.dump -o $home_dir/output_v1.sql -v -b $last_block_v1
python3 $home_dir/rmrk2psql.py -i $home_dir/dump_v2.dump -o $home_dir/output_v2.sql -v -b $last_block_v2

psql "$pg_connect" -f $home_dir/output_vLite.sql
psql "$pg_connect" -f $home_dir/output_v1.sql
psql "$pg_connect" -f $home_dir/output_v2.sql