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
    # Split by CREATE TABLE (preserving it at start of each part)
    parts = re.split(r'(?=CREATE\s+TABLE)', ddl_text, flags=re.IGNORECASE)
    
    # Now extract table name and columns from each part
    block_re = re.compile(
        r'CREATE\s+TABLE\s+(?:\[?\w+\]?\.)?\[?(\w+)\]?\s*\(([\s\S]*?)\)\s*(?=ON|;|GO|$)',
        re.IGNORECASE | re.DOTALL,
    )
    col_pattern = re.compile(
        r'^\[(\w+)\]\s+\[(\w+)\](?:\(([^)]+)\))?',
        re.IGNORECASE,
    )

    blocks = []
    for part in parts:
        if not part.strip():
            continue
        m = block_re.search(part)
        if not m:
            continue
        
        table_name = m.group(1)
        body = m.group(2)
        cols = []
        field_no = 1
        for line in body.splitlines():
            line = line.strip().rstrip(',')
            if re.match(r'(CONSTRAINT|PRIMARY|UNIQUE|CHECK|FOREIGN)', line, re.IGNORECASE):
                continue
            cm = col_pattern.match(line)
            if not cm:
                continue

            col_name = cm.group(1)
            base_type = cm.group(2)
            precision_str = (cm.group(3) or "").strip()
            type_sql = f"[{base_type}]({precision_str})" if precision_str else f"[{base_type}]"
            cols.append((col_name, type_sql))
            field_no += 1

        if cols:
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
    rnk_name = "RNKTRANS"

    s1_entity_id = _pick_col(src1_cols, "entity_id")
    s1_ts = _pick_col(src1_cols, "_data_timestamp")  # Fixed: changed from _data_timestamp_sequence
    s1_offset = _pick_col(src1_cols, "offset")

    s2_entity_id = _pick_col(src2_cols, "entity_id")
    s2_ts = _pick_col(src2_cols, "_data_timestamp")  # Fixed: changed from _data_timestamp_sequence
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
        f"{src1_name}.{s1_entity_id} = {src2_name}.{s2_entity_id} AND "
        f"{src1_name}.{s1_offset}={src2_name}.{s2_offset} AND "
        f"{src1_name}.{s1_ts}={src2_name}.{s2_ts}"
    )
    add(sq, "TABLEATTRIBUTE", NAME="Sql Query", VALUE="")
    add(sq, "TABLEATTRIBUTE", NAME="User Defined Join", VALUE=join_value)
    sf = source_filter if source_filter is not None else ""
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

    # Add RANK transformation
    rnk = add(mp, "TRANSFORMATION", DESCRIPTION="", NAME=rnk_name, OBJECTVERSION="1", REUSABLE="NO", TYPE="Rank", VERSIONNUMBER="1")
    add(rnk, "TRANSFORMFIELD", DATATYPE="integer", DEFAULTVALUE="ERROR('transformation error')", DESCRIPTION="", EXPRESSION="RANKINDEX",
        EXPRESSIONTYPE="RANKINDEX", NAME="RANKINDEX", PICTURETEXT="", PORTTYPE="OUTPUT", PRECISION="10", SCALE="0")
    add(rnk, "TRANSFORMFIELD", DATATYPE="string", DEFAULTVALUE="", DESCRIPTION="", EXPRESSION=s2_trans_id,
        EXPRESSIONTYPE="RANKPORT", NAME=s2_trans_id, PICTURETEXT="", PORTTYPE="INPUT/OUTPUT", PRECISION="50", SCALE="0")
    for c in src1_cols:
        if c["name"].lower() not in [s2_trans_id.lower()]:
            sm = delta_000_sq_meta(c["type_sql"])
            # row_create_Date should be GENERAL, not GROUPBY
            expr_type = "GENERAL" if c["name"].lower() == "row_create_date" else "GROUPBY"
            add(rnk, "TRANSFORMFIELD", DATATYPE=sm["DATATYPE"], DEFAULTVALUE="", DESCRIPTION="", EXPRESSION=c["name"],
                EXPRESSIONTYPE=expr_type, NAME=c["name"], PICTURETEXT="", PORTTYPE="INPUT/OUTPUT",
                PRECISION=sm["PRECISION"], SCALE=sm["SCALE"])
    for n, v in [("Cache Directory", "$PMCacheDir"), ("Top/Bottom", "Top"), ("Number of Ranks", "1"),
                 ("Case Sensitive String Comparison", "YES"), ("Tracing Level", "Normal"),
                 ("Rank Data Cache Size", "Auto"), ("Rank Index Cache Size", "Auto"),
                 ("Transformation Scope", "All Input")]:
        add(rnk, "TABLEATTRIBUTE", NAME=n, VALUE=v)

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
    add(mp, "INSTANCE", DESCRIPTION="", NAME=rnk_name, REUSABLE="NO", TRANSFORMATION_NAME=rnk_name,
        TRANSFORMATION_TYPE="Rank", TYPE="TRANSFORMATION")

    for c in src1_cols:
        conn(mp, c["name"], src1_name, "Source Definition", c["name"], sq_name, "Source Qualifier")
    conn(mp, s2_entity_type, src2_name, "Source Definition", "entity_type_current", sq_name, "Source Qualifier")
    for c in src1_cols:
        conn(mp, c["name"], sq_name, "Source Qualifier", c["name"], exp_name, "Expression")
    # Connect EXP_Transform to RANK
    conn(mp, s2_trans_id, exp_name, "Expression", s2_trans_id, rnk_name, "Rank")
    for c in src1_cols:
        if c["name"].lower() != s2_trans_id.lower():
            conn(mp, c["name"], exp_name, "Expression", c["name"], rnk_name, "Rank")
    # Connect RANK to Target
    for c in src1_cols:
        conn(mp, c["name"], rnk_name, "Rank", c["name"], target_name, "Target Definition")

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
        
        if len(blocks) < 2:
            # טעם debug: הדפס כמה בלוקים מצאנו
            found_tables = f"נמצאו {len(blocks)} טבלאות: {[name for name, _ in blocks]}" if blocks else "לא נמצאו טבלאות בקלט"
            return f"<!-- DELTA 030 - ERROR: נדרשות שתי טבלאות - אחת עם סיומת _MASTER ואחת עם סיומת _DETAIL. {found_tables} -->"

        detail_block = None
        master_block = None
        for tname, tcols in blocks:
            ln = tname.lower()
            if detail_block is None and ("detail" in ln or "communication" in ln):
                detail_block = (tname, tcols)
            if master_block is None and "master" in ln:
                master_block = (tname, tcols)

        if detail_block is None or master_block is None:
            found = []
            if detail_block:
                found.append(f"DETAIL: {detail_block[0]}")
            if master_block:
                found.append(f"MASTER: {master_block[0]}")
            found_str = ", ".join(found) if found else "לא נמצא"
            return f"<!-- DELTA 030 - ERROR: לא נמצאו שתי הטבלאות הנדרשות (_MASTER ו-_DETAIL) בקלט. {found_str} -->"

        detail_name, detail_cols_raw = detail_block
        master_name, master_cols_raw = master_block

        # Convert raw tuples to dict format for compatibility
        detail_cols = [{"name": col[0], "type_sql": col[1], "field_no": i+1, "nullable": True} 
                      for i, col in enumerate(detail_cols_raw)]
        master_cols = [{"name": col[0], "type_sql": col[1], "field_no": i+1, "nullable": True} 
                      for i, col in enumerate(master_cols_raw)]

        src1_name = detail_name
        if src1_name.lower().endswith("_stg"):
            base_name = src1_name[:-4]
        elif src1_name.lower().endswith("_cln"):
            base_name = src1_name[:-4]
        else:
            base_name = src1_name

        # Fixed: Master source name needs _CLN suffix
        src2_name = f"{master_name}_CLN" if not master_name.lower().endswith("_cln") else master_name
        target_name = f"{base_name}_CLN"
        mapping_name = f"m_DELTA_030_{base_name}_cln"

        pm = ET.Element("POWERMART", CREATION_DATE=datetime.now().strftime("%m/%d/%Y %H:%M:%S"), REPOSITORY_VERSION="187.96")
        repo = add(pm, "REPOSITORY", NAME="InfoDW_QA_Rep", VERSION="187", CODEPAGE="MS1255", DATABASETYPE="Microsoft SQL Server")
        fld = add(repo, "FOLDER", NAME=folder_name, GROUP="", OWNER="Administrator", SHARED="NOTSHARED",
                  DESCRIPTION="", PERMISSIONS="rwx------", UUID="620f71cd-f2d3-4541-9b90-9c08ea2afbf8")

        _build_source(fld, src1_name, "dwh-dev", "kfk", detail_cols)
        _build_source(fld, src2_name, "dwh-dev", "KFK", master_cols)
        _build_target(fld, target_name, detail_cols)
        _build_two_source_delta_mapping(
            fld,
            mapping_name=mapping_name,
            src1_name=src1_name,
            src1_cols=detail_cols,
            src2_name=src2_name,
            src2_cols=master_cols,
            target_name=target_name,
            source_filter="",
        )

        return _render_powermart_xml(pm)
    except Exception as e:
        return f"<!-- DELTA 030 - ERROR: {e} -->"


# =====================================================================
# WF PARAMETERS - Workflow XML Generator
# =====================================================================

