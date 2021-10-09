# rmrk2psql
### rmrk2psql parser for rmrk v1, v2, vLite dumps to PSQL format for rmrk hacktoberfest

**How to run:** 

python3 ./rmrk.py -i <dump_filename> -o <output_sql_filename> [-b] <start_block> [-v] <verbose_mode>

python3 ./rmrk2psql.py [-h] -i DUMP_FILENAME -o OUTPUT_SQL_FILENAME [-b START_BLOCK] [-v]

python3 ./rmrk2psql.py -i precon-lite.rmrk.link -o output_vlite.sql -v

**Required arguments:**

  -i DUMP_FILENAME, --input DUMP_FILENAME
                        RMRK dump file name
                        
  -o OUTPUT_SQL_FILENAME, --output OUTPUT_SQL_FILENAME
                        Output PSQL file name

**Optional arguments:**
  -h, --help            show this help message and exit
  
  -b START_BLOCK, --block START_BLOCK
                        Start block, 0 by default
                        
  -v, --verbose         Verbose mode

**Fresh dump urls:**

https://gateway.pinata.cloud/ipns/precon-mkt.rmrk.app - _RMRKv1_ 

https://gateway.pinata.cloud/ipns/precon-rmrk2.rmrk.link - _RMRKv2_

https://gateway.pinata.cloud/ipns/precon-lite.rmrk.link - _RMRK2vLite_
