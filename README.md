# rmrk2psql
rmrk2psql parser for rmrk v1, v2, vLite dumps to PSQL format for rmrk hacktoberfest

usage: rmrk2psql.py [-h] -i DUMP_FILENAME -o OUTPUT_SQL_FILENAME [-b START_BLOCK] [-v]

How to run: python3 ./rmrk.py -i <dump_filename> -o <output_sql_filename> [-b] <start_block> [-v]

optional arguments:
  -h, --help            show this help message and exit

required arguments:
  -i DUMP_FILENAME, --input DUMP_FILENAME
                        RMRK dump file name
  -o OUTPUT_SQL_FILENAME, --output OUTPUT_SQL_FILENAME
                        Output PSQL file name

optional arguments:
  -b START_BLOCK, --block START_BLOCK
                        Start block, 0 by default
  -v, --verbose         Verbose mode

fresh dump urls:
https://gateway.pinata.cloud/ipns/precon-mkt.rmrk.app - RMRKv1 
https://gateway.pinata.cloud/ipns/precon-rmrk2.rmrk.link - RMRKv2
https://gateway.pinata.cloud/ipns/precon-lite.rmrk.link - RMRK2vLite