def get_wf_parameters_template():
    """Return WF_PARAMETERS template XML as string - FULL template with all mappings and sessions"""
    return """<?xml version="1.0" encoding="windows-1255"?>
<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">
<POWERMART CREATION_DATE="__CREATION_DATE__" REPOSITORY_VERSION="187.96">
<REPOSITORY NAME="InfoDW_QA_Rep" VERSION="187" CODEPAGE="MS1255" DATABASETYPE="Microsoft SQL Server">
<FOLDER NAME="__FOLDER_NAME__" GROUP="" OWNER="Administrator" SHARED="NOTSHARED" DESCRIPTION="" PERMISSIONS="rwx------" UUID="620f71cd-f2d3-4541-9b90-9c08ea2afbf8">
    <SOURCE BUSINESSNAME ="" DATABASETYPE ="Microsoft SQL Server" DBDNAME ="DWH" DESCRIPTION ="" NAME ="ETL_PARAMETERS_VALUES" OBJECTVERSION ="1" OWNERNAME ="mng" VERSIONNUMBER ="5">
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="int" DESCRIPTION ="" FIELDNUMBER ="1" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="PRIMARY KEY" LENGTH ="11" LEVEL ="0" NAME ="PARAM_CODE" NULLABLE ="NOTNULL" OCCURS ="0" OFFSET ="0" PHYSICALLENGTH ="10" PHYSICALOFFSET ="0" PICTURETEXT ="" PRECISION ="10" SCALE ="0" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="int" DESCRIPTION ="" FIELDNUMBER ="2" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="PRIMARY KEY" LENGTH ="11" LEVEL ="0" NAME ="PARAM_VALUE_CODE" NULLABLE ="NOTNULL" OCCURS ="0" OFFSET ="11" PHYSICALLENGTH ="10" PHYSICALOFFSET ="10" PICTURETEXT ="" PRECISION ="10" SCALE ="0" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="smallint" DESCRIPTION ="" FIELDNUMBER ="3" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="6" LEVEL ="0" NAME ="MANUAL_VALUE_IND" NULLABLE ="NULL" OCCURS ="0" OFFSET ="22" PHYSICALLENGTH ="5" PHYSICALOFFSET ="20" PICTURETEXT ="" PRECISION ="5" SCALE ="0" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="bigint" DESCRIPTION ="" FIELDNUMBER ="4" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="20" LEVEL ="0" NAME ="PARAM_VALUE_INT" NULLABLE ="NULL" OCCURS ="0" OFFSET ="28" PHYSICALLENGTH ="19" PHYSICALOFFSET ="25" PICTURETEXT ="" PRECISION ="19" SCALE ="0" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="datetime" DESCRIPTION ="" FIELDNUMBER ="5" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="19" LEVEL ="0" NAME ="PARAM_VALUE_DATETIME" NULLABLE ="NULL" OCCURS ="0" OFFSET ="48" PHYSICALLENGTH ="23" PHYSICALOFFSET ="44" PICTURETEXT ="" PRECISION ="23" SCALE ="3" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="varchar" DESCRIPTION ="" FIELDNUMBER ="6" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="0" LEVEL ="0" NAME ="PARAM_VALUE_VARCHAR" NULLABLE ="NULL" OCCURS ="0" OFFSET ="67" PHYSICALLENGTH ="500" PHYSICALOFFSET ="67" PICTURETEXT ="" PRECISION ="500" SCALE ="0" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="datetime" DESCRIPTION ="" FIELDNUMBER ="7" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="19" LEVEL ="0" NAME ="CREATE_DATE" NULLABLE ="NULL" OCCURS ="0" OFFSET ="67" PHYSICALLENGTH ="23" PHYSICALOFFSET ="567" PICTURETEXT ="" PRECISION ="23" SCALE ="3" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="datetime" DESCRIPTION ="" FIELDNUMBER ="8" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="19" LEVEL ="0" NAME ="UPDATE_DATE" NULLABLE ="NULL" OCCURS ="0" OFFSET ="86" PHYSICALLENGTH ="23" PHYSICALOFFSET ="590" PICTURETEXT ="" PRECISION ="23" SCALE ="3" USAGE_FLAGS =""/>
    </SOURCE>
    <SOURCE BUSINESSNAME ="" DATABASETYPE ="Microsoft SQL Server" DBDNAME ="DWH" DESCRIPTION ="" NAME ="ETL_PARAMETERS_HEADERS" OBJECTVERSION ="1" OWNERNAME ="mng" VERSIONNUMBER ="5">
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="int" DESCRIPTION ="" FIELDNUMBER ="1" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="PRIMARY KEY" LENGTH ="11" LEVEL ="0" NAME ="PARAM_CODE" NULLABLE ="NOTNULL" OCCURS ="0" OFFSET ="0" PHYSICALLENGTH ="10" PHYSICALOFFSET ="0" PICTURETEXT ="" PRECISION ="10" SCALE ="0" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="varchar" DESCRIPTION ="" FIELDNUMBER ="2" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="0" LEVEL ="0" NAME ="PARAM_NAME" NULLABLE ="NULL" OCCURS ="0" OFFSET ="11" PHYSICALLENGTH ="100" PHYSICALOFFSET ="10" PICTURETEXT ="" PRECISION ="100" SCALE ="0" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="varchar" DESCRIPTION ="" FIELDNUMBER ="3" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="0" LEVEL ="0" NAME ="PARAM_FILE_NAME" NULLABLE ="NULL" OCCURS ="0" OFFSET ="11" PHYSICALLENGTH ="100" PHYSICALOFFSET ="110" PICTURETEXT ="" PRECISION ="100" SCALE ="0" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="varchar" DESCRIPTION ="" FIELDNUMBER ="4" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="0" LEVEL ="0" NAME ="MODEL_NAME" NULLABLE ="NULL" OCCURS ="0" OFFSET ="11" PHYSICALLENGTH ="100" PHYSICALOFFSET ="210" PICTURETEXT ="" PRECISION ="100" SCALE ="0" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="varchar" DESCRIPTION ="" FIELDNUMBER ="5" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="0" LEVEL ="0" NAME ="KAFKA_SHEET" NULLABLE ="NULL" OCCURS ="0" OFFSET ="11" PHYSICALLENGTH ="1000" PHYSICALOFFSET ="310" PICTURETEXT ="" PRECISION ="1000" SCALE ="0" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="datetime" DESCRIPTION ="" FIELDNUMBER ="6" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="19" LEVEL ="0" NAME ="CREATE_DATE" NULLABLE ="NULL" OCCURS ="0" OFFSET ="11" PHYSICALLENGTH ="23" PHYSICALOFFSET ="1310" PICTURETEXT ="" PRECISION ="23" SCALE ="3" USAGE_FLAGS =""/>
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="datetime" DESCRIPTION ="" FIELDNUMBER ="7" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="19" LEVEL ="0" NAME ="UPDATE_DATE" NULLABLE ="NULL" OCCURS ="0" OFFSET ="30" PHYSICALLENGTH ="23" PHYSICALOFFSET ="1333" PICTURETEXT ="" PRECISION ="23" SCALE ="3" USAGE_FLAGS =""/>
    </SOURCE>
    <SOURCE BUSINESSNAME ="" DATABASETYPE ="Microsoft SQL Server" DBDNAME ="SQL-DWH-DW_Management" DESCRIPTION ="" NAME ="DUAL" OBJECTVERSION ="1" OWNERNAME ="dwh" VERSIONNUMBER ="5">
        <SOURCEFIELD BUSINESSNAME ="" DATATYPE ="char" DESCRIPTION ="" FIELDNUMBER ="1" FIELDPROPERTY ="0" FIELDTYPE ="ELEMITEM" HIDDEN ="NO" KEYTYPE ="NOT A KEY" LENGTH ="0" LEVEL ="0" NAME ="DUMMY" NULLABLE ="NULL" OCCURS ="0" OFFSET ="0" PHYSICALLENGTH ="1" PHYSICALOFFSET ="0" PICTURETEXT ="" PRECISION ="1" SCALE ="0" USAGE_FLAGS =""/>
    </SOURCE>
    <TARGET BUSINESSNAME ="" CONSTRAINT ="" DATABASETYPE ="Flat File" DESCRIPTION ="" NAME ="FLAT_FILE" OBJECTVERSION ="1" TABLEOPTIONS ="" VERSIONNUMBER ="5">
        <FLATFILE CODEPAGE ="MS1255" CONSECDELIMITERSASONE ="NO" DELIMITED ="YES" DELIMITERS ="," ESCAPE_CHARACTER ="" KEEPESCAPECHAR ="NO" LINESEQUENTIAL ="NO" MULTIDELIMITERSASAND ="NO" NULLCHARTYPE ="ASCII" NULL_CHARACTER ="*" PADBYTES ="1" QUOTE_CHARACTER ="NONE" REPEATABLE ="NO" ROWDELIMITER ="0" SKIPROWS ="0" STRIPTRAILINGBLANKS ="NO"/>
        <TARGETFIELD BUSINESSNAME ="" DATATYPE ="string" DESCRIPTION ="" FIELDNUMBER ="1" KEYTYPE ="NOT A KEY" NAME ="PARAM_FILE_VALUE" NULLABLE ="NULL" PICTURETEXT ="" PRECISION ="4000" SCALE ="0"/>
        <TABLEATTRIBUTE NAME ="Datetime Format" VALUE ="A  19 mm/dd/yyyy hh24:mi:ss"/>
        <TABLEATTRIBUTE NAME ="Thousand Separator" VALUE ="None"/>
        <TABLEATTRIBUTE NAME ="Decimal Separator" VALUE ="."/>
        <TABLEATTRIBUTE NAME ="Line Endings" VALUE ="System default"/>
    </TARGET>
    <MAPPING DESCRIPTION ="" ISVALID ="YES" NAME ="Shortcut_to_m_Parameter_File" OBJECTVERSION ="1" VERSIONNUMBER ="5">
        <TRANSFORMATION DESCRIPTION ="" NAME ="AGG_MAX_PARAM_VALUE_CODE" OBJECTVERSION ="1" REUSABLE ="NO" TYPE ="Aggregator" VERSIONNUMBER ="5">
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_CODE" EXPRESSIONTYPE ="GROUPBY" NAME ="PARAM_CODE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_CODE" PICTURETEXT ="" PORTTYPE ="INPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="ERROR(&apos;transformation error&apos;)" DESCRIPTION ="" EXPRESSION ="MAX(PARAM_VALUE_CODE)" EXPRESSIONTYPE ="GENERAL" NAME ="MAX_PARAM_VALUE_CODE" PICTURETEXT ="" PORTTYPE ="OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TABLEATTRIBUTE NAME ="Cache Directory" VALUE ="$PMCacheDir"/>
            <TABLEATTRIBUTE NAME ="Tracing Level" VALUE ="Normal"/>
            <TABLEATTRIBUTE NAME ="Sorted Input" VALUE ="YES"/>
            <TABLEATTRIBUTE NAME ="Aggregator Data Cache Size" VALUE ="Auto"/>
            <TABLEATTRIBUTE NAME ="Aggregator Index Cache Size" VALUE ="Auto"/>
            <TABLEATTRIBUTE NAME ="Transformation Scope" VALUE ="All Input"/>
        </TRANSFORMATION>
        <TRANSFORMATION DESCRIPTION ="" NAME ="JNR_WITH_MIN_PARAM_CODE" OBJECTVERSION ="1" REUSABLE ="NO" TYPE ="Joiner" VERSIONNUMBER ="5">
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_CODE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_CODE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="bigint" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_INT" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="19" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_DATETIME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="29" SCALE ="9"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_VARCHAR" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="500" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_FILE_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="MAX_PARAM_VALUE_CODE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_FILE_NAME1" PICTURETEXT ="" PORTTYPE ="INPUT/MASTER" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_CODE_MIN" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT/MASTER" PRECISION ="10" SCALE ="0"/>
            <TABLEATTRIBUTE NAME ="Case Sensitive String Comparison" VALUE ="YES"/>
            <TABLEATTRIBUTE NAME ="Cache Directory" VALUE ="$PMCacheDir"/>
            <TABLEATTRIBUTE NAME ="Join Condition" VALUE ="PARAM_FILE_NAME1 = PARAM_FILE_NAME"/>
            <TABLEATTRIBUTE NAME ="Join Type" VALUE ="Normal Join"/>
            <TABLEATTRIBUTE NAME ="Tracing Level" VALUE ="Normal"/>
            <TABLEATTRIBUTE NAME ="Transformation Scope" VALUE ="All Input"/>
        </TRANSFORMATION>
        <TRANSFORMATION DESCRIPTION ="" NAME ="SQ_ETL_PARAMETERS_HEADERS" OBJECTVERSION ="1" REUSABLE ="NO" TYPE ="Source Qualifier" VERSIONNUMBER ="5">
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_CODE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_CODE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_FILE_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="MODEL_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="KAFKA_SHEET" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="1000" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="CREATE_DATE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="29" SCALE ="9"/>
            <TRANSFORMFIELD DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="UPDATE_DATE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="29" SCALE ="9"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_CODE1" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="small integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="MANUAL_VALUE_IND" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="5" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="bigint" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_INT" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="19" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_DATETIME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="29" SCALE ="9"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_VARCHAR" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="500" SCALE ="0"/>
            <TABLEATTRIBUTE NAME ="Sql Query" VALUE =""/>
            <TABLEATTRIBUTE NAME ="User Defined Join" VALUE ="ETL_PARAMETERS_HEADERS.PARAM_CODE=ETL_PARAMETERS_VALUES.PARAM_CODE"/>
            <TABLEATTRIBUTE NAME ="Source Filter" VALUE ="ETL_PARAMETERS_HEADERS.PARAM_CODE in ($$m_PARAMETER_CODES)"/>
            <TABLEATTRIBUTE NAME ="Number Of Sorted Ports" VALUE ="2"/>
            <TABLEATTRIBUTE NAME ="Tracing Level" VALUE ="Normal"/>
            <TABLEATTRIBUTE NAME ="Select Distinct" VALUE ="NO"/>
            <TABLEATTRIBUTE NAME ="Is Partitionable" VALUE ="NO"/>
            <TABLEATTRIBUTE NAME ="Pre SQL" VALUE =""/>
            <TABLEATTRIBUTE NAME ="Post SQL" VALUE =""/>
            <TABLEATTRIBUTE NAME ="Output is deterministic" VALUE ="NO"/>
            <TABLEATTRIBUTE NAME ="Output is repeatable" VALUE ="Never"/>
        </TRANSFORMATION>
        <TRANSFORMATION DESCRIPTION ="" NAME ="EXP_CREATE_FILE_TEXT" OBJECTVERSION ="1" REUSABLE ="NO" TYPE ="Expression" VERSIONNUMBER ="5">
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_CODE" PICTURETEXT ="" PORTTYPE ="INPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_CODE_MIN" PICTURETEXT ="" PORTTYPE ="INPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_NAME" PICTURETEXT ="" PORTTYPE ="INPUT" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_CODE" PICTURETEXT ="" PORTTYPE ="INPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_FILE_VALUE" PICTURETEXT ="" PORTTYPE ="OUTPUT" PRECISION ="4000" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_FILE_VALUE_LENGTH" PICTURETEXT ="" PORTTYPE ="OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_FILE_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TABLEATTRIBUTE NAME ="Tracing Level" VALUE ="Normal"/>
        </TRANSFORMATION>
        <TRANSFORMATION DESCRIPTION ="takes only the longest value = complete file" NAME ="RNK_LONGEST" OBJECTVERSION ="1" REUSABLE ="NO" TYPE ="Rank" VERSIONNUMBER ="5">
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="RANKINDEX" EXPRESSIONTYPE ="RANKINDEX" NAME ="RANKINDEX" PICTURETEXT ="" PORTTYPE ="OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_FILE_VALUE" EXPRESSIONTYPE ="GENERAL" NAME ="PARAM_FILE_VALUE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="4000" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_FILE_VALUE_LENGTH" EXPRESSIONTYPE ="RANKPORT" NAME ="PARAM_FILE_VALUE_LENGTH" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_FILE_NAME" EXPRESSIONTYPE ="GROUPBY" NAME ="PARAM_FILE_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TABLEATTRIBUTE NAME ="Cache Directory" VALUE ="$PMCacheDir"/>
            <TABLEATTRIBUTE NAME ="Top/Bottom" VALUE ="Top"/>
            <TABLEATTRIBUTE NAME ="Number of Ranks" VALUE ="1"/>
            <TABLEATTRIBUTE NAME ="Tracing Level" VALUE ="Normal"/>
        </TRANSFORMATION>
        <TRANSFORMATION DESCRIPTION ="" NAME ="EXP_ARRANGE" OBJECTVERSION ="1" REUSABLE ="NO" TYPE ="Expression" VERSIONNUMBER ="5">
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_CODE" EXPRESSIONTYPE ="GENERAL" NAME ="PARAM_CODE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_NAME" EXPRESSIONTYPE ="GENERAL" NAME ="PARAM_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_VALUE_CODE" EXPRESSIONTYPE ="GENERAL" NAME ="PARAM_VALUE_CODE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="bigint" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_VALUE_INT" EXPRESSIONTYPE ="GENERAL" NAME ="PARAM_VALUE_INT" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="19" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_VALUE_DATETIME" EXPRESSIONTYPE ="GENERAL" NAME ="PARAM_VALUE_DATETIME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="29" SCALE ="9"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_VALUE_VARCHAR" EXPRESSIONTYPE ="GENERAL" NAME ="PARAM_VALUE_VARCHAR" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="500" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_FILE_NAME" EXPRESSIONTYPE ="GENERAL" NAME ="PARAM_FILE_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TABLEATTRIBUTE NAME ="Tracing Level" VALUE ="Normal"/>
        </TRANSFORMATION>
        <TRANSFORMATION DESCRIPTION ="" NAME ="AGG_MIN_PARAM_CODE" OBJECTVERSION ="1" REUSABLE ="NO" TYPE ="Aggregator" VERSIONNUMBER ="5">
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_CODE" PICTURETEXT ="" PORTTYPE ="INPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="PARAM_FILE_NAME" EXPRESSIONTYPE ="GROUPBY" NAME ="PARAM_FILE_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" EXPRESSION ="MIN(PARAM_CODE)" EXPRESSIONTYPE ="GENERAL" NAME ="PARAM_CODE_MIN" PICTURETEXT ="" PORTTYPE ="OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TABLEATTRIBUTE NAME ="Cache Directory" VALUE ="$PMCacheDir"/>
            <TABLEATTRIBUTE NAME ="Tracing Level" VALUE ="Normal"/>
        </TRANSFORMATION>
        <TRANSFORMATION DESCRIPTION ="" NAME ="JNR_WITH_MAX_PARAM_VALUE_CODE" OBJECTVERSION ="1" REUSABLE ="NO" TYPE ="Joiner" VERSIONNUMBER ="5">
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_CODE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_CODE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="bigint" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_INT" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="19" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_DATETIME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="29" SCALE ="9"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_VALUE_VARCHAR" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="500" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_FILE_NAME" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_CODE1" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT/MASTER" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="MAX_PARAM_VALUE_CODE" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT/MASTER" PRECISION ="10" SCALE ="0"/>
            <TABLEATTRIBUTE NAME ="Cache Directory" VALUE ="$PMCacheDir"/>
            <TABLEATTRIBUTE NAME ="Join Condition" VALUE ="PARAM_CODE1 = PARAM_CODE"/>
            <TABLEATTRIBUTE NAME ="Tracing Level" VALUE ="Normal"/>
        </TRANSFORMATION>
        <INSTANCE DESCRIPTION ="" NAME ="FLAT_FILE" TRANSFORMATION_NAME ="FLAT_FILE" TRANSFORMATION_TYPE ="Target Definition" TYPE ="TARGET"/>
        <INSTANCE DBDNAME ="DWH" DESCRIPTION ="" NAME ="ETL_PARAMETERS_HEADERS1" TRANSFORMATION_NAME ="ETL_PARAMETERS_HEADERS" TRANSFORMATION_TYPE ="Source Definition" TYPE ="SOURCE"/>
        <INSTANCE DBDNAME ="DWH" DESCRIPTION ="" NAME ="Shortcut_to_ETL_PARAMETERS_VALUES" TRANSFORMATION_NAME ="ETL_PARAMETERS_VALUES" TRANSFORMATION_TYPE ="Source Definition" TYPE ="SOURCE"/>
        <INSTANCE DESCRIPTION ="" NAME ="AGG_MAX_PARAM_VALUE_CODE" REUSABLE ="NO" TRANSFORMATION_NAME ="AGG_MAX_PARAM_VALUE_CODE" TRANSFORMATION_TYPE ="Aggregator" TYPE ="TRANSFORMATION"/>
        <INSTANCE DESCRIPTION ="" NAME ="JNR_WITH_MIN_PARAM_CODE" REUSABLE ="NO" TRANSFORMATION_NAME ="JNR_WITH_MIN_PARAM_CODE" TRANSFORMATION_TYPE ="Joiner" TYPE ="TRANSFORMATION"/>
        <INSTANCE DESCRIPTION ="" NAME ="SQ_ETL_PARAMETERS_HEADERS" REUSABLE ="NO" TRANSFORMATION_NAME ="SQ_ETL_PARAMETERS_HEADERS" TRANSFORMATION_TYPE ="Source Qualifier" TYPE ="TRANSFORMATION">
            <ASSOCIATED_SOURCE_INSTANCE NAME ="ETL_PARAMETERS_HEADERS1"/>
            <ASSOCIATED_SOURCE_INSTANCE NAME ="Shortcut_to_ETL_PARAMETERS_VALUES"/>
        </INSTANCE>
        <INSTANCE DESCRIPTION ="" NAME ="EXP_CREATE_FILE_TEXT" REUSABLE ="NO" TRANSFORMATION_NAME ="EXP_CREATE_FILE_TEXT" TRANSFORMATION_TYPE ="Expression" TYPE ="TRANSFORMATION"/>
        <INSTANCE DESCRIPTION ="takes only the longest value = complete file" NAME ="RNK_LONGEST" REUSABLE ="NO" TRANSFORMATION_NAME ="RNK_LONGEST" TRANSFORMATION_TYPE ="Rank" TYPE ="TRANSFORMATION"/>
        <INSTANCE DESCRIPTION ="" NAME ="EXP_ARRANGE" REUSABLE ="NO" TRANSFORMATION_NAME ="EXP_ARRANGE" TRANSFORMATION_TYPE ="Expression" TYPE ="TRANSFORMATION"/>
        <INSTANCE DESCRIPTION ="" NAME ="AGG_MIN_PARAM_CODE" REUSABLE ="NO" TRANSFORMATION_NAME ="AGG_MIN_PARAM_CODE" TRANSFORMATION_TYPE ="Aggregator" TYPE ="TRANSFORMATION"/>
        <INSTANCE DESCRIPTION ="" NAME ="JNR_WITH_MAX_PARAM_VALUE_CODE" REUSABLE ="NO" TRANSFORMATION_NAME ="JNR_WITH_MAX_PARAM_VALUE_CODE" TRANSFORMATION_TYPE ="Joiner" TYPE ="TRANSFORMATION"/>
        <CONNECTOR FROMFIELD ="PARAM_CODE" FROMINSTANCE ="EXP_ARRANGE" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_CODE" TOINSTANCE ="AGG_MAX_PARAM_VALUE_CODE" TOINSTANCETYPE ="Aggregator"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_CODE" FROMINSTANCE ="EXP_ARRANGE" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_VALUE_CODE" TOINSTANCE ="AGG_MAX_PARAM_VALUE_CODE" TOINSTANCETYPE ="Aggregator"/>
        <CONNECTOR FROMFIELD ="PARAM_CODE" FROMINSTANCE ="AGG_MAX_PARAM_VALUE_CODE" FROMINSTANCETYPE ="Aggregator" TOFIELD ="PARAM_CODE1" TOINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="MAX_PARAM_VALUE_CODE" FROMINSTANCE ="AGG_MAX_PARAM_VALUE_CODE" FROMINSTANCETYPE ="Aggregator" TOFIELD ="MAX_PARAM_VALUE_CODE" TOINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_FILE_NAME" FROMINSTANCE ="AGG_MIN_PARAM_CODE" FROMINSTANCETYPE ="Aggregator" TOFIELD ="PARAM_FILE_NAME1" TOINSTANCE ="JNR_WITH_MIN_PARAM_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_CODE_MIN" FROMINSTANCE ="AGG_MIN_PARAM_CODE" FROMINSTANCETYPE ="Aggregator" TOFIELD ="PARAM_CODE_MIN" TOINSTANCE ="JNR_WITH_MIN_PARAM_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_NAME" FROMINSTANCE ="SQ_ETL_PARAMETERS_HEADERS" FROMINSTANCETYPE ="Source Qualifier" TOFIELD ="PARAM_NAME" TOINSTANCE ="EXP_ARRANGE" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_CODE" FROMINSTANCE ="SQ_ETL_PARAMETERS_HEADERS" FROMINSTANCETYPE ="Source Qualifier" TOFIELD ="PARAM_VALUE_CODE" TOINSTANCE ="EXP_ARRANGE" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="PARAM_CODE" FROMINSTANCE ="SQ_ETL_PARAMETERS_HEADERS" FROMINSTANCETYPE ="Source Qualifier" TOFIELD ="PARAM_CODE" TOINSTANCE ="EXP_ARRANGE" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="PARAM_FILE_VALUE" FROMINSTANCE ="EXP_CREATE_FILE_TEXT" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_FILE_VALUE" TOINSTANCE ="RNK_LONGEST" TOINSTANCETYPE ="Rank"/>
        <CONNECTOR FROMFIELD ="PARAM_FILE_VALUE_LENGTH" FROMINSTANCE ="EXP_CREATE_FILE_TEXT" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_FILE_VALUE_LENGTH" TOINSTANCE ="RNK_LONGEST" TOINSTANCETYPE ="Rank"/>
        <CONNECTOR FROMFIELD ="PARAM_FILE_NAME" FROMINSTANCE ="EXP_CREATE_FILE_TEXT" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_FILE_NAME" TOINSTANCE ="RNK_LONGEST" TOINSTANCETYPE ="Rank"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_DATETIME" FROMINSTANCE ="EXP_ARRANGE" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_VALUE_DATETIME" TOINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_CODE" FROMINSTANCE ="EXP_ARRANGE" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_CODE" TOINSTANCE ="AGG_MIN_PARAM_CODE" TOINSTANCETYPE ="Aggregator"/>
        <CONNECTOR FROMFIELD ="PARAM_FILE_NAME" FROMINSTANCE ="EXP_ARRANGE" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_FILE_NAME" TOINSTANCE ="AGG_MIN_PARAM_CODE" TOINSTANCETYPE ="Aggregator"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_VARCHAR" FROMINSTANCE ="EXP_ARRANGE" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_VALUE_VARCHAR" TOINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_FILE_NAME" FROMINSTANCE ="EXP_ARRANGE" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_FILE_NAME" TOINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_CODE" FROMINSTANCE ="EXP_ARRANGE" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_CODE" TOINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_NAME" FROMINSTANCE ="EXP_ARRANGE" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_NAME" TOINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_CODE" FROMINSTANCE ="EXP_ARRANGE" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_VALUE_CODE" TOINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_INT" FROMINSTANCE ="EXP_ARRANGE" FROMINSTANCETYPE ="Expression" TOFIELD ="PARAM_VALUE_INT" TOINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_CODE" FROMINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_CODE" TOINSTANCE ="JNR_WITH_MIN_PARAM_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_NAME" FROMINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_NAME" TOINSTANCE ="JNR_WITH_MIN_PARAM_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_CODE" FROMINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_VALUE_CODE" TOINSTANCE ="JNR_WITH_MIN_PARAM_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_INT" FROMINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_VALUE_INT" TOINSTANCE ="JNR_WITH_MIN_PARAM_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_DATETIME" FROMINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_VALUE_DATETIME" TOINSTANCE ="JNR_WITH_MIN_PARAM_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_VARCHAR" FROMINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_VALUE_VARCHAR" TOINSTANCE ="JNR_WITH_MIN_PARAM_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_FILE_NAME" FROMINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_FILE_NAME" TOINSTANCE ="JNR_WITH_MIN_PARAM_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="MAX_PARAM_VALUE_CODE" FROMINSTANCE ="JNR_WITH_MAX_PARAM_VALUE_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="MAX_PARAM_VALUE_CODE" TOINSTANCE ="JNR_WITH_MIN_PARAM_CODE" TOINSTANCETYPE ="Joiner"/>
        <CONNECTOR FROMFIELD ="PARAM_CODE" FROMINSTANCE ="JNR_WITH_MIN_PARAM_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_CODE" TOINSTANCE ="EXP_CREATE_FILE_TEXT" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="PARAM_NAME" FROMINSTANCE ="JNR_WITH_MIN_PARAM_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_NAME" TOINSTANCE ="EXP_CREATE_FILE_TEXT" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_CODE" FROMINSTANCE ="JNR_WITH_MIN_PARAM_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_VALUE_CODE" TOINSTANCE ="EXP_CREATE_FILE_TEXT" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_INT" FROMINSTANCE ="JNR_WITH_MIN_PARAM_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_VALUE_INT" TOINSTANCE ="EXP_CREATE_FILE_TEXT" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="MAX_PARAM_VALUE_CODE" FROMINSTANCE ="JNR_WITH_MIN_PARAM_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="MAX_PARAM_VALUE_CODE" TOINSTANCE ="EXP_CREATE_FILE_TEXT" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_DATETIME" FROMINSTANCE ="JNR_WITH_MIN_PARAM_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_VALUE_DATETIME" TOINSTANCE ="EXP_CREATE_FILE_TEXT" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="PARAM_VALUE_VARCHAR" FROMINSTANCE ="JNR_WITH_MIN_PARAM_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_VALUE_VARCHAR" TOINSTANCE ="EXP_CREATE_FILE_TEXT" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="PARAM_FILE_NAME" FROMINSTANCE ="JNR_WITH_MIN_PARAM_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_FILE_NAME" TOINSTANCE ="EXP_CREATE_FILE_TEXT" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="PARAM_CODE_MIN" FROMINSTANCE ="JNR_WITH_MIN_PARAM_CODE" FROMINSTANCETYPE ="Joiner" TOFIELD ="PARAM_CODE_MIN" TOINSTANCE ="EXP_CREATE_FILE_TEXT" TOINSTANCETYPE ="Expression"/>
        <CONNECTOR FROMFIELD ="PARAM_FILE_VALUE" FROMINSTANCE ="RNK_LONGEST" FROMINSTANCETYPE ="Rank" TOFIELD ="PARAM_FILE_VALUE" TOINSTANCE ="FLAT_FILE" TOINSTANCETYPE ="Target Definition"/>
        <TARGETLOADORDER ORDER ="1" TARGETINSTANCE ="FLAT_FILE"/>
        <MAPPINGVARIABLE AGGFUNCTION ="MAX" DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" ISEXPRESSIONVARIABLE ="NO" ISPARAM ="NO" NAME ="$$m_PARAMETER_CODES" PRECISION ="200" SCALE ="0" USERDEFINED ="YES"/>
        <ERPINFO/>
    </MAPPING>
    <MAPPING DESCRIPTION ="" ISVALID ="YES" NAME ="m_param_calc_TRANSACTION_ID" OBJECTVERSION ="1" VERSIONNUMBER ="1">
        <TRANSFORMATION DESCRIPTION ="" NAME ="sp_ETL_PARAMETERS_CALC" OBJECTVERSION ="1" REUSABLE ="NO" TYPE ="Stored Procedure" VERSIONNUMBER ="1">
            <TRANSFORMFIELD DATATYPE ="integer" DEFAULTVALUE ="ERROR(&apos;transformation error&apos;)" DESCRIPTION ="" NAME ="RETURN_VALUE" PICTURETEXT ="" PORTTYPE ="RETURN/OUTPUT" PRECISION ="10" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_NAME" PICTURETEXT ="" PORTTYPE ="INPUT" PRECISION ="100" SCALE ="0"/>
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="PARAM_FILE_NAME" PICTURETEXT ="" PORTTYPE ="INPUT" PRECISION ="100" SCALE ="0"/>
            <TABLEATTRIBUTE NAME ="Stored Procedure Name" VALUE ="dwh.sp_ETL_PARAMETERS_CALC(TRANSACTION_ID,KFK_ISSUED_DRUG)"/>
            <TABLEATTRIBUTE NAME ="Connection Information" VALUE ="Dw_Management"/>
        </TRANSFORMATION>
        <TRANSFORMATION DESCRIPTION ="" NAME ="SQ_DUAL" OBJECTVERSION ="1" REUSABLE ="NO" TYPE ="Source Qualifier" VERSIONNUMBER ="1">
            <TRANSFORMFIELD DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="DUMMY" PICTURETEXT ="" PORTTYPE ="INPUT/OUTPUT" PRECISION ="1" SCALE ="0"/>
        </TRANSFORMATION>
        <INSTANCE DESCRIPTION ="" NAME ="FLAT_FILE" TRANSFORMATION_NAME ="FLAT_FILE" TRANSFORMATION_TYPE ="Target Definition" TYPE ="TARGET"/>
        <INSTANCE DBDNAME ="SQL-DWH-DW_Management" DESCRIPTION ="" NAME ="DUAL" TRANSFORMATION_NAME ="DUAL" TRANSFORMATION_TYPE ="Source Definition" TYPE ="SOURCE"/>
        <INSTANCE DESCRIPTION ="" NAME ="sp_ETL_PARAMETERS_CALC" REUSABLE ="NO" TRANSFORMATION_NAME ="sp_ETL_PARAMETERS_CALC" TRANSFORMATION_TYPE ="Stored Procedure" TYPE ="TRANSFORMATION"/>
        <INSTANCE DESCRIPTION ="" NAME ="SQ_DUAL" REUSABLE ="NO" TRANSFORMATION_NAME ="SQ_DUAL" TRANSFORMATION_TYPE ="Source Qualifier" TYPE ="TRANSFORMATION">
            <ASSOCIATED_SOURCE_INSTANCE NAME ="DUAL"/>
        </INSTANCE>
        <CONNECTOR FROMFIELD ="DUMMY" FROMINSTANCE ="DUAL" FROMINSTANCETYPE ="Source Definition" TOFIELD ="DUMMY" TOINSTANCE ="SQ_DUAL" TOINSTANCETYPE ="Source Qualifier"/>
        <CONNECTOR FROMFIELD ="DUMMY" FROMINSTANCE ="SQ_DUAL" FROMINSTANCETYPE ="Source Qualifier" TOFIELD ="PARAM_FILE_VALUE" TOINSTANCE ="FLAT_FILE" TOINSTANCETYPE ="Target Definition"/>
        <TARGETLOADORDER ORDER ="1" TARGETINSTANCE ="FLAT_FILE"/>
        <ERPINFO/>
    </MAPPING>
    <CONFIG DESCRIPTION ="Default session configuration object" ISDEFAULT ="YES" NAME ="default_session_config" VERSIONNUMBER ="21">
        <ATTRIBUTE NAME ="Advanced" VALUE =""/>
        <ATTRIBUTE NAME ="Constraint based load ordering" VALUE ="NO"/>
        <ATTRIBUTE NAME ="Cache LOOKUP() function" VALUE ="YES"/>
        <ATTRIBUTE NAME ="Default buffer block size" VALUE ="Auto"/>
        <ATTRIBUTE NAME ="Optimization Level" VALUE ="Medium"/>
        <ATTRIBUTE NAME ="DateTime Format String" VALUE ="MM/DD/YYYY HH24:MI:SS.US"/>
        <ATTRIBUTE NAME ="Stop on errors" VALUE ="1"/>
    </CONFIG>
    <WORKFLOW DESCRIPTION ="" ISENABLED ="YES" ISRUNNABLESERVICE ="NO" ISSERVICE ="NO" ISVALID ="YES" NAME ="__WF_NAME__" REUSABLE_SCHEDULER ="NO" SCHEDULERNAME ="Scheduler" SERVERNAME ="Int_Prod" SERVER_DOMAINNAME ="Domain_DW_QA" SUSPEND_ON_ERROR ="NO" TASKS_MUST_RUN_ON_SERVER ="NO" VERSIONNUMBER ="2">
        <SCHEDULER DESCRIPTION ="" NAME ="Scheduler" REUSABLE ="NO" VERSIONNUMBER ="2">
            <SCHEDULEINFO SCHEDULETYPE ="ONDEMAND"/>
        </SCHEDULER>
        <TASK DESCRIPTION ="" NAME ="Assignment" REUSABLE ="NO" TYPE ="Assignment" VERSIONNUMBER ="2">
            <ATTRIBUTE NAME ="Assignment Condition" VALUE =""/>
            <VALUEPAIR EXECORDER ="1" NAME ="$$WF_PARAMETER_FILE_NAME" REVERSEASSIGNMENT ="NO" VALUE ="&apos;__FILE_NAME__.par&apos;"/>
            <VALUEPAIR EXECORDER ="2" NAME ="$$PARAM_CODE" REVERSEASSIGNMENT ="NO" VALUE ="__PARAM_CODE__"/>
            <VALUEPAIR EXECORDER ="3" NAME ="$$PARAMETER_CODES" REVERSEASSIGNMENT ="NO" VALUE ="&apos;__PARAM_CODE__&apos;"/>
        </TASK>
        <TASK DESCRIPTION ="" NAME ="Start" REUSABLE ="NO" TYPE ="Start" VERSIONNUMBER ="2"/>
        <SESSION DESCRIPTION ="" ISVALID ="YES" MAPPINGNAME ="m_param_calc_TRANSACTION_ID" NAME ="s_m_param_calc_TRANSACTION_ID" REUSABLE ="NO" SORTORDER ="Binary" VERSIONNUMBER ="2">
            <SESSTRANSFORMATIONINST ISREPARTITIONPOINT ="YES" PARTITIONTYPE ="PASS THROUGH" PIPELINE ="2" SINSTANCENAME ="FLAT_FILE" STAGE ="1" TRANSFORMATIONNAME ="FLAT_FILE" TRANSFORMATIONTYPE ="Target Definition">
                <FLATFILE CODEPAGE ="MS1255" CONSECDELIMITERSASONE ="NO" DELIMITED ="YES" DELIMITERS ="," ESCAPE_CHARACTER ="" KEEPESCAPECHAR ="NO" LINESEQUENTIAL ="NO" MULTIDELIMITERSASAND ="NO" NULLCHARTYPE ="ASCII" NULL_CHARACTER ="*" PADBYTES ="1" QUOTE_CHARACTER ="NONE" REPEATABLE ="NO" ROWDELIMITER ="0" SKIPROWS ="0" STRIPTRAILINGBLANKS ="NO"/>
            </SESSTRANSFORMATIONINST>
            <CONFIGREFERENCE REFOBJECTNAME ="default_session_config" TYPE ="Session config">
                <ATTRIBUTE NAME ="Maximum Memory Allowed For Auto Memory Attributes" VALUE ="512MB"/>
                <ATTRIBUTE NAME ="Save session log for these runs" VALUE ="3"/>
            </CONFIGREFERENCE>
            <SESSIONEXTENSION NAME ="File Writer" SINSTANCENAME ="FLAT_FILE" SUBTYPE ="File Writer" TRANSFORMATIONTYPE ="Target Definition" TYPE ="WRITER">
                <CONNECTIONREFERENCE CNXREFNAME ="Connection" CONNECTIONNAME ="" CONNECTIONNUMBER ="1" CONNECTIONSUBTYPE ="" CONNECTIONTYPE ="" VARIABLE =""/>
                <ATTRIBUTE NAME ="Merge Type" VALUE ="No Merge"/>
                <ATTRIBUTE NAME ="Merge File Directory" VALUE ="$PMTargetFileDir&#x5c;"/>
                <ATTRIBUTE NAME ="Output file directory" VALUE ="$PMTargetFileDir&#x5c;"/>
                <ATTRIBUTE NAME ="Output filename" VALUE ="flat_file1.out"/>
            </SESSIONEXTENSION>
            <ATTRIBUTE NAME ="General Options" VALUE =""/>
            <ATTRIBUTE NAME ="Write Backward Compatible Session Log File" VALUE ="NO"/>
            <ATTRIBUTE NAME ="Session Log File Name" VALUE ="s_m_param_calc_TRANSACTION_ID.log"/>
            <ATTRIBUTE NAME ="Session Log File directory" VALUE ="$PMSessionLogDir&#x5c;"/>
            <ATTRIBUTE NAME ="Parameter Filename" VALUE =""/>
            <ATTRIBUTE NAME ="Enable Test Load" VALUE ="NO"/>
            <ATTRIBUTE NAME ="Treat source rows as" VALUE ="Insert"/>
            <ATTRIBUTE NAME ="Commit Type" VALUE ="Target"/>
            <ATTRIBUTE NAME ="Commit Interval" VALUE ="10000"/>
            <ATTRIBUTE NAME ="Commit On End Of File" VALUE ="YES"/>
            <ATTRIBUTE NAME ="Rollback Transactions on Errors" VALUE ="NO"/>
            <ATTRIBUTE NAME ="Recovery Strategy" VALUE ="Fail task and continue workflow"/>
        </SESSION>
        <SESSION DESCRIPTION ="" ISVALID ="YES" MAPPINGNAME ="Shortcut_to_m_Parameter_File" NAME ="s_Shortcut_to_m_Parameter_File" REUSABLE ="NO" SORTORDER ="Binary" VERSIONNUMBER ="2">
            <SESSTRANSFORMATIONINST ISREPARTITIONPOINT ="YES" PARTITIONTYPE ="PASS THROUGH" PIPELINE ="1" SINSTANCENAME ="FLAT_FILE" STAGE ="1" TRANSFORMATIONNAME ="FLAT_FILE" TRANSFORMATIONTYPE ="Target Definition">
                <FLATFILE CODEPAGE ="MS1255" CONSECDELIMITERSASONE ="NO" DELIMITED ="YES" DELIMITERS ="," ESCAPE_CHARACTER ="" KEEPESCAPECHAR ="NO" LINESEQUENTIAL ="NO" MULTIDELIMITERSASAND ="NO" NULLCHARTYPE ="ASCII" NULL_CHARACTER ="*" PADBYTES ="1" QUOTE_CHARACTER ="NONE" REPEATABLE ="NO" ROWDELIMITER ="0" SKIPROWS ="0" STRIPTRAILINGBLANKS ="NO"/>
            </SESSTRANSFORMATIONINST>
            <CONFIGREFERENCE REFOBJECTNAME ="default_session_config" TYPE ="Session config">
                <ATTRIBUTE NAME ="Maximum Memory Allowed For Auto Memory Attributes" VALUE ="512MB"/>
                <ATTRIBUTE NAME ="Maximum Percentage of Total Memory Allowed For Auto Memory Attributes" VALUE ="5"/>
                <ATTRIBUTE NAME ="Save session log for these runs" VALUE ="3"/>
            </CONFIGREFERENCE>
            <SESSIONCOMPONENT REFOBJECTNAME ="presession_variable_assignment" REUSABLE ="NO" TYPE ="Pre-session variable assignment">
                <TASK DESCRIPTION ="" NAME ="presession_variable_assignment" REUSABLE ="NO" TYPE ="Command" VERSIONNUMBER ="2">
                    <ATTRIBUTE NAME ="Fail task if any command fails" VALUE ="NO"/>
                    <ATTRIBUTE NAME ="Recovery Strategy" VALUE ="Fail task and continue workflow"/>
                </TASK>
                <VALUEPAIR EXECORDER ="1" NAME ="$$m_PARAMETER_CODES" REVERSEASSIGNMENT ="NO" VALUE ="$$PARAMETER_CODES"/>
            </SESSIONCOMPONENT>
            <SESSIONEXTENSION NAME ="File Writer" SINSTANCENAME ="FLAT_FILE" SUBTYPE ="File Writer" TRANSFORMATIONTYPE ="Target Definition" TYPE ="WRITER">
                <CONNECTIONREFERENCE CNXREFNAME ="Connection" CONNECTIONNAME ="" CONNECTIONNUMBER ="1" CONNECTIONSUBTYPE ="" CONNECTIONTYPE ="" VARIABLE =""/>
                <ATTRIBUTE NAME ="Merge Type" VALUE ="No Merge"/>
                <ATTRIBUTE NAME ="Merge File Directory" VALUE ="$PMTargetFileDir&#x5c;"/>
                <ATTRIBUTE NAME ="Output file directory" VALUE ="$PMRootDir&#x5c;ParamFiles&#x5c;"/>
                <ATTRIBUTE NAME ="Output filename" VALUE ="$$wf_PARAMETER_FILE_NAME"/>
            </SESSIONEXTENSION>
            <SESSIONEXTENSION NAME ="Relational Reader" SINSTANCENAME ="SQ_ETL_PARAMETERS_HEADERS" SUBTYPE ="Relational Reader" TRANSFORMATIONTYPE ="Source Qualifier" TYPE ="READER">
                <CONNECTIONREFERENCE CNXREFNAME ="DB Connection" CONNECTIONNAME ="DW_Management" CONNECTIONNUMBER ="1" CONNECTIONSUBTYPE ="Microsoft SQL Server" CONNECTIONTYPE ="Relational" VARIABLE =""/>
            </SESSIONEXTENSION>
            <ATTRIBUTE NAME ="General Options" VALUE =""/>
            <ATTRIBUTE NAME ="Write Backward Compatible Session Log File" VALUE ="NO"/>
            <ATTRIBUTE NAME ="Session Log File Name" VALUE ="s_Shortcut_to_m_Parameter_File.log"/>
            <ATTRIBUTE NAME ="Session Log File directory" VALUE ="$PMSessionLogDir&#x5c;"/>
            <ATTRIBUTE NAME ="Parameter Filename" VALUE =""/>
            <ATTRIBUTE NAME ="Enable Test Load" VALUE ="NO"/>
            <ATTRIBUTE NAME ="Treat source rows as" VALUE ="Insert"/>
            <ATTRIBUTE NAME ="Commit Type" VALUE ="Target"/>
            <ATTRIBUTE NAME ="Commit Interval" VALUE ="10000"/>
            <ATTRIBUTE NAME ="Commit On End Of File" VALUE ="YES"/>
            <ATTRIBUTE NAME ="Rollback Transactions on Errors" VALUE ="NO"/>
            <ATTRIBUTE NAME ="Recovery Strategy" VALUE ="Fail task and continue workflow"/>
        </SESSION>
        <TASKINSTANCE DESCRIPTION ="" FAIL_PARENT_IF_INSTANCE_DID_NOT_RUN ="NO" FAIL_PARENT_IF_INSTANCE_FAILS ="YES" ISENABLED ="YES" NAME ="s_m_param_calc_TRANSACTION_ID" REUSABLE ="NO" TASKNAME ="s_m_param_calc_TRANSACTION_ID" TASKTYPE ="Session" TREAT_INPUTLINK_AS_AND ="YES"/>
        <TASKINSTANCE DESCRIPTION ="" FAIL_PARENT_IF_INSTANCE_DID_NOT_RUN ="NO" FAIL_PARENT_IF_INSTANCE_FAILS ="YES" ISENABLED ="YES" NAME ="Assignment" REUSABLE ="NO" TASKNAME ="Assignment" TASKTYPE ="Assignment" TREAT_INPUTLINK_AS_AND ="YES"/>
        <TASKINSTANCE DESCRIPTION ="" ISENABLED ="YES" NAME ="Start" REUSABLE ="NO" TASKNAME ="Start" TASKTYPE ="Start"/>
        <TASKINSTANCE DESCRIPTION ="" FAIL_PARENT_IF_INSTANCE_DID_NOT_RUN ="NO" FAIL_PARENT_IF_INSTANCE_FAILS ="YES" ISENABLED ="YES" NAME ="s_Shortcut_to_m_Parameter_File" REUSABLE ="NO" TASKNAME ="s_Shortcut_to_m_Parameter_File" TASKTYPE ="Session" TREAT_INPUTLINK_AS_AND ="YES"/>
        <WORKFLOWLINK CONDITION ="$Assignment.Status=SUCCEEDED" FROMTASK ="Assignment" TOTASK ="s_m_param_calc_TRANSACTION_ID"/>
        <WORKFLOWLINK CONDITION ="" FROMTASK ="Start" TOTASK ="Assignment"/>
        <WORKFLOWLINK CONDITION ="$s_m_param_calc_TRANSACTION_ID.Status=SUCCEEDED" FROMTASK ="s_m_param_calc_TRANSACTION_ID" TOTASK ="s_Shortcut_to_m_Parameter_File"/>
        <WORKFLOWVARIABLE DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="The time this task started" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$s_m_param_calc_TRANSACTION_ID.StartTime" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="The time this task completed" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$s_m_param_calc_TRANSACTION_ID.EndTime" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="Status of this task&apos;s execution" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$s_m_param_calc_TRANSACTION_ID.Status" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="Status of the previous task that is not disabled" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$s_m_param_calc_TRANSACTION_ID.PrevTaskStatus" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="The time this task started" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$Assignment.StartTime" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="The time this task completed" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$Assignment.EndTime" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="Status of this task&apos;s execution" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$Assignment.Status" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="The time this task started" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$Start.StartTime" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="The time this task completed" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$Start.EndTime" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="The time this task started" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$s_Shortcut_to_m_Parameter_File.StartTime" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="The time this task completed" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$s_Shortcut_to_m_Parameter_File.EndTime" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="Status of this task&apos;s execution" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$s_Shortcut_to_m_Parameter_File.Status" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="nstring" DEFAULTVALUE ="" DESCRIPTION ="" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$$WF_PARAMETER_FILE_NAME" USERDEFINED ="YES"/>
        <WORKFLOWVARIABLE DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$$PARAM_CODE" USERDEFINED ="YES"/>
        <WORKFLOWVARIABLE DATATYPE ="nstring" DEFAULTVALUE ="" DESCRIPTION ="" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$$PARAMETER_CODES" USERDEFINED ="YES"/>
        <ATTRIBUTE NAME ="Parameter Filename" VALUE ="$PMRootDir&#x5c;ParamFiles&#x5c;__FILE_NAME__.par"/>
        <ATTRIBUTE NAME ="Write Backward Compatible Workflow Log File" VALUE ="NO"/>
        <ATTRIBUTE NAME ="Workflow Log File Name" VALUE ="__WF_NAME__.log"/>
        <ATTRIBUTE NAME ="Workflow Log File Directory" VALUE ="$PMWorkflowLogDir&#x5c;"/>
        <ATTRIBUTE NAME ="Service Level Name" VALUE ="Default"/>
        <ATTRIBUTE NAME ="Expected Service Time" VALUE ="1"/>
    </WORKFLOW>
</FOLDER>
</REPOSITORY>
</POWERMART>"""

