import json
import argparse
'''
usage: python3 ./rmrk2psql.py [-h] -i DUMP_FILENAME -o OUTPUT_SQL_FILENAME [-b START_BLOCK] [-v]

How to run: python3 ./rmrk2psql.py -i <dump_filename> -o <output_sql_filename> [-b] <start_block> [-v]

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
'''

# print in verbose mode


def print_v(print_text, is_verbose):
    if is_verbose:
        print(print_text)

# load data from the dump and define version


def load_data(filename):
    with open(filename, encoding="utf-8") as json_file:
        data = json.loads(
            (json.dumps(json.load(json_file)).replace("'", "''")))
    if 'bases' in data:
        version = 'v2'
    elif len(data['invalid']) == 0:
        version = 'vlite'
    else:
        version = 'v1'
    return data, version

# nfts parsing
# tables: nfts, nft_changes, nft_reactions, nft_resources (v2), nft_children (v2)


def parse_rmrk_nfts(data, start_block, version, is_verbose):
    schema_sql = f'''
CREATE TABLE IF NOT EXISTS nft_changes_{version} (nft_id text, change_index integer, field text, old text, new text, caller text, block integer, opType text);
CREATE UNIQUE INDEX IF NOT EXISTS idx_nft_id_change_{version} ON nft_changes_{version} (nft_id, change_index);
CREATE TABLE IF NOT EXISTS nft_reactions_{version} (nft_id text, reaction text, wallets jsonb);
CREATE UNIQUE INDEX IF NOT EXISTS idx_nft_id_reaction_{version} ON nft_reactions_{version} (nft_id, reaction);
'''
    if version != "v2":
        schema_sql += f'''
CREATE TABLE IF NOT EXISTS nfts_{version} (id text primary key, block integer, collection text, name text, instance text, transferable integer, sn text, metadata text, owner text, forsale bigint, burned text, updatedAtBlock integer);
'''
        nfts_sql = f"INSERT INTO nfts_{version} (id, block, collection, name, instance, transferable, sn, metadata, owner, forsale, burned, updatedAtBlock) VALUES \n"
    else:
        schema_sql += f'''
CREATE TABLE IF NOT EXISTS nfts_{version} (id text primary key, block integer, collection text, symbol text, priority jsonb, transferable integer, sn text, metadata text, owner text, rootowner text, forsale bigint, burned text, properties jsonb, pending text, updatedAtBlock integer);
CREATE TABLE IF NOT EXISTS nft_resources_{version} (nft_id text, id text, pending boolean, src text, slot text, thumb text, theme jsonb, base text, parts jsonb, themeId text, metadata text);
CREATE UNIQUE INDEX IF NOT EXISTS idx_nft_id_resource_{version} ON nft_resources_{version} (nft_id, id);
CREATE TABLE IF NOT EXISTS nft_children_{version} (nft_id text, id text, pending boolean, equipped text);
CREATE UNIQUE INDEX IF NOT EXISTS idx_nft_id_child_{version} ON nft_children_{version} (nft_id, id);
'''
        nfts_sql = f"INSERT INTO nfts_{version} (id, block, collection, symbol, priority, transferable, sn, metadata, owner, rootowner, forsale, burned, properties, pending, updatedAtBlock) VALUES \n"
        nft_resources_sql = f"INSERT INTO nft_resources_{version} (nft_id, id, pending, src, slot, thumb, theme, base, parts, themeId, metadata) VALUES \n"
        nft_children_sql = f"INSERT INTO nft_children_{version} (nft_id, id, pending, equipped) VALUES \n"
    nft_changes_sql = f"INSERT INTO nft_changes_{version} (nft_id, change_index, field, old, new, caller, block, opType) VALUES \n"
    nft_reactions_sql = f"INSERT INTO nft_reactions_{version} (nft_id, reaction, wallets) VALUES \n"
    print_v("Parsing NFTS:", is_verbose)
    counts = 0
    total_changes = 0
    total_reactions = 0
    total_resources = 0
    total_children = 0
    total_nfts = 0
    for nft_id in data['nfts']:
        nft = data['nfts'][nft_id]
        # print progress every 10%
        if counts % (len(data['nfts']) // 10) == 0:
            print_v(
                f"{((counts * 100) // len(data['nfts'])) + 1}%", is_verbose)
        counts += 1
        if len(nft['changes']) > 0:
            max_nft_block = nft['changes'][-1]['block']
        else:
            max_nft_block = 0
        max_nft_block = max(max_nft_block, nft['block'])
        if max_nft_block > start_block:
            if version != "v2":
                nfts_sql += f"(\'{nft['id']}\',{nft['block']},\'{nft['collection']}\',\'{nft['name']}\',\'{nft['instance']}\',{nft['transferable']},\'{nft['sn']}\',\'{nft.get('metadata', '')}\',\'{nft['owner']}\',{nft['forsale']},\'{nft['burned']}\',{max_nft_block}),\n"
            else:
                nfts_sql += f"(\'{nft['id']}\',{nft['block']},\'{nft['collection']}\',\'{nft['symbol']}\',\'{json.dumps(nft['priority'])}\',{nft['transferable']},\'{nft['sn']}\',\'{nft.get('metadata', '')}\',\'{nft['owner']}\',\'{nft['rootowner']}\',{nft['forsale']},\'{nft['burned']}\',\'{json.dumps(nft['properties'])}\',\'{nft['pending']}\',{max_nft_block}),\n"
            total_nfts += 1
            change_index = 0
            for change in nft['changes']:
                nft_changes_sql += f"(\'{nft['id']}\',{change_index},\'{change['field']}\',\'{change['old']}\',\'{change['new']}\',\'{change['caller']}\',{change['block']},\'{change['opType']}\'),\n"
                change_index += 1
                total_changes += 1
            for reaction in nft['reactions']:
                nft_reactions_sql += f"(\'{nft['id']}\',\'{reaction}\',\'{json.dumps(nft['reactions'][reaction])}\'),\n"
                total_reactions += 1
            if version == "v2":
                for resource in nft['resources']:
                    nft_resources_sql += f"(\'{nft['id']}\',\'{resource['id']}\',{resource.get('pending', False)},\'{resource.get('src','')}\',\'{resource.get('slot','')}\',\'{resource.get('thumb','')}\',\'{json.dumps(resource.get('theme',{}))}\',\'{resource.get('base','')}\',\'{json.dumps(resource.get('parts',[]))}\',\'{resource.get('themeId','')}\',\'{resource.get('metadata','')}\'),\n"
                    total_resources += 1
        if version == "v2":    
            for child in nft['children']:
                nft_children_sql += f"(\'{nft['id']}\',\'{child['id']}\',{child.get('pending', False)},\'{child['equipped']}\'),\n"
                total_children += 1
    if total_nfts == 0:
        nfts_sql = ""
    else:
        if version != "v2":
            nfts_sql = nfts_sql[:-2] + " ON CONFLICT (id) DO UPDATE SET block = excluded.block, collection = excluded.collection, name = excluded.name, instance = excluded.instance, transferable = excluded.transferable, sn = excluded.sn, metadata = excluded.metadata, owner = excluded.owner, forsale = excluded.forsale, burned = excluded.burned, updatedAtBlock = excluded.updatedAtBlock;"
        else:
            nfts_sql = nfts_sql[:-2] + " ON CONFLICT (id) DO UPDATE SET block = excluded.block, collection = excluded.collection, symbol = excluded.symbol, priority = excluded.priority, transferable = excluded.transferable, sn = excluded.sn, metadata = excluded.metadata, owner = excluded.owner, rootowner = excluded.rootowner, forsale = excluded.forsale, burned = excluded.burned, properties = excluded.properties, updatedAtBlock = excluded.updatedAtBlock;"
    if total_changes == 0:
        nft_changes_sql = ""
    else:
        nft_changes_sql = nft_changes_sql[:-2] + \
            " ON CONFLICT (nft_id, change_index) DO UPDATE SET field = excluded.field, old = excluded.old, new = excluded.new, caller = excluded.caller, opType = excluded.opType;"
    if total_reactions == 0:
        nft_reactions_sql = ""
    else:
        nft_reactions_sql = nft_reactions_sql[:-2] + \
            " ON CONFLICT (nft_id, reaction) DO UPDATE SET wallets = excluded.wallets;"
    if total_resources == 0:
        nft_resources_sql = ""
    else:
        nft_resources_sql = nft_resources_sql[:-2] + \
            " ON CONFLICT (nft_id, id) DO UPDATE SET pending = excluded.pending, src = excluded.src, slot = excluded.slot, thumb = excluded.thumb, theme = excluded.theme, base = excluded.base, parts = excluded.parts, themeId = excluded.themeId, metadata = excluded.metadata;"
    if total_children == 0:
        nft_children_sql = ""
    else:
        nft_children_sql = f"DELETE FROM nft_children_{version};" + nft_children_sql[:-2] + \
            " ON CONFLICT (nft_id, id) DO UPDATE SET pending = excluded.pending, equipped = excluded.equipped;"
    if version != "v2":
        return '\n'.join([schema_sql, nfts_sql, nft_changes_sql, nft_reactions_sql])
    else:
        return '\n'.join([schema_sql, nfts_sql, nft_changes_sql, nft_reactions_sql, nft_resources_sql, nft_children_sql])

# collections parsing
# tables: collections, collection_changes


def parse_rmrk_collections(data, start_block, version, is_verbose):
    schema_sql = f'''
CREATE TABLE IF NOT EXISTS collection_changes_{version} (collection_id text, change_index integer, field text, old text, new text, caller text, block integer, opType text);
CREATE UNIQUE INDEX IF NOT EXISTS idx_collection_id_changes_{version} ON collection_changes_{version} (collection_id, change_index);
'''
    if version != "v2":
        schema_sql += f"CREATE TABLE IF NOT EXISTS collections_{version} (id text primary key, block integer, name text, max int, issuer text, symbol text, metadata text, updatedAtBlock text);\n"
        collections_sql = f"INSERT INTO collections_{version} (id, block, name, max, issuer, symbol, metadata, updatedAtBlock) VALUES \n"
    else:
        schema_sql += f"CREATE TABLE IF NOT EXISTS collections_{version} (id text primary key, block integer, max int, issuer text, symbol text, metadata text, updatedAtBlock text);\n"
        collections_sql = f"INSERT INTO collections_{version} (id, block, max, issuer, symbol, metadata, updatedAtBlock) VALUES \n"
    collection_changes_sql = f"INSERT INTO collection_changes_{version} (collection_id, change_index, field, old, new, caller, block, opType) VALUES \n"

    print_v("Parsing Collections", is_verbose)
    total_changes = 0
    total_collections = 0
    for collection_id in data['collections']:
        collection = data['collections'][collection_id]
        if len(collection['changes']) > 0:
            max_collection_block = collection['changes'][-1]['block']
        else:
            max_collection_block = 0
        max_collection_block = max(max_collection_block, collection['block'])
        if max_collection_block > start_block:
            if version != "v2":
                collections_sql += f"(\'{collection['id']}\',{collection['block']},\'{collection['name']}\',{collection['max']},\'{collection['issuer']}\',\'{collection['symbol']}\',\'{collection.get('metadata', '')}\',{max_collection_block}),\n"
            else:
                collections_sql += f"(\'{collection['id']}\',{collection['block']},{collection['max']},\'{collection['issuer']}\',\'{collection['symbol']}\',\'{collection.get('metadata', '')}\',{max_collection_block}),\n"
            total_collections += 1
            change_index = 0
            for change in collection['changes']:
                collection_changes_sql += f"(\'{collection['id']}\',{change_index},\'{change['field']}\',\'{change['old']}\',\'{change['new']}\',\'{change['caller']}\',{change['block']},\'{change['opType']}\'),\n"
                change_index += 1
                total_changes += 1
    if total_collections == 0:
        collections_sql = ""
    else:
        if version != "v2":
            collections_sql = collections_sql[:-2] + \
                " ON CONFLICT (id) DO UPDATE SET block = excluded.block, name = excluded.name, max = excluded.max, issuer = excluded.issuer, symbol = excluded.symbol, metadata = excluded.metadata, updatedAtBlock = excluded.updatedAtBlock;"
        else:
            collections_sql = collections_sql[:-2] + \
                " ON CONFLICT (id) DO UPDATE SET block = excluded.block, max = excluded.max, issuer = excluded.issuer, symbol = excluded.symbol, metadata = excluded.metadata, updatedAtBlock = excluded.updatedAtBlock;"
    if total_changes == 0:
        collection_changes_sql = ""
    else:
        collection_changes_sql = collection_changes_sql[:-2] + \
            " ON CONFLICT (collection_id, change_index) DO UPDATE SET field = excluded.field, old = excluded.old, new = excluded.new, caller = excluded.caller, opType = excluded.opType;"

    return '\n'.join([schema_sql, collections_sql, collection_changes_sql])

# invalid messages parsing
#tables: invalid


def parse_rmrk_invalid(data, start_block, version, is_verbose):
    schema_sql = f"\nCREATE TABLE IF NOT EXISTS invalid_{version} (invalid_index integer primary key, op_type text, block integer, caller text, object_id text, message text);"
    invalid_sql = f"INSERT INTO invalid_{version} (invalid_index, op_type, block, caller, object_id, message) VALUES \n"

    print_v("Parsing Invalid messages", is_verbose)
    total_invalid = 0
    invalid_index = 0
    for message in data['invalid']:
        if message['block'] > start_block:
            invalid_sql += f"({invalid_index},\'{message['op_type']}\',{message['block']},\'{message['caller']}\',\'{message['object_id']}\',\'{message['message']}\'),\n"
            total_invalid += 1
        invalid_index += 1
    if total_invalid == 0:
        invalid_sql = ""
    else:
        invalid_sql = invalid_sql[:-2] + \
            " ON CONFLICT (invalid_index) DO UPDATE SET op_type = excluded.op_type, block = excluded.block, caller = excluded.caller, object_id = excluded.object_id, message = excluded.message;"
    return '\n'.join([schema_sql, invalid_sql])

# bases parsing
# tables: bases, base_changes, base_themes, base_parts


def parse_rmrk_bases(data, start_block, version, is_verbose):
    schema_sql = f'''
CREATE TABLE IF NOT EXISTS bases_{version} (id text primary key, block integer, symbol text, type text, issuer text, updatedAtBlock integer);
CREATE TABLE IF NOT EXISTS base_changes_{version} (base_id text, change_index integer, field text, old text, new text, caller text, block integer, opType text);
CREATE UNIQUE INDEX IF NOT EXISTS idx_base_id_changes_{version} ON base_changes_{version} (base_id, change_index);
CREATE TABLE IF NOT EXISTS base_themes_{version} (base_id text, theme_name text, theme jsonb);
CREATE UNIQUE INDEX IF NOT EXISTS idx_base_id_themes_{version} ON base_themes_{version} (base_id, theme_name);
CREATE TABLE IF NOT EXISTS base_parts_{version} (base_id text, id text, type text, src text, z integer, equippable jsonb, themable boolean);
CREATE UNIQUE INDEX IF NOT EXISTS idx_base_id_parts_{version} ON base_parts_{version} (base_id, id);
'''
    bases_sql = f"INSERT INTO bases_{version} (id, block, symbol, type, issuer, updatedAtBlock) VALUES \n"
    base_changes_sql = f"INSERT INTO base_changes_{version} (base_id, change_index, field, old, new, caller, block, opType) VALUES \n"
    base_themes_sql = f"INSERT INTO base_themes_{version} (base_id, theme_name, theme) VALUES \n"
    base_parts_sql = f"INSERT INTO base_parts_{version} (base_id, id, type, src, z, equippable, themable) VALUES \n"

    print_v("Parsing Bases", is_verbose)
    total_bases = 0
    total_changes = 0
    total_themes = 0
    total_parts = 0
    for base_id in data['bases']:
        base = data['bases'][base_id]
        if len(base['changes']) > 0:
            max_base_block = base['changes'][-1]['block']
        else:
            max_base_block = 0
        max_base_block = max(max_base_block, base['block'])
        if max_base_block > start_block:
            bases_sql += f"(\'{base['id']}\',{base['block']},\'{base['symbol']}\',\'{base['type']}\',\'{base['issuer']}\',{max_base_block}),\n"
            total_bases += 1
            change_index = 0
            for change in base.get('changes',[]):
                base_changes_sql += f"(\'{base['id']}\',{change_index},\'{change['field']}\',\'{change['old']}\',\'{change['new']}\',\'{change['caller']}\',{change['block']},\'{change['opType']}\'),\n"
                change_index += 1
                total_changes += 1
            for theme in base.get('themes',[]):
                base_themes_sql += f"(\'{base['id']}\',\'{theme}\',\'{json.dumps(base['themes'][theme])}\'),\n"
                total_themes += 1
            for part in base.get('parts',[]):
                base_parts_sql += f"(\'{base['id']}\',\'{part['id']}\',\'{part.get('type','')}\',\'{part.get('src', '')}\',{part.get('z','null')},\'{json.dumps(part.get('equippable',[]))}\',{part.get('themable','null')}),\n"
                total_parts += 1

    if total_bases == 0:
        bases_sql = ""
    else:
        bases_sql = bases_sql[:-2] + \
            " ON CONFLICT (id) DO UPDATE SET block = excluded.block, symbol = excluded.symbol, type = excluded.type, issuer = excluded.issuer, updatedAtBlock = excluded.updatedAtBlock;"

    if total_changes == 0:
        base_changes_sql = ""
    else:
        base_changes_sql = base_changes_sql[:-2] + \
            " ON CONFLICT (base_id, change_index) DO UPDATE SET field = excluded.field, old = excluded.old, new = excluded.new, caller = excluded.caller, opType = excluded.opType;"

    if total_themes == 0:
        base_themes_sql = ""
    else:
        base_themes_sql = base_themes_sql[:-2] + \
            " ON CONFLICT (base_id, theme_name) DO UPDATE SET theme = excluded.theme;"

    if total_parts == 0:
        base_parts_sql = ""
    else:
        base_parts_sql = base_parts_sql[:-2] + \
            " ON CONFLICT (base_id, id) DO UPDATE SET type = excluded.type, src = excluded.src, z = excluded.z, equippable = excluded.equippable, themable = excluded.themable;"

    return '\n'.join([schema_sql, bases_sql, base_changes_sql, base_themes_sql, base_parts_sql])

# last block updating
#tables: lastBlock


def parse_rmrk_lastBlock(data, version, is_verbose):
    schema_sql = f"\nCREATE TABLE IF NOT EXISTS lastBlock_{version} (lastBlock integer);"
    last_block_sql = f"TRUNCATE lastBlock_{version}; INSERT INTO lastBlock_{version} (lastBlock) VALUES ({data['lastBlock']});"
    return '\n'.join([schema_sql, last_block_sql])

# parsing the entire dump


def parse_rmrk_data(data, start_block, version, is_verbose):
    result_sql = parse_rmrk_nfts(data, start_block, version, is_verbose)
    result_sql += parse_rmrk_collections(data,
                                         start_block, version, is_verbose)
    result_sql += parse_rmrk_invalid(data, start_block, version, is_verbose)
    result_sql += parse_rmrk_lastBlock(data, version, is_verbose)
    if version == "v2":
        result_sql += parse_rmrk_bases(data, start_block, version, is_verbose)
    return result_sql


if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='How to run:\npython3 ./rmrk.py -i <dump_filename> -o <output_sql_filename> [-b] <start_block> [-v]\n')
    required = p.add_argument_group('required arguments')
    optional = p.add_argument_group('optional arguments')
    required.add_argument('-i', '--input', type=str, dest='dump_filename',
                          help='RMRK dump file name', required=True)
    required.add_argument('-o', '--output', type=str, dest='output_sql_filename',
                          help='Output PSQL file name', required=True)
    optional.add_argument('-b', '--block', type=str, dest='start_block',
                          default=0, help='Start block, 0 by default')
    optional.add_argument('-v', '--verbose', dest='is_verbose',
                          help='Verbose mode', action='store_true')
    args = p.parse_args()

    dump_filename = args.dump_filename
    output_sql_filename = args.output_sql_filename
    start_block = int(args.start_block)
    is_verbose = args.is_verbose

    print_v(f"Reading dump file: {dump_filename}", is_verbose)
    data, version = load_data(dump_filename)
    print_v(f"RMRK version {version}", is_verbose)
    result_sql = parse_rmrk_data(data, start_block, version, is_verbose)
    print_v(f"Generating PSQL file: {output_sql_filename}", is_verbose)
    with open(output_sql_filename, 'w') as output_file:
        output_file.write(result_sql)
    print_v("Done", is_verbose)
