#!/bin/bash
pg_login="<your_pg_login>"
pg_pass="<your_pg_password>"
pg_db_name="rmrk"
pg_host="localhost"
pg_connect="postgresql://$pg_login:$pg_pass@$pg_host/$pg_db_name"
home_dir="/home/ubuntu"
cd $home_dir

ipfs_vLite=`dig precon-lite.rmrk.link TXT | grep ipfs | cut -f 2 -d '"' | cut -f 2 -d '='`
url_vLite="http://cloudflare-ipfs.com/$ipfs_vLite"

ipfs_v1=`dig precon-mkt.rmrk.app TXT | grep ipfs | cut -f 2 -d '"' | cut -f 2 -d '='`
url_v1="http://cloudflare-ipfs.com/$ipfs_v1"

ipfs_v2=`dig precon-rmrk2.rmrk.link TXT | grep ipfs | cut -f 2 -d '"' | cut -f 2 -d '='`
url_v2="http://cloudflare-ipfs.com/$ipfs_v2"


wget $url_vLite -O $home_dir/dump_vLite.dump
wget $url_v1 -O $home_dir/dump_v1.dump
wget $url_v2 -O $home_dir/dump_v2.dump

last_block_vLite=`psql "$pg_connect" -t -c "select lastBlock from lastblock_vlite;" | tr -d ' ' | head -1`
last_block_v1=`psql "$pg_connect" -t -c "select lastBlock from lastblock_v1;" | tr -d ' ' | head -1`
last_block_v2=`psql "$pg_connect" -t -c "select lastBlock from lastblock_v2;" | tr -d ' ' | head -1`

python3 $home_dir/rmrk2psql.py -i $home_dir/dump_vLite.dump -o $home_dir/output_vLite.sql -v -b $last_block_vLite
python3 $home_dir/rmrk2psql.py -i $home_dir/dump_v1.dump -o $home_dir/output_v1.sql -v -b $last_block_v1
python3 $home_dir/rmrk2psql.py -i $home_dir/dump_v2.dump -o $home_dir/output_v2.sql -v -b $last_block_v2

psql "$pg_connect" -f $home_dir/output_vLite.sql
psql "$pg_connect" -f $home_dir/output_v1.sql
psql "$pg_connect" -f $home_dir/output_v2.sql