def generate_wf_parameters(topic, file_name, param_code, folder_name="DW_Drugs"):
    """
    Generate WF_PARAMETERS XML for Informatica PowerCenter (embedded template).
    topic:       business topic (e.g. ISSUE_DRUG)  → WF name: WF_PARAMETERS_ISSUE_DRUG
    file_name:   parameter file base name without .par extension (e.g. KFK_ISSUED_DRUG)
    param_code:  numeric parameter code (e.g. 230)
    folder_name: Informatica folder name
    """
    now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    wf_name = f"WF_PARAMETERS_{topic.strip().upper()}"
    file_name_upper = file_name.strip().upper()
    param_code_str = str(param_code).strip()
    
    # Get template and substitute placeholders
    xml = get_wf_parameters_template()
    xml = xml.replace("__CREATION_DATE__", now)
    xml = xml.replace("__FOLDER_NAME__", folder_name)
    xml = xml.replace("__WF_NAME__", wf_name)
    xml = xml.replace("__FILE_NAME__", file_name_upper)
    xml = xml.replace("__PARAM_CODE__", param_code_str)
    
    return xml


# =====================================================================
# WF_DELTA - WORKFLOW XML GENERATOR
# =====================================================================

def get_wf_delta_template():
    """
    Return embedded XML template for WF_DELTA workflow (Informatica PowerCenter).
    Placeholders: __CREATION_DATE__, __FOLDER_NAME__, __WF_NAME__, __FILE_NAME__
    """
    return """<?xml version="1.0" encoding="windows-1255"?>
<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">
<POWERMART CREATION_DATE="__CREATION_DATE__" REPOSITORY_VERSION="187.96">
<REPOSITORY NAME="InfoDW_QA_Rep" VERSION="187" CODEPAGE="MS1255" DATABASETYPE="Microsoft SQL Server">
<FOLDER NAME="__FOLDER_NAME__" GROUP="" OWNER="Administrator" SHARED="NOTSHARED" DESCRIPTION="" PERMISSIONS="rwx------" UUID="620f71cd-f2d3-4541-9b90-9c08ea2afbf8">
    <WORKFLOW DESCRIPTION ="" ISENABLED ="YES" ISRUNNABLESERVICE ="NO" ISSERVICE ="NO" ISVALID ="NO" NAME ="__WF_NAME__" REUSABLE_SCHEDULER ="NO" SCHEDULERNAME ="Scheduler" SERVERNAME ="Int_Prod" SERVER_DOMAINNAME ="Domain_DW_QA" SUSPEND_ON_ERROR ="NO" TASKS_MUST_RUN_ON_SERVER ="NO" VERSIONNUMBER ="1">
        <SCHEDULER DESCRIPTION ="" NAME ="Scheduler" REUSABLE ="NO" VERSIONNUMBER ="1">
            <SCHEDULEINFO SCHEDULETYPE ="ONDEMAND"/>
        </SCHEDULER>
        <TASK DESCRIPTION ="" NAME ="Start" REUSABLE ="NO" TYPE ="Start" VERSIONNUMBER ="1"/>
        <TASKINSTANCE DESCRIPTION ="" ISENABLED ="YES" NAME ="Start" REUSABLE ="NO" TASKNAME ="Start" TASKTYPE ="Start"/>
        <WORKFLOWVARIABLE DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="The time this task started" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$Start.StartTime" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="date/time" DEFAULTVALUE ="" DESCRIPTION ="The time this task completed" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$Start.EndTime" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="Status of this task&apos;s execution" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$Start.Status" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="Status of the previous task that is not disabled" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$Start.PrevTaskStatus" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="integer" DEFAULTVALUE ="" DESCRIPTION ="Error code for this task&apos;s execution" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$Start.ErrorCode" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="string" DEFAULTVALUE ="" DESCRIPTION ="Error message for this task&apos;s execution" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$Start.ErrorMsg" USERDEFINED ="NO"/>
        <WORKFLOWVARIABLE DATATYPE ="nstring" DEFAULTVALUE ="" DESCRIPTION ="" ISNULL ="NO" ISPERSISTENT ="NO" NAME ="$$TRANSACTION_ID" USERDEFINED ="YES"/>
        <ATTRIBUTE NAME ="Parameter Filename" VALUE ="$PMRootDir&#x5c;ParamFiles&#x5c;__FILE_NAME__.par"/>
        <ATTRIBUTE NAME ="Write Backward Compatible Workflow Log File" VALUE ="NO"/>
        <ATTRIBUTE NAME ="Workflow Log File Name" VALUE ="__WF_NAME__.log"/>
        <ATTRIBUTE NAME ="Workflow Log File Directory" VALUE ="$PMWorkflowLogDir&#x5c;"/>
        <ATTRIBUTE NAME ="Save Workflow log by" VALUE ="By runs"/>
        <ATTRIBUTE NAME ="Save workflow log for these runs" VALUE ="0"/>
        <ATTRIBUTE NAME ="Service Name" VALUE =""/>
        <ATTRIBUTE NAME ="Service Timeout" VALUE ="0"/>
        <ATTRIBUTE NAME ="Is Service Visible" VALUE ="NO"/>
        <ATTRIBUTE NAME ="Is Service Protected" VALUE ="NO"/>
        <ATTRIBUTE NAME ="Fail task after wait time" VALUE ="0"/>
        <ATTRIBUTE NAME ="Enable HA recovery" VALUE ="NO"/>
        <ATTRIBUTE NAME ="Automatically recover terminated tasks" VALUE ="NO"/>
        <ATTRIBUTE NAME ="Service Level Name" VALUE ="Default"/>
        <ATTRIBUTE NAME ="Allow concurrent run with unique run instance name" VALUE ="NO"/>
        <ATTRIBUTE NAME ="Allow concurrent run with same run instance name" VALUE ="NO"/>
        <ATTRIBUTE NAME ="Maximum number of concurrent runs" VALUE ="0"/>
        <ATTRIBUTE NAME ="Assigned Web Services Hubs" VALUE =""/>
        <ATTRIBUTE NAME ="Maximum number of concurrent runs per Hub" VALUE ="1000"/>
        <ATTRIBUTE NAME ="Expected Service Time" VALUE ="1"/>
    </WORKFLOW>
</FOLDER>
</REPOSITORY>
</POWERMART>"""

