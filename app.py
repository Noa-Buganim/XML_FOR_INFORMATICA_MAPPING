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

        src2_name = master_name
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
            source_filter=f"{src2_name}.TRANSACTION_ID is null",
        )

        return _render_powermart_xml(pm)
    except Exception as e:
        return f"<!-- DELTA 030 - ERROR: {e} -->"


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
        ["DELTA 000 - Master Key STG", "DELTA 010 - Master STG", "DELTA 020 - Master CLN", "DELTA 030 - Communication Detail CLN", "GENERATE DDL DELTA TABLES"],
        index=0
    )

    if "GENERATE DDL DELTA TABLES" in delta_stage:
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
    if "GENERATE DDL DELTA TABLES" not in delta_stage:
        folder_name = st.text_input(
            "שם FOLDER באינפורמטיקה:",
            value="DW_Drugs",
            key="folder_name_input"
        ).strip() or "DW_Drugs"
    else:
        folder_name = "DW_Drugs"  # Default, won't be used
    
    st.markdown("---")
    
    btn_label = "✨ ייצר DDL" if "GENERATE DDL DELTA TABLES" in delta_stage else "✨ ייצר XML"
    if st.button(btn_label, use_container_width=True, type="primary"):
        if not ddl_input.strip():
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
            st.download_button(
                label="⬇️ הורד XML",
                data=st.session_state.xml_content,
                file_name=f"informatica_{delta_stage.split()[1]}.xml",
                mime="application/xml",
                use_container_width=True,
                type="primary"
            )


if __name__ == "__main__":
    main()
