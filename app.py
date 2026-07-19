#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Informatica PowerCenter XML Generator - Streamlit App
עטיפה עבור 4 מחוללי XML עובדים
לא משנים לוגיקה - רק מוסיפים UI של Streamlit
"""

import streamlit as st
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime


# =====================================================================
# DELTA 000 - מהקובץ PROGRAMIZ_DELTA_000_MASTER_KEY_STG.PY
# =====================================================================

def delta_000_parse_ddl(ddl):
    def norm(s): return s.strip().upper()
    tbl_match = re.search(r'CREATE\s+TABLE\s+(?:\[?\w+\]?\.)?\[?(\w+)\]?', ddl, re.IGNORECASE)
    if not tbl_match:
        raise ValueError("Cannot find table name")
    table_name = norm(tbl_match.group(1))
    body_match = re.search(r'\((.*)\)', ddl, re.DOTALL)
    if not body_match:
        raise ValueError("Cannot find table body")
    body = body_match.group(1)
    cols = []
    field_no = 1
    col_pattern = re.compile(
        r'\[(\w+)\]\s+\[(\w+)\](?:\(([^)]+)\))?\s*(IDENTITY[^,]*)?(NOT\s+NULL|NULL)?',
        re.IGNORECASE
    )
    for line in body.splitlines():
        line = line.strip().rstrip(',')
        m = col_pattern.match(line)
        if not m:
            continue
        col_name   = norm(m.group(1))
        base_type  = m.group(2).lower()
        precision_str = m.group(3) or ""
        nullable   = True if (m.group(5) or "NULL").strip().upper() == "NULL" else False
        if base_type in ("bigint",):
            type_sql = "bigint"
        elif base_type in ("int",):
            type_sql = "int"
        elif base_type in ("datetime",):
            type_sql = "datetime"
        elif base_type in ("date",):
            type_sql = "date"
        elif base_type in ("varchar","nvarchar"):
            p = precision_str.strip() if precision_str else "50"
            type_sql = f"varchar({p})"
        elif base_type in ("decimal","numeric"):
            ps = precision_str.strip() if precision_str else "18,0"
            type_sql = f"decimal({ps})"
        else:
            type_sql = f"varchar(50)"
        cols.append({"name": col_name, "type_sql": type_sql, "field_no": field_no, "nullable": nullable})
        field_no += 1
    return table_name, cols

def delta_000_src_meta(type_sql):
    t = type_sql.lower()
    if t.startswith("varchar"):
        p = int(re.search(r'\((\d+)', t).group(1)) if re.search(r'\((\d+)', t) else 50
        return {"DATATYPE":"varchar","LENGTH":"0","PRECISION":str(p),"SCALE":"0","PHYSICALLENGTH":str(p)}
    if t == "bigint":
        return {"DATATYPE":"bigint","LENGTH":"20","PRECISION":"19","SCALE":"0","PHYSICALLENGTH":"19"}
    if t == "int":
        return {"DATATYPE":"integer","LENGTH":"10","PRECISION":"10","SCALE":"0","PHYSICALLENGTH":"10"}
    if t.startswith("decimal"):
        m = re.search(r'\((\d+),\s*(\d+)', t)
        p, s = (int(m.group(1)), int(m.group(2))) if m else (18, 0)
        return {"DATATYPE":"decimal","LENGTH":str(p),"PRECISION":str(p),"SCALE":str(s),"PHYSICALLENGTH":str(p)}
    if t == "datetime":
        return {"DATATYPE":"datetime","LENGTH":"19","PRECISION":"23","SCALE":"3","PHYSICALLENGTH":"23"}
    if t == "date":
        return {"DATATYPE":"date","LENGTH":"10","PRECISION":"10","SCALE":"0","PHYSICALLENGTH":"10"}
    return {"DATATYPE":"varchar","LENGTH":"0","PRECISION":"50","SCALE":"0","PHYSICALLENGTH":"50"}

def delta_000_sq_meta(type_sql):
    t = type_sql.lower()
    if t.startswith("varchar"):
        p = int(re.search(r'\((\d+)', t).group(1)) if re.search(r'\((\d+)', t) else 50
        return {"DATATYPE":"string","PRECISION":str(p),"SCALE":"0"}
    if t == "bigint":
        return {"DATATYPE":"bigint","PRECISION":"19","SCALE":"0"}
    if t == "int":
        return {"DATATYPE":"integer","PRECISION":"10","SCALE":"0"}
    if t.startswith("decimal"):
        m = re.search(r'\((\d+),\s*(\d+)', t)
        p, s = (int(m.group(1)), int(m.group(2))) if m else (18, 0)
        return {"DATATYPE":"decimal","PRECISION":str(p),"SCALE":str(s)}
    if t in ("datetime","date"):
        return {"DATATYPE":"date/time","PRECISION":"29","SCALE":"9"}
    return {"DATATYPE":"string","PRECISION":"50","SCALE":"0"}

def add(parent, tag, **attrs):
    e = ET.SubElement(parent, tag)
    for k, v in attrs.items():
        e.set(k, str(v))
    return e

def conn(mp, ff, fi, fit, tf, ti, tit):
    add(mp, "CONNECTOR",
        FROMFIELD=ff, FROMINSTANCE=fi, FROMINSTANCETYPE=fit,
        TOFIELD=tf,   TOINSTANCE=ti,   TOINSTANCETYPE=tit)

def delta_000_build(table_name, cols, folder_name="DW_Drugs"):
    cfg = {
        "repo_name":"InfoDW_QA_Rep",
        "repo_version":"187",
        "codepage":"MS1255",
        "db_type":"Microsoft SQL Server",
        "folder_name": folder_name,
        "folder_owner":"Administrator",
        "folder_uuid":"620f71cd-f2d3-4541-9b90-9c08ea2afbf8",
        "dbdname":"dwh-dev",
        "ownername":"kfk",
        "target_suffix":"_KEY_STG",
        "mapping_prefix":"m_DELTA_000_",
        "sq_prefix":"SQ_",
    }
    def norm(s): return s.strip().upper()
    SRC   = table_name
    TGT   = norm(f"{table_name}{cfg['target_suffix']}")
    MNAME = f"{cfg['mapping_prefix']}{TGT}"
    SQ    = f"{cfg['sq_prefix']}{SRC}"
    E1    = "EXP_SRC"
    SRT   = "SRTTRANS"
    AGG   = "AGG"
    E2    = "EXPTRANS"
    EID   = "ENTITY_ID"
    TS    = "_DATA_TIMESTAMP_SEQUENCE"
    OFF   = "OFFSET"

    pm = ET.Element("POWERMART", CREATION_DATE=datetime.now().strftime("%m/%d/%Y %H:%M:%S"), REPOSITORY_VERSION="187.96")
    repo = add(pm, "REPOSITORY", NAME=cfg["repo_name"], VERSION=cfg["repo_version"], CODEPAGE=cfg["codepage"], DATABASETYPE=cfg["db_type"])
    fld  = add(repo, "FOLDER", NAME=cfg["folder_name"], GROUP="", OWNER=cfg["folder_owner"],
               SHARED="NOTSHARED", DESCRIPTION="", PERMISSIONS="rwx------", UUID=cfg["folder_uuid"])

    # SOURCE
    src_el = add(fld, "SOURCE", BUSINESSNAME="", DATABASETYPE=cfg["db_type"], DBDNAME=cfg["dbdname"],
                 DESCRIPTION="", NAME=SRC, OBJECTVERSION="1", OWNERNAME=cfg["ownername"], VERSIONNUMBER="2")
    lo, po = 0, 0
    for c in cols:
        m = delta_000_src_meta(c["type_sql"])
        add(src_el, "SOURCEFIELD", BUSINESSNAME="", DATATYPE=m["DATATYPE"], DESCRIPTION="",
            FIELDNUMBER=str(c["field_no"]), FIELDPROPERTY="0", FIELDTYPE="ELEMITEM", HIDDEN="NO",
            KEYTYPE="NOT A KEY", LENGTH=m["LENGTH"], LEVEL="0", NAME=c["name"],
            NULLABLE="NULL" if c["nullable"] else "NOTNULL", OCCURS="0",
            OFFSET=str(lo), PHYSICALLENGTH=m["PHYSICALLENGTH"], PHYSICALOFFSET=str(po),
            PICTURETEXT="", PRECISION=m["PRECISION"], SCALE=m["SCALE"], USAGE_FLAGS="")
        lo += 20
        po += int(m["PHYSICALLENGTH"])

    # TARGET
    tgt_el = add(fld, "TARGET", BUSINESSNAME="", CONSTRAINT="", DATABASETYPE=cfg["db_type"],
                 DESCRIPTION="", NAME=TGT, OBJECTVERSION="1", TABLEOPTIONS="", VERSIONNUMBER="2")
    add(tgt_el, "TARGETFIELD", BUSINESSNAME="", DATATYPE="varchar", DESCRIPTION="", FIELDNUMBER="1",
        KEYTYPE="PRIMARY KEY", NAME="ENTITY_ID", NULLABLE="NOTNULL", PICTURETEXT="", PRECISION="50", SCALE="0")
    add(tgt_el, "TARGETFIELD", BUSINESSNAME="", DATATYPE="varchar", DESCRIPTION="", FIELDNUMBER="2",
        KEYTYPE="NOT A KEY", NAME="timestamp_sequence", NULLABLE="NOTNULL", PICTURETEXT="", PRECISION="50", SCALE="0")
    add(tgt_el, "TARGETFIELD", BUSINESSNAME="", DATATYPE="bigint", DESCRIPTION="", FIELDNUMBER="3",
        KEYTYPE="NOT A KEY", NAME="OFFSET", NULLABLE="NULL", PICTURETEXT="", PRECISION="19", SCALE="0")
    add(tgt_el, "METADATAEXTENSION", DATATYPE="NUMERIC", DESCRIPTION="", DOMAINNAME="User Defined Metadata Domain",
        ISCLIENTEDITABLE="YES", ISCLIENTVISIBLE="YES", ISREUSABLE="NO", ISSHAREREAD="NO", ISSHAREWRITE="NO",
        MAXLENGTH="0", NAME="Extension", VALUE="", VENDORNAME="INFORMATICA")

    # MAPPING
    mp = add(fld, "MAPPING", DESCRIPTION="", ISVALID="YES", NAME=MNAME, OBJECTVERSION="1", VERSIONNUMBER="2")

    # EXP_SRC
    e1 = add(mp, "TRANSFORMATION", DESCRIPTION="", NAME=E1, OBJECTVERSION="1", REUSABLE="NO", TYPE="Expression", VERSIONNUMBER="2")
    add(e1, "TRANSFORMFIELD", DATATYPE="string", DEFAULTVALUE="", DESCRIPTION="", EXPRESSION=EID,
        EXPRESSIONTYPE="GENERAL", NAME=EID, PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION="50", SCALE="0")
    add(e1, "TRANSFORMFIELD", DATATYPE="date/time", DEFAULTVALUE="ERROR('transformation error')", DESCRIPTION="",
        EXPRESSION=f"TO_DATE(Concat( Concat(Substr({TS}_in, 1, 10), ' ' ) , Substr({TS}_in, 12, 8)), 'YYYY-MM-DD HH24:MI:SS')",
        EXPRESSIONTYPE="GENERAL", NAME=f"{TS}_out", PICTURETEXT="", PORTTYPE="OUTPUT", PRECISION="29", SCALE="9")
    add(e1, "TRANSFORMFIELD", DATATYPE="string", DEFAULTVALUE="", DESCRIPTION="", NAME=f"{TS}_in",
        PICTURETEXT="", PORTTYPE="INPUT", PRECISION="50", SCALE="0")
    add(e1, "TRANSFORMFIELD", DATATYPE="decimal", DEFAULTVALUE="", DESCRIPTION="", EXPRESSION=OFF,
        EXPRESSIONTYPE="GENERAL", NAME=OFF, PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION="19", SCALE="0")
    add(e1, "TABLEATTRIBUTE", NAME="Tracing Level", VALUE="Normal")

    # SRTTRANS
    sr = add(mp, "TRANSFORMATION", DESCRIPTION="", NAME=SRT, OBJECTVERSION="1", REUSABLE="NO", TYPE="Sorter", VERSIONNUMBER="2")
    add(sr, "TRANSFORMFIELD", DATATYPE="string", DEFAULTVALUE="", DESCRIPTION="", ISSORTKEY="YES",
        NAME=EID, PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION="50", SCALE="0", SORTDIRECTION="ASCENDING")
    add(sr, "TRANSFORMFIELD", DATATYPE="date/time", DEFAULTVALUE="", DESCRIPTION="", ISSORTKEY="YES",
        NAME=TS, PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION="29", SCALE="9", SORTDIRECTION="DESCENDING")
    add(sr, "TRANSFORMFIELD", DATATYPE="decimal", DEFAULTVALUE="", DESCRIPTION="", ISSORTKEY="YES",
        NAME=OFF, PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION="19", SCALE="0", SORTDIRECTION="DESCENDING")
    for n,v in [("Sorter Cache Size","Auto"),("Case Sensitive","YES"),("Work Directory","$PMTempDir"),
                ("Distinct","NO"),("Tracing Level","Normal"),("Null Treated Low","NO"),("Merge Only","NO"),
                ("Partitioning","Order records for individual partitions"),("Transformation Scope","All Input")]:
        add(sr, "TABLEATTRIBUTE", NAME=n, VALUE=v)

    # AGG
    ag = add(mp, "TRANSFORMATION", DESCRIPTION="", NAME=AGG, OBJECTVERSION="1", REUSABLE="NO", TYPE="Aggregator", VERSIONNUMBER="2")
    add(ag, "TRANSFORMFIELD", DATATYPE="string", DEFAULTVALUE="", DESCRIPTION="", EXPRESSION=EID,
        EXPRESSIONTYPE="GROUPBY", NAME=EID, PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION="50", SCALE="0")
    add(ag, "TRANSFORMFIELD", DATATYPE="date/time", DEFAULTVALUE="ERROR('transformation error')", DESCRIPTION="",
        EXPRESSION=f"first({TS}_in)", EXPRESSIONTYPE="GENERAL", NAME=f"{TS}_out", PICTURETEXT="", PORTTYPE="OUTPUT", PRECISION="29", SCALE="9")
    add(ag, "TRANSFORMFIELD", DATATYPE="date/time", DEFAULTVALUE="", DESCRIPTION="", NAME=f"{TS}_in",
        PICTURETEXT="", PORTTYPE="INPUT", PRECISION="29", SCALE="9")
    add(ag, "TRANSFORMFIELD", DATATYPE="decimal", DEFAULTVALUE="", DESCRIPTION="", NAME="OFFSET_IN",
        PICTURETEXT="", PORTTYPE="INPUT", PRECISION="19", SCALE="0")
    add(ag, "TRANSFORMFIELD", DATATYPE="decimal", DEFAULTVALUE="ERROR('transformation error')", DESCRIPTION="",
        EXPRESSION="first(OFFSET_IN)", EXPRESSIONTYPE="GENERAL", NAME="OFFSET_OUT", PICTURETEXT="", PORTTYPE="OUTPUT", PRECISION="19", SCALE="0")
    for n,v in [("Cache Directory","$PMCacheDir"),("Tracing Level","Normal"),("Sorted Input","YES"),
                ("Aggregator Data Cache Size","Auto"),("Aggregator Index Cache Size","Auto"),("Transformation Scope","All Input")]:
        add(ag, "TABLEATTRIBUTE", NAME=n, VALUE=v)

    # EXPTRANS
    e2 = add(mp, "TRANSFORMATION", DESCRIPTION="", NAME=E2, OBJECTVERSION="1", REUSABLE="NO", TYPE="Expression", VERSIONNUMBER="2")
    add(e2, "TRANSFORMFIELD", DATATYPE="string", DEFAULTVALUE="", DESCRIPTION="", EXPRESSION=EID,
        EXPRESSIONTYPE="GENERAL", NAME=EID, PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION="50", SCALE="0")
    add(e2, "TRANSFORMFIELD", DATATYPE="date/time", DEFAULTVALUE="", DESCRIPTION="", NAME=f"{TS}_IN",
        PICTURETEXT="", PORTTYPE="INPUT", PRECISION="29", SCALE="9")
    add(e2, "TRANSFORMFIELD", DATATYPE="string", DEFAULTVALUE="ERROR('transformation error')", DESCRIPTION="",
        EXPRESSION=f"Concat( Concat(Substr(TO_CHAR({TS}_IN, 'YYYY-MM-DD HH24:MI:SS'), 1, 10), 'T') , Substr(TO_CHAR({TS}_IN, 'YYYY-MM-DD HH24:MI:SS'), 12, 8))",
        EXPRESSIONTYPE="GENERAL", NAME=f"{TS}_OUT", PICTURETEXT="", PORTTYPE="OUTPUT", PRECISION="50", SCALE="0")
    add(e2, "TRANSFORMFIELD", DATATYPE="decimal", DEFAULTVALUE="", DESCRIPTION="", EXPRESSION="OFFSET_OUT",
        EXPRESSIONTYPE="GENERAL", NAME="OFFSET_OUT", PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION="19", SCALE="0")
    add(e2, "TABLEATTRIBUTE", NAME="Tracing Level", VALUE="Normal")

    # SQ
    sq = add(mp, "TRANSFORMATION", DESCRIPTION="", NAME=SQ, OBJECTVERSION="1", REUSABLE="NO", TYPE="Source Qualifier", VERSIONNUMBER="2")
    for c in cols:
        sm = delta_000_sq_meta(c["type_sql"])
        add(sq, "TRANSFORMFIELD", DATATYPE=sm["DATATYPE"], DEFAULTVALUE="", DESCRIPTION="", NAME=c["name"],
            PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION=sm["PRECISION"], SCALE=sm["SCALE"])
    add(sq, "TABLEATTRIBUTE", NAME="Sql Query", VALUE="")
    add(sq, "TABLEATTRIBUTE", NAME="User Defined Join", VALUE="")
    add(sq, "TABLEATTRIBUTE", NAME="Source Filter",
        VALUE=f"{SRC}.TRANSACTION_ID > $$TRANSACTION_ID AND {SRC}.ROW_CREATE_DATE < CONVERT(DATETIME, $$ROW_CREATE_DATE)")
    for n,v in [("Number Of Sorted Ports","0"),("Tracing Level","Normal"),("Select Distinct","NO"),
                ("Is Partitionable","NO"),("Pre SQL",""),("Post SQL",""),
                ("Output is deterministic","NO"),("Output is repeatable","Never")]:
        add(sq, "TABLEATTRIBUTE", NAME=n, VALUE=v)

    # INSTANCES
    add(mp, "INSTANCE", DESCRIPTION="", NAME=TGT, TRANSFORMATION_NAME=TGT, TRANSFORMATION_TYPE="Target Definition", TYPE="TARGET")
    add(mp, "INSTANCE", DBDNAME=cfg["dbdname"], DESCRIPTION="", NAME=SRC, TRANSFORMATION_NAME=SRC, TRANSFORMATION_TYPE="Source Definition", TYPE="SOURCE")
    add(mp, "INSTANCE", DESCRIPTION="", NAME=E1, REUSABLE="NO", TRANSFORMATION_NAME=E1, TRANSFORMATION_TYPE="Expression", TYPE="TRANSFORMATION")
    add(mp, "INSTANCE", DESCRIPTION="", NAME=E2, REUSABLE="NO", TRANSFORMATION_NAME=E2, TRANSFORMATION_TYPE="Expression", TYPE="TRANSFORMATION")
    add(mp, "INSTANCE", DESCRIPTION="", NAME=AGG, REUSABLE="NO", TRANSFORMATION_NAME=AGG, TRANSFORMATION_TYPE="Aggregator", TYPE="TRANSFORMATION")
    sq_inst = add(mp, "INSTANCE", DESCRIPTION="", NAME=SQ, REUSABLE="NO", TRANSFORMATION_NAME=SQ, TRANSFORMATION_TYPE="Source Qualifier", TYPE="TRANSFORMATION")
    add(sq_inst, "ASSOCIATED_SOURCE_INSTANCE", NAME=SRC)
    add(mp, "INSTANCE", DESCRIPTION="", NAME=SRT, REUSABLE="NO", TRANSFORMATION_NAME=SRT, TRANSFORMATION_TYPE="Sorter", TYPE="TRANSFORMATION")

    # CONNECTORS source -> SQ (all columns)
    for c in cols:
        conn(mp, c["name"], SRC, "Source Definition", c["name"], SQ, "Source Qualifier")

    # Fixed flow connectors
    conn(mp, EID,         SQ,  "Source Qualifier", EID,           E1,  "Expression")
    conn(mp, TS,          SQ,  "Source Qualifier", f"{TS}_in",    E1,  "Expression")
    conn(mp, OFF,         SQ,  "Source Qualifier", OFF,           E1,  "Expression")

    conn(mp, EID,         E1,  "Expression",       EID,           SRT, "Sorter")
    conn(mp, f"{TS}_out", E1,  "Expression",       TS,            SRT, "Sorter")
    conn(mp, OFF,         E1,  "Expression",       OFF,           SRT, "Sorter")

    conn(mp, EID,         SRT, "Sorter",           EID,           AGG, "Aggregator")
    conn(mp, TS,          SRT, "Sorter",           f"{TS}_in",    AGG, "Aggregator")
    conn(mp, OFF,         SRT, "Sorter",           "OFFSET_IN",   AGG, "Aggregator")

    conn(mp, EID,         AGG, "Aggregator",       EID,           E2,  "Expression")
    conn(mp, f"{TS}_out", AGG, "Aggregator",       f"{TS}_IN",    E2,  "Expression")
    conn(mp, "OFFSET_OUT",AGG, "Aggregator",       "OFFSET_OUT",  E2,  "Expression")

    conn(mp, EID,         E2,  "Expression",       "ENTITY_ID",         TGT, "Target Definition")
    conn(mp, f"{TS}_OUT", E2,  "Expression",       "timestamp_sequence", TGT, "Target Definition")
    conn(mp, "OFFSET_OUT",E2,  "Expression",       "OFFSET",            TGT, "Target Definition")

    add(mp, "TARGETLOADORDER", ORDER="1", TARGETINSTANCE=TGT)
    add(mp, "MAPPINGVARIABLE", DATATYPE="decimal", DEFAULTVALUE="", DESCRIPTION="", ISEXPRESSIONVARIABLE="NO",
        ISPARAM="YES", NAME="$$TRANSACTION_ID", PRECISION="19", SCALE="0", USERDEFINED="YES")
    add(mp, "MAPPINGVARIABLE", DATATYPE="string", DEFAULTVALUE="", DESCRIPTION="", ISEXPRESSIONVARIABLE="NO",
        ISPARAM="YES", NAME="$$ROW_CREATE_DATE", PRECISION="50", SCALE="0", USERDEFINED="YES")
    add(mp, "ERPINFO")

    return pm

def generate_delta_000(ddl_text, folder_name="DW_Drugs"):
    table_name, cols = delta_000_parse_ddl(ddl_text)
    root = delta_000_build(table_name, cols, folder_name=folder_name)
    body   = ET.tostring(root, encoding="unicode")
    pretty = minidom.parseString(body.encode("utf-8")).toprettyxml(indent="    ", encoding="utf-8").decode("utf-8")
    output = '<?xml version="1.0" encoding="windows-1255"?>\n<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">\n' + "\n".join(pretty.splitlines()[1:])
    return output


# =====================================================================
# DELTA 010 - מהקובץ PROGRAMIZ_DELTA_010_master_STG.py
# =====================================================================

def delta_010_parse_ddl(ddl):
    def norm(s): return s.strip().upper()
    tbl_match = re.search(r'CREATE\s+TABLE\s+(?:\[?\w+\]?\.)?\[?(\w+)\]?', ddl, re.IGNORECASE)
    if not tbl_match:
        raise ValueError("Cannot find table name")
    table_name = norm(tbl_match.group(1))
    body_match = re.search(r'\((.*)\)', ddl, re.DOTALL)
    if not body_match:
        raise ValueError("Cannot find table body")
    body = body_match.group(1)
    cols = []
    field_no = 1
    col_pattern = re.compile(
        r'\[(\w+)\]\s+\[(\w+)\](?:\(([^)]+)\))?\s*(IDENTITY[^,]*)?(NOT\s+NULL|NULL)?',
        re.IGNORECASE
    )
    for line in body.splitlines():
        line = line.strip().rstrip(',')
        m = col_pattern.match(line)
        if not m:
            continue
        col_name   = norm(m.group(1))
        base_type  = m.group(2).lower()
        precision_str = m.group(3) or ""
        nullable   = True if (m.group(5) or "NULL").strip().upper() == "NULL" else False
        if base_type in ("bigint",):
            type_sql = "bigint"
        elif base_type in ("int",):
            type_sql = "int"
        elif base_type in ("datetime",):
            type_sql = "datetime"
        elif base_type in ("date",):
            type_sql = "date"
        elif base_type in ("varchar","nvarchar"):
            p = precision_str.strip() if precision_str else "50"
            type_sql = f"varchar({p})"
        elif base_type in ("decimal","numeric"):
            ps = precision_str.strip() if precision_str else "18,0"
            type_sql = f"decimal({ps})"
        else:
            type_sql = f"varchar(50)"
        cols.append({"name": col_name, "type_sql": type_sql, "field_no": field_no, "nullable": nullable})
        field_no += 1
    return table_name, cols

def delta_010_src_meta(type_sql):
    t = type_sql.lower()
    if t.startswith("varchar"):
        p = int(re.search(r'\((\d+)', t).group(1)) if re.search(r'\((\d+)', t) else 50
        return {"inf_type":"varchar","physicallength":str(p),"precision":str(p),"scale":"0"}
    if t == "bigint":
        return {"inf_type":"bigint","physicallength":"8","precision":"19","scale":"0"}
    if t == "int" or t == "integer":
        return {"inf_type":"integer","physicallength":"4","precision":"10","scale":"0"}
    if t == "datetime":
        return {"inf_type":"datetime","physicallength":"8","precision":"23","scale":"3"}
    if t.startswith("decimal"):
        m = re.search(r'\((\d+),\s*(\d+)', t)
        p, s = (int(m.group(1)), int(m.group(2))) if m else (18, 0)
        return {"inf_type":"decimal","physicallength":str(p),"precision":str(p),"scale":str(s)}
    return {"inf_type":"varchar","physicallength":"50","precision":"50","scale":"0"}

def delta_010_sq_meta(type_sql):
    t = type_sql.lower()
    if t.startswith("varchar"):
        p = int(re.search(r'\((\d+)', t).group(1)) if re.search(r'\((\d+)', t) else 50
        return {"tf_type":"string","tf_precision":str(p),"tf_scale":"0"}
    if t == "bigint":
        return {"tf_type":"bigint","tf_precision":"19","tf_scale":"0"}
    if t == "int" or t == "integer":
        return {"tf_type":"integer","tf_precision":"10","tf_scale":"0"}
    if t == "datetime":
        return {"tf_type":"date/time","tf_precision":"29","tf_scale":"9"}
    if t.startswith("decimal"):
        m = re.search(r'\((\d+),\s*(\d+)', t)
        p, s = (int(m.group(1)), int(m.group(2))) if m else (18, 0)
        return {"tf_type":"decimal","tf_precision":str(p),"tf_scale":str(s)}
    return {"tf_type":"string","tf_precision":"50","tf_scale":"0"}

def delta_010_calc_offsets(fields):
    offset = 0
    result = []
    for f in fields:
        name, sql_type, length, nullable, keytype = f
        info = delta_010_src_meta(f"{sql_type}{f'({length})' if length else ''}")
        result.append((name, sql_type, length, nullable, keytype, info, offset))
        offset += int(info["physicallength"])
    return result

def xml_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")

def delta_010_build_xml(src1_name, src1_fields_raw, src2_name, src2_fields_raw, cfg):
    src1_fields = delta_010_calc_offsets(src1_fields_raw)
    src2_fields = delta_010_calc_offsets(src2_fields_raw)
    
    tgt_name = src1_name
    sq_name = "SQ_" + src1_name
    mapping_name = cfg["mapping_prefix"] + src1_name
    tgt_instance_name = tgt_name + "_target"
    
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">')
    
    now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    lines.append(f'<POWERMART CREATION_DATE="{now}" REPOSITORY_VERSION="187.96">')
    lines.append(f'  <REPOSITORY NAME="{cfg["repo_name"]}" VERSION="{cfg["repo_version"]}" CODEPAGE="{cfg["codepage"]}" DATABASETYPE="Microsoft SQL Server">')
    lines.append(f'    <FOLDER NAME="{cfg["folder_name"]}" OWNER="{cfg["folder_owner"]}" UUID="{cfg["folder_uuid"]}">')
    
    lines.append(f'      <SOURCE NAME="{src1_name}" DATABASETYPE="Microsoft SQL Server" DBDNAME="{cfg["src1_dbdname"]}" OWNERNAME="{cfg["src1_ownername"]}">')
    for i, (name, sql_type, length, nullable, keytype, info, phys_offset) in enumerate(src1_fields, 1):
        lines.append(f'        <SOURCEFIELD NAME="{name}" DATATYPE="{info["inf_type"]}" PHYSICALLENGTH="{info["physicallength"]}" PRECISION="{info["precision"]}" SCALE="{info["scale"]}" FIELDNUMBER="{i}" NULLABLE="{nullable}" PHYSICALOFFSET="{phys_offset}"/>')
    lines.append('      </SOURCE>')
    
    lines.append(f'      <SOURCE NAME="{src2_name}" DATABASETYPE="Microsoft SQL Server" DBDNAME="{cfg["src2_dbdname"]}" OWNERNAME="{cfg["src2_ownername"]}">')
    for i, (name, sql_type, length, nullable, keytype, info, phys_offset) in enumerate(src2_fields, 1):
        lines.append(f'        <SOURCEFIELD NAME="{name}" DATATYPE="{info["inf_type"]}" PHYSICALLENGTH="{info["physicallength"]}" PRECISION="{info["precision"]}" SCALE="{info["scale"]}" FIELDNUMBER="{i}" NULLABLE="{nullable}" PHYSICALOFFSET="{phys_offset}"/>')
    lines.append('      </SOURCE>')
    
    lines.append(f'      <TARGET NAME="{tgt_name}" DATABASETYPE="Microsoft SQL Server">')
    for i, (name, sql_type, length, nullable, keytype, info, _) in enumerate(src1_fields, 1):
        lines.append(f'        <TARGETFIELD NAME="{name}" DATATYPE="{info["inf_type"]}" FIELDNUMBER="{i}" NULLABLE="{nullable}" PRECISION="{info["precision"]}" SCALE="{info["scale"]}"/>')
    lines.append('      </TARGET>')
    
    lines.append(f'      <MAPPING NAME="{mapping_name}" DESCRIPTION="" ISVALID="YES" OBJECTVERSION="1" VERSIONNUMBER="1">')
    
    src1_names_lower = {f[0].lower() for f in src1_fields_raw}
    lines.append(f'        <TRANSFORMATION NAME="{sq_name}" TYPE="Source Qualifier" VERSIONNUMBER="1" REUSABLE="NO">')
    for name, sql_type, length, nullable, keytype, info, _ in src1_fields:
        sm = delta_010_sq_meta(f"{sql_type}{f'({length})' if length else ''}")
        lines.append(f'          <TRANSFORMFIELD NAME="{name}" DATATYPE="{sm["tf_type"]}" PRECISION="{sm["tf_precision"]}" SCALE="{sm["tf_scale"]}" PORTTYPE="INPUT/OUTPUT"/>')
    
    src2_sq_names = {}
    for name, sql_type, length, nullable, keytype, info, _ in src2_fields:
        sq_field_name = name + "1" if name.lower() in src1_names_lower else name
        src2_sq_names[name] = sq_field_name
        sm = delta_010_sq_meta(f"{sql_type}{f'({length})' if length else ''}")
        lines.append(f'          <TRANSFORMFIELD NAME="{sq_field_name}" DATATYPE="{sm["tf_type"]}" PRECISION="{sm["tf_precision"]}" SCALE="{sm["tf_scale"]}" PORTTYPE="INPUT/OUTPUT"/>')
    
    udj = (f'{src1_name}.entity_id={src2_name}.ENTITY_ID '
           f'and {src1_name}._data_timestamp_sequence={src2_name}.timestamp_sequence '
           f'AND {src1_name}.offset={src2_name}.OFFSET')
    lines.append(f'          <TABLEATTRIBUTE NAME="User Defined Join" VALUE="{xml_escape(udj)}"/>')
    lines.append(f'        </TRANSFORMATION>')
    
    lines.append(f'        <TRANSFORMATION DESCRIPTION="" NAME="RNKTRANS" OBJECTVERSION="1" REUSABLE="NO" TYPE="Rank" VERSIONNUMBER="1">')
    lines.append('          <TRANSFORMFIELD DATATYPE="integer" DEFAULTVALUE="ERROR(\'transformation error\')" EXPRESSION="RANKINDEX" EXPRESSIONTYPE="RANKINDEX" NAME="RANKINDEX" PORTTYPE="OUTPUT" PRECISION="10" SCALE="0"/>')
    lines.append('          <TRANSFORMFIELD DATATYPE="bigint" EXPRESSION="TRANSACTION_ID" EXPRESSIONTYPE="RANKPORT" NAME="TRANSACTION_ID" PORTTYPE="INPUT/OUTPUT" PRECISION="19" SCALE="0"/>')
    for name, sql_type, length, nullable, keytype, info, _ in src1_fields:
        if name == "TRANSACTION_ID":
            continue
        sm = delta_010_sq_meta(f"{sql_type}{f'({length})' if length else ''}")
        expr_type = "GENERAL" if sm["tf_type"] == "date/time" else "GROUPBY"
        lines.append(f'          <TRANSFORMFIELD DATATYPE="{sm["tf_type"]}" EXPRESSION="{name}" EXPRESSIONTYPE="{expr_type}" NAME="{name}" PORTTYPE="INPUT/OUTPUT" PRECISION="{sm["tf_precision"]}" SCALE="{sm["tf_scale"]}"/>')
    for n,v in [("Top/Bottom","Top"),("Number of Ranks","1")]:
        lines.append(f'          <TABLEATTRIBUTE NAME="{n}" VALUE="{v}"/>')
    lines.append(f'        </TRANSFORMATION>')
    
    lines.append(f'        <TRANSFORMATION DESCRIPTION="" NAME="EXP_SRC" OBJECTVERSION="1" REUSABLE="NO" TYPE="Expression" VERSIONNUMBER="1">')
    for name, sql_type, length, nullable, keytype, info, _ in src1_fields:
        sm = delta_010_sq_meta(f"{sql_type}{f'({length})' if length else ''}")
        lines.append(f'          <TRANSFORMFIELD DATATYPE="{sm["tf_type"]}" EXPRESSION="{name}" EXPRESSIONTYPE="GENERAL" NAME="{name}" PORTTYPE="INPUT/OUTPUT" PRECISION="{sm["tf_precision"]}" SCALE="{sm["tf_scale"]}"/>')
    lines.append(f'        </TRANSFORMATION>')
    
    lines.append(f'        <INSTANCE DESCRIPTION="" NAME="{tgt_instance_name}" TRANSFORMATION_NAME="{tgt_name}" TRANSFORMATION_TYPE="Target Definition" TYPE="TARGET"/>')
    lines.append(f'        <INSTANCE DBDNAME="{cfg["src1_dbdname"]}" DESCRIPTION="" NAME="{src1_name}" TRANSFORMATION_NAME="{src1_name}" TRANSFORMATION_TYPE="Source Definition" TYPE="SOURCE"/>')
    lines.append(f'        <INSTANCE DBDNAME="{cfg["src2_dbdname"]}" DESCRIPTION="" NAME="{src2_name}" TRANSFORMATION_NAME="{src2_name}" TRANSFORMATION_TYPE="Source Definition" TYPE="SOURCE"/>')
    lines.append(f'        <INSTANCE DESCRIPTION="" NAME="{sq_name}" REUSABLE="NO" TRANSFORMATION_NAME="{sq_name}" TRANSFORMATION_TYPE="Source Qualifier" TYPE="TRANSFORMATION">')
    lines.append(f'          <ASSOCIATED_SOURCE_INSTANCE NAME="{src1_name}"/>')
    lines.append(f'          <ASSOCIATED_SOURCE_INSTANCE NAME="{src2_name}"/>')
    lines.append(f'        </INSTANCE>')
    lines.append('        <INSTANCE DESCRIPTION="" NAME="RNKTRANS" REUSABLE="NO" TRANSFORMATION_NAME="RNKTRANS" TRANSFORMATION_TYPE="Rank" TYPE="TRANSFORMATION"/>')
    lines.append('        <INSTANCE DESCRIPTION="" NAME="EXP_SRC" REUSABLE="NO" TRANSFORMATION_NAME="EXP_SRC" TRANSFORMATION_TYPE="Expression" TYPE="TRANSFORMATION"/>')
    
    for name, *_ in src1_fields_raw:
        lines.append(f'        <CONNECTOR FROMFIELD="{name}" FROMINSTANCE="{src1_name}" FROMINSTANCETYPE="Source Definition" TOFIELD="{name}" TOINSTANCE="{sq_name}" TOINSTANCETYPE="Source Qualifier"/>')
    
    for name, *_ in src2_fields_raw:
        to_field = src2_sq_names[name]
        lines.append(f'        <CONNECTOR FROMFIELD="{name}" FROMINSTANCE="{src2_name}" FROMINSTANCETYPE="Source Definition" TOFIELD="{to_field}" TOINSTANCE="{sq_name}" TOINSTANCETYPE="Source Qualifier"/>')
    
    for name, *_ in src1_fields_raw:
        lines.append(f'        <CONNECTOR FROMFIELD="{name}" FROMINSTANCE="{sq_name}" FROMINSTANCETYPE="Source Qualifier" TOFIELD="{name}" TOINSTANCE="RNKTRANS" TOINSTANCETYPE="Rank"/>')
    
    for name, *_ in src1_fields_raw:
        lines.append(f'        <CONNECTOR FROMFIELD="{name}" FROMINSTANCE="RNKTRANS" FROMINSTANCETYPE="Rank" TOFIELD="{name}" TOINSTANCE="EXP_SRC" TOINSTANCETYPE="Expression"/>')
    
    for name, *_ in src1_fields_raw:
        lines.append(f'        <CONNECTOR FROMFIELD="{name}" FROMINSTANCE="EXP_SRC" FROMINSTANCETYPE="Expression" TOFIELD="{name}" TOINSTANCE="{tgt_instance_name}" TOINSTANCETYPE="Target Definition"/>')
    
    lines.append(f'        <TARGETLOADORDER ORDER="1" TARGETINSTANCE="{tgt_instance_name}"/>')
    lines.append('        <ERPINFO/>')
    lines.append('      </MAPPING>')
    lines.append('    </FOLDER>')
    lines.append('  </REPOSITORY>')
    lines.append('</POWERMART>')
    
    return "\n".join(lines)

def generate_delta_010(ddl_text, folder_name="DW_Drugs"):
    cfg = {
        "repo_name": "InfoDW_QA_Rep",
        "repo_version": "187",
        "codepage": "MS1255",
        "folder_name": folder_name,
        "folder_owner": "Administrator",
        "folder_uuid": "620f71cd-f2d3-4541-9b90-9c08ea2afbf8",
        "src1_dbdname": "dwh-dev",
        "src1_ownername": "kfk",
        "src2_dbdname": "dwh-dev",
        "src2_ownername": "dbo",
        "mapping_prefix": "m_DELTA_010_",
    }
    
    table_name, cols = delta_010_parse_ddl(ddl_text)
    src1_name = table_name + "_STG"
    src2_name = table_name + "_KEY_STG"
    
    # SOURCE1 FIELDS
    src1_fields_raw = [(c["name"], c["type_sql"].split("(")[0], c["type_sql"].split("(")[1].rstrip(")") if "(" in c["type_sql"] else "", "NULL" if c["nullable"] else "NOTNULL", "NOT A KEY") for c in cols]
    
    # SOURCE2 FIELDS - hardcoded
    src2_fields_raw = [
        ("ENTITY_ID",           "varchar", "50", "NOTNULL", "PRIMARY KEY"),
        ("timestamp_sequence",  "varchar", "50", "NOTNULL", "NOT A KEY"),
        ("OFFSET",              "varchar", "50", "NULL",    "NOT A KEY"),
    ]
    
    return delta_010_build_xml(src1_name, src1_fields_raw, src2_name, src2_fields_raw, cfg)


# =====================================================================
# DELTA 020 + 030 - לוגיקה מלאה מהקבצים העובדים
# =====================================================================

def _parse_ddl_for_delta(ddl):
    tbl_match = re.search(r'CREATE\s+TABLE\s+(?:\[?\w+\]?\.)?\[?(\w+)\]?', ddl, re.IGNORECASE)
    if not tbl_match:
        raise ValueError("Cannot find table name")
    table_name = tbl_match.group(1)

    body_match = re.search(r'\((.*)\)', ddl, re.DOTALL)
    if not body_match:
        raise ValueError("Cannot find table body")
    body = body_match.group(1)

    cols = []
    field_no = 1
    col_pattern = re.compile(
        r'\[(\w+)\]\s+\[(\w+)\](?:\(([^)]+)\))?\s*(IDENTITY[^,]*)?(NOT\s+NULL|NULL)?',
        re.IGNORECASE
    )
    for line in body.splitlines():
        line = line.strip().rstrip(',')
        m = col_pattern.match(line)
        if not m:
            continue

        col_name = m.group(1)
        base_type = m.group(2).lower()
        precision_str = m.group(3) or ""
        nullable = True if (m.group(5) or "NULL").strip().upper() == "NULL" else False

        if base_type in ("bigint",):
            type_sql = "bigint"
        elif base_type in ("int",):
            type_sql = "int"
        elif base_type in ("datetime",):
            type_sql = "datetime"
        elif base_type in ("date",):
            type_sql = "date"
        elif base_type in ("varchar", "nvarchar"):
            p = precision_str.strip() if precision_str else "50"
            type_sql = f"varchar({p})"
        elif base_type in ("decimal", "numeric"):
            ps = precision_str.strip() if precision_str else "18,0"
            type_sql = f"decimal({ps})"
        else:
            type_sql = "varchar(50)"

        cols.append({"name": col_name, "type_sql": type_sql, "field_no": field_no, "nullable": nullable})
        field_no += 1

    return table_name, cols


def _parse_all_ddl_blocks(ddl_text):
    block_re = re.compile(
        r'CREATE\s+TABLE\s+(?:\[?\w+\]?\.)?\[?(\w+)\]?\s*\((.*?)\)\s*(?=CREATE\s+TABLE|$)',
        re.IGNORECASE | re.DOTALL,
    )
    col_pattern = re.compile(
        r'\[(\w+)\]\s+\[(\w+)\](?:\(([^)]+)\))?\s*(IDENTITY[^,]*)?(NOT\s+NULL|NULL)?',
        re.IGNORECASE,
    )

    blocks = []
    for m in block_re.finditer(ddl_text):
        table_name = m.group(1)
        body = m.group(2)
        cols = []
        field_no = 1
        for line in body.splitlines():
            line = line.strip().rstrip(',')
            cm = col_pattern.match(line)
            if not cm:
                continue

            col_name = cm.group(1)
            base_type = cm.group(2).lower()
            precision_str = cm.group(3) or ""
            nullable = True if (cm.group(5) or "NULL").strip().upper() == "NULL" else False

            if base_type in ("bigint",):
                type_sql = "bigint"
            elif base_type in ("int",):
                type_sql = "int"
            elif base_type in ("datetime",):
                type_sql = "datetime"
            elif base_type in ("date",):
                type_sql = "date"
            elif base_type in ("varchar", "nvarchar"):
                p = precision_str.strip() if precision_str else "50"
                type_sql = f"varchar({p})"
            elif base_type in ("decimal", "numeric"):
                ps = precision_str.strip() if precision_str else "18,0"
                type_sql = f"decimal({ps})"
            else:
                type_sql = "varchar(50)"

            cols.append({"name": col_name, "type_sql": type_sql, "field_no": field_no, "nullable": nullable})
            field_no += 1

        blocks.append((table_name, cols))
    return blocks


def _render_powermart_xml(root):
    body = ET.tostring(root, encoding="unicode")
    pretty = minidom.parseString(body.encode("utf-8")).toprettyxml(indent="    ", encoding="utf-8").decode("utf-8")
    return '<?xml version="1.0" encoding="windows-1255"?>\n<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">\n' + "\n".join(pretty.splitlines()[1:])


def _pick_col(cols, default_name):
    for c in cols:
        if c["name"].lower() == default_name.lower():
            return c["name"]
    return default_name


def _build_source(parent, source_name, dbdname, ownername, cols):
    src_el = add(parent, "SOURCE", BUSINESSNAME="", DATABASETYPE="Microsoft SQL Server", DBDNAME=dbdname,
                 DESCRIPTION="", NAME=source_name, OBJECTVERSION="1", OWNERNAME=ownername, VERSIONNUMBER="1")
    po = 0
    for i, c in enumerate(cols, 1):
        m = delta_000_src_meta(c["type_sql"])
        add(src_el, "SOURCEFIELD", BUSINESSNAME="", DATATYPE=m["DATATYPE"], DESCRIPTION="", FIELDNUMBER=str(i),
            FIELDPROPERTY="0", FIELDTYPE="ELEMITEM", HIDDEN="NO", KEYTYPE="NOT A KEY", LENGTH=m["LENGTH"],
            LEVEL="0", NAME=c["name"], NULLABLE="NULL" if c["nullable"] else "NOTNULL", OCCURS="0", OFFSET="0",
            PHYSICALLENGTH=m["PHYSICALLENGTH"], PHYSICALOFFSET=str(po), PICTURETEXT="", PRECISION=m["PRECISION"],
            SCALE=m["SCALE"], USAGE_FLAGS="")
        po += int(m["PHYSICALLENGTH"])


def _build_target(parent, target_name, cols):
    tgt_el = add(parent, "TARGET", BUSINESSNAME="", CONSTRAINT="", DATABASETYPE="Microsoft SQL Server",
                 DESCRIPTION="", NAME=target_name, OBJECTVERSION="1", TABLEOPTIONS="", VERSIONNUMBER="1")
    for i, c in enumerate(cols, 1):
        m = delta_000_src_meta(c["type_sql"])
        add(tgt_el, "TARGETFIELD", BUSINESSNAME="", DATATYPE=m["DATATYPE"], DESCRIPTION="", FIELDNUMBER=str(i),
            KEYTYPE="NOT A KEY", NAME=c["name"], NULLABLE="NULL" if c["nullable"] else "NOTNULL", PICTURETEXT="",
            PRECISION=m["PRECISION"], SCALE=m["SCALE"])


def _build_two_source_delta_mapping(fld, *, mapping_name, src1_name, src1_cols, src2_name, src2_cols, target_name, source_filter=None):
    sq_name = f"SQ_{src1_name}"
    exp_name = "EXP_Transform"

    s1_entity_id = _pick_col(src1_cols, "entity_id")
    s1_ts = _pick_col(src1_cols, "_data_timestamp_sequence")
    s1_offset = _pick_col(src1_cols, "offset")

    s2_entity_id = _pick_col(src2_cols, "entity_id")
    s2_ts = _pick_col(src2_cols, "_data_timestamp_sequence")
    s2_offset = _pick_col(src2_cols, "offset")
    s2_trans_id = _pick_col(src2_cols, "TRANSACTION_ID")
    s2_entity_type = _pick_col(src2_cols, "entity_type")

    mp = add(fld, "MAPPING", DESCRIPTION="", ISVALID="YES", NAME=mapping_name, OBJECTVERSION="1", VERSIONNUMBER="1")

    sq = add(mp, "TRANSFORMATION", DESCRIPTION="", NAME=sq_name, OBJECTVERSION="1", REUSABLE="NO", TYPE="Source Qualifier", VERSIONNUMBER="1")
    for c in src1_cols:
        sm = delta_000_sq_meta(c["type_sql"])
        add(sq, "TRANSFORMFIELD", DATATYPE=sm["DATATYPE"], DEFAULTVALUE="", DESCRIPTION="", NAME=c["name"],
            PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION=sm["PRECISION"], SCALE=sm["SCALE"])
    add(sq, "TRANSFORMFIELD", DATATYPE="string", DEFAULTVALUE="", DESCRIPTION="", NAME="entity_type_current",
        PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION="50", SCALE="0")

    join_value = (
        f"{src1_name}.{s1_entity_id} = {src2_name}.{s2_entity_id} "
        f"AND {src1_name}.{s1_ts} < {src2_name}.{s2_ts} "
        f"AND {src1_name}.{s1_offset} < {src2_name}.{s2_offset} "
        f"AND {src2_name}.{s2_trans_id} <= $$TRANSACTION_ID"
    )
    add(sq, "TABLEATTRIBUTE", NAME="Sql Query", VALUE="")
    add(sq, "TABLEATTRIBUTE", NAME="User Defined Join", VALUE=join_value)
    sf = source_filter if source_filter is not None else f"{src2_name}.{s2_trans_id} is null"
    add(sq, "TABLEATTRIBUTE", NAME="Source Filter", VALUE=sf)
    for n, v in [("Number Of Sorted Ports", "0"), ("Tracing Level", "Normal"), ("Select Distinct", "NO"),
                 ("Is Partitionable", "NO"), ("Pre SQL", ""), ("Post SQL", ""),
                 ("Output is deterministic", "NO"), ("Output is repeatable", "Never")]:
        add(sq, "TABLEATTRIBUTE", NAME=n, VALUE=v)

    exp = add(mp, "TRANSFORMATION", DESCRIPTION="", NAME=exp_name, OBJECTVERSION="1", REUSABLE="NO", TYPE="Expression", VERSIONNUMBER="1")
    for c in src1_cols:
        sm = delta_000_sq_meta(c["type_sql"])
        add(exp, "TRANSFORMFIELD", DATATYPE=sm["DATATYPE"], DEFAULTVALUE="", DESCRIPTION="", EXPRESSION=c["name"],
            EXPRESSIONTYPE="GENERAL", NAME=c["name"], PICTURETEXT="", PORTTYPE="INPUT/OUTPUT",
            PRECISION=sm["PRECISION"], SCALE=sm["SCALE"])

    add(mp, "INSTANCE", DBDNAME="dwh-dev", DESCRIPTION="", NAME=src1_name, TRANSFORMATION_NAME=src1_name,
        TRANSFORMATION_TYPE="Source Definition", TYPE="SOURCE")
    add(mp, "INSTANCE", DBDNAME="dwh-dev", DESCRIPTION="", NAME=src2_name, TRANSFORMATION_NAME=src2_name,
        TRANSFORMATION_TYPE="Source Definition", TYPE="SOURCE")
    add(mp, "INSTANCE", DESCRIPTION="", NAME=target_name, TRANSFORMATION_NAME=target_name,
        TRANSFORMATION_TYPE="Target Definition", TYPE="TARGET")
    sq_inst = add(mp, "INSTANCE", DESCRIPTION="", NAME=sq_name, REUSABLE="NO", TRANSFORMATION_NAME=sq_name,
                  TRANSFORMATION_TYPE="Source Qualifier", TYPE="TRANSFORMATION")
    add(sq_inst, "ASSOCIATED_SOURCE_INSTANCE", NAME=src1_name)
    add(sq_inst, "ASSOCIATED_SOURCE_INSTANCE", NAME=src2_name)
    add(mp, "INSTANCE", DESCRIPTION="", NAME=exp_name, REUSABLE="NO", TRANSFORMATION_NAME=exp_name,
        TRANSFORMATION_TYPE="Expression", TYPE="TRANSFORMATION")

    for c in src1_cols:
        conn(mp, c["name"], src1_name, "Source Definition", c["name"], sq_name, "Source Qualifier")
    conn(mp, s2_entity_type, src2_name, "Source Definition", "entity_type_current", sq_name, "Source Qualifier")
    for c in src1_cols:
        conn(mp, c["name"], sq_name, "Source Qualifier", c["name"], exp_name, "Expression")
    for c in src1_cols:
        conn(mp, c["name"], exp_name, "Expression", c["name"], target_name, "Target Definition")

    add(mp, "TARGETLOADORDER", ORDER="1", TARGETINSTANCE=target_name)
    add(mp, "MAPPINGVARIABLE", DATATYPE="bigint", DEFAULTVALUE="0", DESCRIPTION="Transaction ID Parameter",
        ISEXPRESSIONVARIABLE="NO", ISPARAM="YES", NAME="$$TRANSACTION_ID", PRECISION="19", SCALE="0", USERDEFINED="YES")
    add(mp, "ERPINFO")

def generate_delta_020(ddl_text, folder_name="DW_Drugs"):
    try:
        table_name, cols = _parse_ddl_for_delta(ddl_text)
        is_stg_input = table_name.lower().endswith("_stg")
        base_name = table_name[:-4] if is_stg_input else table_name
        src1_name = table_name if is_stg_input else f"{table_name}_stg"
        src2_name = base_name
        target_name = f"{base_name}_CLN"
        mapping_name = f"m_DELTA_020_{base_name}_MASTER_CLN"

        # ב-020 מקור ה-MASTER צריך להכיל את אותו סט שדות מלא של ה-DDL.
        src2_cols = [
            {
                "name": c["name"],
                "type_sql": c["type_sql"],
                "field_no": i,
                "nullable": c["nullable"],
            }
            for i, c in enumerate(cols, 1)
        ]

        pm = ET.Element("POWERMART", CREATION_DATE=datetime.now().strftime("%m/%d/%Y %H:%M:%S"), REPOSITORY_VERSION="187.96")
        repo = add(pm, "REPOSITORY", NAME="InfoDW_QA_Rep", VERSION="187", CODEPAGE="MS1255", DATABASETYPE="Microsoft SQL Server")
        fld = add(repo, "FOLDER", NAME=folder_name, GROUP="", OWNER="Administrator", SHARED="NOTSHARED",
                  DESCRIPTION="", PERMISSIONS="rwx------", UUID="620f71cd-f2d3-4541-9b90-9c08ea2afbf8")

        _build_source(fld, src1_name, "dwh-dev", "delta", cols)
        _build_source(fld, src2_name, "dwh-dev", "KFK", src2_cols)
        _build_target(fld, target_name, cols)
        _build_two_source_delta_mapping(
            fld,
            mapping_name=mapping_name,
            src1_name=src1_name,
            src1_cols=cols,
            src2_name=src2_name,
            src2_cols=src2_cols,
            target_name=target_name,
            source_filter=f"{src2_name}.TRANSACTION_ID is null",
        )

        return _render_powermart_xml(pm)
    except Exception as e:
        return f"<!-- DELTA 020 - ERROR: {e} -->"
    

def generate_delta_030(ddl_text, folder_name="DW_Drugs"):
    try:
        blocks = _parse_all_ddl_blocks(ddl_text)
        if not blocks:
            table_name, cols = _parse_ddl_for_delta(ddl_text)
            blocks = [(table_name, cols)]

        detail_block = None
        master_block = None
        for tname, tcols in blocks:
            ln = tname.lower()
            if detail_block is None and ("detail" in ln or "communication" in ln):
                detail_block = (tname, tcols)
            if master_block is None and "master" in ln:
                master_block = (tname, tcols)

        if detail_block is None:
            detail_block = blocks[0]
        if master_block is None:
            master_block = blocks[1] if len(blocks) > 1 else ("member_demographic_master_cln", [
                {"name": "TRANSACTION_ID", "type_sql": "bigint", "field_no": 1, "nullable": False},
                {"name": "entity_id", "type_sql": "varchar(50)", "field_no": 2, "nullable": True},
                {"name": "entity_type", "type_sql": "varchar(50)", "field_no": 3, "nullable": True},
                {"name": "_data_timestamp_sequence", "type_sql": "varchar(50)", "field_no": 4, "nullable": True},
                {"name": "offset", "type_sql": "bigint", "field_no": 5, "nullable": True},
            ])

        detail_name, cols = detail_block
        master_name, src2_cols = master_block

        src1_name = detail_name
        if src1_name.lower().endswith("_stg"):
            base_name = src1_name[:-4]
        elif src1_name.lower().endswith("_cln"):
            base_name = src1_name[:-4]
        else:
            base_name = src1_name

        src2_name = master_name
        target_name = f"{base_name}_CLN"
        mapping_name = f"m_DELTA_030_{base_name}_cln"

        pm = ET.Element("POWERMART", CREATION_DATE=datetime.now().strftime("%m/%d/%Y %H:%M:%S"), REPOSITORY_VERSION="187.96")
        repo = add(pm, "REPOSITORY", NAME="InfoDW_QA_Rep", VERSION="187", CODEPAGE="MS1255", DATABASETYPE="Microsoft SQL Server")
        fld = add(repo, "FOLDER", NAME=folder_name, GROUP="", OWNER="Administrator", SHARED="NOTSHARED",
                  DESCRIPTION="", PERMISSIONS="rwx------", UUID="620f71cd-f2d3-4541-9b90-9c08ea2afbf8")

        _build_source(fld, src1_name, "dwh-dev", "kfk", cols)
        _build_source(fld, src2_name, "dwh-dev", "KFK", src2_cols)
        _build_target(fld, target_name, cols)
        _build_two_source_delta_mapping(
            fld,
            mapping_name=mapping_name,
            src1_name=src1_name,
            src1_cols=cols,
            src2_name=src2_name,
            src2_cols=src2_cols,
            target_name=target_name,
            source_filter=f"{src2_name}.TRANSACTION_ID is null",
        )

        return _render_powermart_xml(pm)
    except Exception as e:
        return f"<!-- DELTA 030 - ERROR: {e} -->"


# =====================================================================
# STREAMLIT UI
# =====================================================================

# =====================================================================
# STREAMLIT UI - הגרסה המשודרגת והמעוצבת
# =====================================================================

def main():
    # הגדרת פריסה רחבה ומודרנית
    st.set_page_config(page_title="Informatica XML Generator", layout="wide", page_icon="🔧")
    
    # הזרקת CSS מותאם אישית ליישור RTL מלא ועיצוב כפתורים מרשים
    st.markdown("""
    <style>
    /* יישור כללי לימין ותמיכה ב-RTL */
    .main * {
        direction: rtl;
        text-align: right;
    }
    /* תיקון ספציפי לתיבות קוד וטקסט באנגלית שחייבות להישאר LTR */
    div[data-baseweb="textarea"] textarea, pre, code {
        direction: ltr !important;
        text-align: left !important;
        font-family: 'Courier New', Courier, monospace !important;
    }
    /* עיצוב כותרת ראשית */
    .main-title {
        color: #1E3A8A;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        margin-bottom: 5px;
    }
    /* עיצוב הלשוניות (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # כותרת ראשית ממותגת
    st.markdown("<h1 class='main-title'>🔧 מחולל מפות Informatica PowerCenter</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; font-size: 16px;'>כלי אוטומטי לצוות הפיתוח לייצור קבצי XML מתוך סקריפטי SQL CREATE TABLE.</p>", unsafe_allow_html=True)
    st.divider()
    
    # 1. שימוש בלשוניות (Tabs) מעוצבות עם אמוג'ים במקום כפתורי רדיו
    tab_labels = [
        "🔑 DELTA 000 (Master Key STG)", 
        "📊 DELTA 010 (Master STG)", 
        "🧹 DELTA 020 (Master CLN)", 
        "📋 DELTA 030 (Detail CLN)"
    ]
    selected_tab = st.tabs(tab_labels)
    
    # נמפה את הלשונית הנבחרת למשתנה קריא
    delta_stage = ""
    
    # 2. חלוקת המסך לטורים (Columns) - פריסה ויזואלית חכמה
    col_input, col_settings = st.columns([2, 1], gap="large")
    
    with col_input:
        st.markdown("### 📥 קלט: סקריפט SQL DDL")
        ddl_input = st.text_area(
            "הדבק כאן את קוד ה-CREATE TABLE הארגוני:",
            height=300,
            placeholder="CREATE TABLE [dbo].[MyTable] (\n   [ENTITY_ID] [varchar](50) NOT NULL,\n   ...\n)",
            key="ddl_input"
        )
        
    with col_settings:
        st.markdown("### ⚙️ הגדרות והרצה")
        
        # מיכל סגור להגדרות התיקייה
        with st.container(border=True):
            folder_name = st.text_input(
                "שם ה-FOLDER באינפורמטיקה:",
                value="DW_Drugs",
                key="folder_name_input"
            ).strip() or "DW_Drugs"
            
            st.caption("💡 ודא ששם התיקייה תואם במדויק לסביבת העבודה שלך ב-Repository.")

        st.space = st.empty() # מרווח ויזואלי
        st.markdown("<br>", unsafe_allow_html=True)
        
        # כפתור הפעלה גדול ובולט
        generate_clicked = st.button("✨ ייצר מפת XML עכשיו", use_container_width=True, type="primary")

    # זיהוי איזה לשונית פתוחה כעת כדי להעביר לפונקציה המתאימה
    for idx, tab in enumerate(selected_tab):
        with tab:
            delta_stage = tab_labels[idx]

    # לוגיקת ההפעלה בעת לחיצה
    if generate_clicked:
        if not ddl_input.strip():
            st.error("❌ לא נמצא קוד SQL. אנא הדבק סקריפט CREATE TABLE בתיבת הקלט.")
        else:
            with st.spinner("⏳ מנתח DDL ומייצר מבנה XML... אנא המתן"):
                try:
                    # חילוץ מזהה השלב מתוך מחרוזת הלשונית
                    if "DELTA 000" in delta_stage:
                        xml_content = generate_delta_000(ddl_input, folder_name=folder_name)
                        file_suffix = "000_Master_Key_STG"
                    elif "DELTA 010" in delta_stage:
                        xml_content = generate_delta_010(ddl_input, folder_name=folder_name)
                        file_suffix = "010_Master_STG"
                    elif "DELTA 020" in delta_stage:
                        xml_content = generate_delta_020(ddl_input, folder_name=folder_name)
                        file_suffix = "020_Master_CLN"
                    else:
                        xml_content = generate_delta_030(ddl_input, folder_name=folder_name)
                        file_suffix = "030_Detail_CLN"
                    
                    st.session_state.xml_content = xml_content
                    st.session_state.file_suffix = file_suffix
                    st.success("✅ ה-XML נוצר בהצלחה ובאופן תקין!")
                except Exception as e:
                    st.error(f"❌ שגיאה בעיבוד ה-DDL: {str(e)}")
                    st.info("💡 ודא שפורמט ה-CREATE TABLE תואם לציפיות הסקריפט (שימוש בסוגריים מרובעים כמקובל ב-SQL Server).")
    
    # 3. תצוגת פלט מעוצבת ונגישה להורדה
    if "xml_content" in st.session_state and st.session_state.xml_content:
        st.divider()
        
        st.markdown(f"### 📄 פלט מוכן: {st.session_state.file_suffix}")
        
        # כפתור הורדה ענקי בצבע ירוק (Secondary מוצלח ב-Streamlit)
        st.download_button(
            label="📥 לחץ כאן להורדת קובץ ה-XML המוכן לאינפורמטיקה",
            data=st.session_state.xml_content,
            file_name=f"m_DELTA_{st.session_state.file_suffix}.xml",
            mime="application/xml",
            use_container_width=True
        )
        
        # אקורדיון סגור לצפייה בקוד במידת הצורך, שלא יתפוס נפח ויזואלי
        with st.expander("🔍 הצג תצוגה מקדימה של קוד ה-XML", expanded=False):
            st.code(st.session_state.xml_content, language="xml")


if __name__ == "__main__":
    main()