def generate_wf_delta(topic, file_name, folder_name="DW_Drugs"):
    """
    Generate WF_DELTA XML for Informatica PowerCenter (embedded template).
    topic:       business topic (e.g. ISSUE_DRUG)  → WF name: WF_DELTA_ISSUE_DRUG
    file_name:   parameter file base name without .par extension (e.g. KFK_ISSUED_DRUG)
    folder_name: Informatica folder name
    """
    now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    wf_name = f"WF_DELTA_{topic.strip().upper()}"
    file_name_upper = file_name.strip().upper()
    
    # Get template and substitute placeholders
    xml = get_wf_delta_template()
    xml = xml.replace("__CREATION_DATE__", now)
    xml = xml.replace("__FOLDER_NAME__", folder_name)
    xml = xml.replace("__WF_NAME__", wf_name)
    xml = xml.replace("__FILE_NAME__", file_name_upper)
    
    return xml


# =====================================================================
# GENERATE DDL DELTA TABLES
# =====================================================================

def generate_ddl_delta_tables(ddl_text):
    """
    Parse a DDL script with one or more CREATE TABLE statements.
    For each table ending with _MASTER  → generate _KEY_STG, _STG, _CLN in schema DELTA.
    For each table ending with _DETAIL  → generate _CLN in schema DELTA.
    IDENTITY and DEFAULT clauses are stripped; only column name + datatype are kept.
    """
    # Split by CREATE TABLE (preserving it at start of each part)
    parts = re.split(r'(?=CREATE\s+TABLE)', ddl_text, flags=re.IGNORECASE)
    
    block_re = re.compile(
        r'CREATE\s+TABLE\s+(?:\[?\w+\]?\.)?\[?(\w+)\]?\s*\((.*?)\)\s*(?:ON|;|GO)',
        re.IGNORECASE | re.DOTALL,
    )
    col_pattern = re.compile(
        r'^\[(\w+)\]\s+\[(\w+)\](?:\(([^)]+)\))?',
        re.IGNORECASE,
    )

    def build_col_list(cols):
        lines = []
        for i, (col_name, type_sql) in enumerate(cols):
            comma = "," if i < len(cols) - 1 else ""
            lines.append(f"\t[{col_name}] {type_sql}{comma}")
        return lines

    output_lines = []

    for part in parts:
        if not part.strip():
            continue
        m = block_re.search(part)
        if not m:
            continue
        
        table_name = m.group(1)
        body = m.group(2)
        upper_name = table_name.upper()

        if not (upper_name.endswith('_MASTER') or upper_name.endswith('_DETAIL')):
            continue

        # Parse columns – strip IDENTITY / DEFAULT / NULL keywords
        cols = []
        for line in body.splitlines():
            line = line.strip().rstrip(',')
            if re.match(r'(CONSTRAINT|PRIMARY|UNIQUE|CHECK|FOREIGN)', line, re.IGNORECASE):
                continue
            cm = col_pattern.match(line)
            if not cm:
                continue
            col_name = cm.group(1)
            base_type = cm.group(2)
            precision_str = (cm.group(3) or "").strip()
            type_sql = f"[{base_type}]({precision_str})" if precision_str else f"[{base_type}]"
            cols.append((col_name, type_sql))

        if not cols:
            continue

        if upper_name.endswith('_MASTER'):
            # 1. _KEY_STG  (fixed 3 columns from source with original lengths)
            key_stg_name = f"{table_name}_KEY_STG"
            
            # Find lengths from source columns
            entity_id_col = None
            timestamp_col = None
            offset_col = None
            
            for col_name, type_sql in cols:
                col_lower = col_name.lower()
                if col_lower == 'entity_id':
                    entity_id_col = type_sql
                elif col_lower == '_data_timestamp_sequence' or col_lower == '_data_timestamp':
                    timestamp_col = type_sql
                elif col_lower == 'offset':
                    offset_col = type_sql
            
            # Use defaults if not found
            entity_id_type = entity_id_col if entity_id_col else '[varchar](100)'
            timestamp_type = timestamp_col if timestamp_col else '[varchar](50)'
            offset_type = offset_col if offset_col else '[bigint]'
            
            output_lines += [
                f"CREATE TABLE [DELTA].[{key_stg_name}] (",
                f"\t[ENTITY_ID] {entity_id_type} NOT NULL,",
                f"\t[timestamp_sequence] {timestamp_type} NOT NULL,",
                f"\t[OFFSET] {offset_type} NULL",
                ");",
                "",
            ]

            # 2. _STG  (all columns from source)
            stg_name = f"{table_name}_STG"
            output_lines.append(f"CREATE TABLE [DELTA].[{stg_name}] (")
            output_lines += build_col_list(cols)
            output_lines += [");", ""]

            # 3. _CLN  (all columns from source)
            cln_name = f"{table_name}_CLN"
            output_lines.append(f"CREATE TABLE [DELTA].[{cln_name}] (")
            output_lines += build_col_list(cols)
            output_lines += [");", ""]

        elif upper_name.endswith('_DETAIL'):
            # _CLN only
            cln_name = f"{table_name}_CLN"
            output_lines.append(f"CREATE TABLE [DELTA].[{cln_name}] (")
            output_lines += build_col_list(cols)
            output_lines += [");", ""]

    if not output_lines:
        return "-- לא נמצאו טבלאות המסתיימות ב-_MASTER או _DETAIL בקלט"

    return "\n".join(output_lines)


# =====================================================================
# STREAMLIT UI
# =====================================================================

def main():
    st.set_page_config(page_title="Informatica XML Generator", layout="wide")
    
    st.markdown("""
    <style>
    h1, h2, h3 { text-align: right; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🔧 Informatica PowerCenter XML Generator")
    st.markdown("<h2 style='text-align: right; direction: rtl;'>יוצר XML עבור 4 שלבי Delta</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    delta_stage = st.radio(
        "בחר את שלב ה-Delta:",
        ["DELTA 000 - Master Key STG", "DELTA 010 - Master STG", "DELTA 020 - Master CLN", "DELTA 030 - Communication Detail CLN", "GENERATE DDL DELTA TABLES", "WF PARAMETERS", "WF DELTA"],
        index=0
    )

    if "WF PARAMETERS" in delta_stage:
        st.markdown("### יצירת XML לוורקפלואו WF_PARAMETERS")
        st.info("הזן את הפרטים ליצירת ה-Workflow. שם ה-WF ייווצר אוטומטית בתבנית: WF_PARAMETERS_<נושא>.")
        col_wf1, col_wf2 = st.columns(2)
        with col_wf1:
            wf_topic = st.text_input(
                "נושא עסקי (לשם ה-WF):",
                placeholder="לדוגמא: ISSUE_DRUG",
                key="wf_topic"
            ).strip().upper()
            wf_file_name = st.text_input(
                "שם קובץ הפרמטרים (ללא סיומת .par):",
                placeholder="לדוגמא: KFK_ISSUED_DRUG",
                key="wf_file_name"
            ).strip().upper()
        with col_wf2:
            wf_param_code = st.text_input(
                "קוד פרמטר ($$PARAM_CODE):",
                placeholder="לדוגמא: 230",
                key="wf_param_code"
            ).strip()
            if wf_topic:
                st.info(f"שם ה-WF שייווצר: **WF_PARAMETERS_{wf_topic}**")
        ddl_input = ""
        ddl_master_input = None
        ddl_detail_input = None
    elif "WF DELTA" in delta_stage:
        st.markdown("### יצירת XML לוורקפלואו WF_DELTA")
        st.info("הזן את הפרטים ליצירת ה-Workflow. שם ה-WF ייווצר אוטומטית בתבנית: WF_DELTA_<נושא>.")
        col_wf1, col_wf2 = st.columns(2)
        with col_wf1:
            wf_delta_topic = st.text_input(
                "נושא עסקי (לשם ה-WF):",
                placeholder="לדוגמא: ISSUE_DRUG",
                key="wf_delta_topic"
            ).strip().upper()
            wf_delta_file_name = st.text_input(
                "שם קובץ הפרמטרים (ללא סיומת .par):",
                placeholder="לדוגמא: KFK_ISSUED_DRUG",
                key="wf_delta_file_name"
            ).strip().upper()
        with col_wf2:
            wf_delta_folder = st.text_input(
                "שם FOLDER באינפורמטיקה:",
                value="DW_Drugs",
                key="wf_delta_folder"
            ).strip() or "DW_Drugs"
            if wf_delta_topic:
                st.info(f"שם ה-WF שייווצר: **WF_DELTA_{wf_delta_topic}**")
        ddl_input = ""
        ddl_master_input = None
        ddl_detail_input = None
        folder_name = wf_delta_folder
        wf_topic = None
        wf_file_name = None
        wf_param_code = None
    elif "GENERATE DDL DELTA TABLES" in delta_stage:
        st.markdown("### הזן סקריפט CREATE TABLE (יכול להכיל מספר טבלאות)")
        st.info("טבלאות המסתיימות ב-_MASTER יניבו: _KEY_STG, _STG, _CLN בסכמה DELTA.\nטבלאות המסתיימות ב-_DETAIL יניבו: _CLN בסכמה DELTA.")
        ddl_input = st.text_area(
            "הדבק DDL:",
            height=250,
            placeholder="CREATE TABLE [schema].[table] (...)",
            key="ddl_input"
        )
        ddl_master_input = None
        ddl_detail_input = None
    elif "DELTA 030" in delta_stage:
        st.markdown("### הזן שתי טבלאות DDL - MASTER ו-DETAIL")
        st.info("הזן את טבלת ה-MASTER בתיבה הראשונה ואת טבלת ה-DETAIL בתיבה השנייה.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### טבלה MASTER")
            ddl_master_input = st.text_area(
                "הדבק DDL של טבלת MASTER:",
                height=250,
                placeholder="CREATE TABLE [schema].[table_master] (...)",
                key="ddl_master_input"
            )
        with col2:
            st.markdown("#### טבלה DETAIL")
            ddl_detail_input = st.text_area(
                "הדבק DDL של טבלת DETAIL:",
                height=250,
                placeholder="CREATE TABLE [schema].[table_detail] (...)",
                key="ddl_detail_input"
            )
        ddl_input = f"{ddl_master_input}\n\n{ddl_detail_input}"
    else:
        st.markdown("### הזן CREATE TABLE DDL")
        ddl_input = st.text_area(
            "הדבק DDL:",
            height=250,
            placeholder="CREATE TABLE [schema].[table] (...)",
            key="ddl_input"
        )
        ddl_master_input = None
        ddl_detail_input = None

    # Folder name input - only for XML modes
    if "GENERATE DDL DELTA TABLES" not in delta_stage and "WF PARAMETERS" not in delta_stage and "WF DELTA" not in delta_stage:
        folder_name = st.text_input(
            "שם FOLDER באינפורמטיקה:",
            value="DW_Drugs",
            key="folder_name_input"
        ).strip() or "DW_Drugs"
    elif "WF PARAMETERS" in delta_stage:
        folder_name = st.text_input(
            "שם FOLDER באינפורמטיקה:",
            value="DW_Drugs",
            key="folder_name_input"
        ).strip() or "DW_Drugs"
    else:
        folder_name = "DW_Drugs"  # Default, won't be used
    
    st.markdown("---")
    
    if "WF PARAMETERS" in delta_stage:
        btn_label = "✨ ייצר WF XML"
    elif "WF DELTA" in delta_stage:
        btn_label = "✨ ייצר WF DELTA XML"
    elif "GENERATE DDL DELTA TABLES" in delta_stage:
        btn_label = "✨ ייצר DDL"
    else:
        btn_label = "✨ ייצר XML"

    if st.button(btn_label, use_container_width=True, type="primary"):
        if "WF PARAMETERS" in delta_stage:
            if not wf_topic:
                st.error("❌ אנא הזן נושא עסקי לשם ה-WF")
            elif not wf_file_name:
                st.error("❌ אנא הזן שם קובץ פרמטרים")
            elif not wf_param_code:
                st.error("❌ אנא הזן קוד פרמטר")
            else:
                with st.spinner("⏳ מעבד..."):
                    try:
                        xml_content = generate_wf_parameters(
                            topic=wf_topic,
                            file_name=wf_file_name,
                            param_code=wf_param_code,
                            folder_name=folder_name
                        )
                        st.session_state.xml_content = xml_content
                        st.session_state.is_ddl_output = False
                        st.session_state.wf_download_name = f"WF_PARAMETERS_{wf_topic}.XML"
                        st.success(f"✅ XML נוצר בהצלחה! שם הקובץ: WF_PARAMETERS_{wf_topic}.XML")
                    except Exception as e:
                        st.error(f"❌ שגיאה: {str(e)}")
        elif "WF DELTA" in delta_stage:
            if not wf_delta_topic:
                st.error("❌ אנא הזן נושא עסקי לשם ה-WF")
            elif not wf_delta_file_name:
                st.error("❌ אנא הזן שם קובץ פרמטרים")
            else:
                with st.spinner("⏳ מעבד..."):
                    try:
                        xml_content = generate_wf_delta(
                            topic=wf_delta_topic,
                            file_name=wf_delta_file_name,
                            folder_name=wf_delta_folder
                        )
                        st.session_state.xml_content = xml_content
                        st.session_state.is_ddl_output = False
                        st.session_state.wf_download_name = f"WF_DELTA_{wf_delta_topic}.XML"
                        st.success(f"✅ XML נוצר בהצלחה! שם הקובץ: WF_DELTA_{wf_delta_topic}.XML")
                    except Exception as e:
                        st.error(f"❌ שגיאה: {str(e)}")
        elif not ddl_input.strip():
            st.error("❌ אנא הדבק DDL")
        elif "DELTA 030" in delta_stage and (not ddl_master_input or not ddl_detail_input or not ddl_master_input.strip() or not ddl_detail_input.strip()):
            st.error("❌ אנא הדבק שתי טבלאות - MASTER ו-DETAIL")
        else:
            with st.spinner("⏳ מעבד..."):
                try:
                    if "GENERATE DDL DELTA TABLES" in delta_stage:
                        result_content = generate_ddl_delta_tables(ddl_input)
                        st.session_state.xml_content = result_content
                        st.session_state.is_ddl_output = True
                        st.success("✅ סקריפט DDL נוצר בהצלחה!")
                    else:
                        st.session_state.is_ddl_output = False
                        if "DELTA 000" in delta_stage:
                            xml_content = generate_delta_000(ddl_input, folder_name=folder_name)
                        elif "DELTA 010" in delta_stage:
                            xml_content = generate_delta_010(ddl_input, folder_name=folder_name)
                        elif "DELTA 020" in delta_stage:
                            xml_content = generate_delta_020(ddl_input, folder_name=folder_name)
                        else:
                            xml_content = generate_delta_030(ddl_input, folder_name=folder_name)
                        st.session_state.xml_content = xml_content
                        st.success("✅ XML נוצר בהצלחה!")
                except Exception as e:
                    st.error(f"❌ שגיאה: {str(e)}")

    if "xml_content" in st.session_state and st.session_state.xml_content:
        st.markdown("---")
        is_ddl = st.session_state.get("is_ddl_output", False)
        if is_ddl:
            st.markdown("### 📄 סקריפט DDL שנוצר")
            with st.expander("הצג DDL", expanded=True):
                st.code(st.session_state.xml_content, language="sql")
            st.download_button(
                label="⬇️ הורד SQL",
                data=st.session_state.xml_content,
                file_name="delta_tables.sql",
                mime="text/plain",
                use_container_width=True,
                type="primary"
            )
        else:
            st.markdown("### 📄 XML שנוצר")
            with st.expander("הצג XML", expanded=False):
                st.code(st.session_state.xml_content, language="xml")
            download_name = st.session_state.get("wf_download_name") or f"informatica_{delta_stage.split()[1]}.xml"
            st.download_button(
                label="⬇️ הורד XML",
                data=st.session_state.xml_content,
                file_name=download_name,
                mime="application/xml",
                use_container_width=True,
                type="primary"
            )


if __name__ == "__main__":
    main()
