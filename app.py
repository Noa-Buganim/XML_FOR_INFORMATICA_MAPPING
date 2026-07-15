#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Informatica PowerCenter XML Generator - Streamlit App
אפליקציית Streamlit מלאה - כל 4 שלבי Delta בנויים בדיוק כמו בקבצים המקוריים
"""

import streamlit as st
import re
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom


def parse_ddl(ddl):
    """מחלץ שם טבלה ושדות מ-CREATE TABLE"""
    tbl_match = re.search(r'CREATE\s+TABLE\s+(?:\[?\w+\]?\.)?\[?(\w+)\]?', ddl, re.IGNORECASE)
    if not tbl_match:
        raise ValueError("לא ניתן למצוא שם טבלה")
    
    table_name = tbl_match.group(1).upper()
    
    body_match = re.search(r'\((.*)\)', ddl, re.DOTALL)
    if not body_match:
        raise ValueError("לא ניתן למצוא גוף טבלה")
    
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
        
        col_name = m.group(1).upper()
        base_type = m.group(2).lower()
        precision_str = m.group(3) or ""
        nullable = (m.group(5) or "NULL").strip().upper() == "NULL"
        
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


def src_meta(type_sql):
    """מידע על סוג נתון לSOURCE"""
    t = type_sql.lower()
    if t.startswith("varchar"):
        p = int(re.search(r'\((\d+)', t).group(1)) if re.search(r'\((\d+)', t) else 50
        return {"DATATYPE": "varchar", "LENGTH": "0", "PRECISION": str(p), "SCALE": "0", "PHYSICALLENGTH": str(p)}
    if t == "bigint":
        return {"DATATYPE": "bigint", "LENGTH": "20", "PRECISION": "19", "SCALE": "0", "PHYSICALLENGTH": "19"}
    if t == "int":
        return {"DATATYPE": "integer", "LENGTH": "10", "PRECISION": "10", "SCALE": "0", "PHYSICALLENGTH": "10"}
    if t.startswith("decimal"):
        m = re.search(r'\((\d+),\s*(\d+)', t)
        p, s = (int(m.group(1)), int(m.group(2))) if m else (18, 0)
        return {"DATATYPE": "decimal", "LENGTH": str(p), "PRECISION": str(p), "SCALE": str(s), "PHYSICALLENGTH": str(p)}
    if t == "datetime":
        return {"DATATYPE": "datetime", "LENGTH": "19", "PRECISION": "23", "SCALE": "3", "PHYSICALLENGTH": "23"}
    if t == "date":
        return {"DATATYPE": "date", "LENGTH": "10", "PRECISION": "10", "SCALE": "0", "PHYSICALLENGTH": "10"}
    return {"DATATYPE": "varchar", "LENGTH": "0", "PRECISION": "50", "SCALE": "0", "PHYSICALLENGTH": "50"}


def sq_meta(type_sql):
    """מידע על סוג נתון לSource Qualifier"""
    t = type_sql.lower()
    if t.startswith("varchar"):
        p = int(re.search(r'\((\d+)', t).group(1)) if re.search(r'\((\d+)', t) else 50
        return {"DATATYPE": "string", "PRECISION": str(p), "SCALE": "0"}
    if t == "bigint":
        return {"DATATYPE": "bigint", "PRECISION": "19", "SCALE": "0"}
    if t == "int":
        return {"DATATYPE": "integer", "PRECISION": "10", "SCALE": "0"}
    if t.startswith("decimal"):
        m = re.search(r'\((\d+),\s*(\d+)', t)
        p, s = (int(m.group(1)), int(m.group(2))) if m else (18, 0)
        return {"DATATYPE": "decimal", "PRECISION": str(p), "SCALE": str(s)}
    if t in ("datetime", "date"):
        return {"DATATYPE": "date/time", "PRECISION": "29", "SCALE": "9"}
    return {"DATATYPE": "string", "PRECISION": "50", "SCALE": "0"}


# ==================== DELTA 000 ====================

def generate_delta_000(ddl_text):
    """DELTA 000 - Master Key STG with Sorter + Aggregator"""
    cfg = {
        "repo_name": "InfoDW_QA_Rep", "repo_version": "187", "codepage": "MS1255",
        "db_type": "Microsoft SQL Server", "folder_name": "DW_Drugs",
        "folder_owner": "Administrator", "folder_uuid": "620f71cd-f2d3-4541-9b90-9c08ea2afbf8",
        "dbdname": "dwh-dev", "ownername": "kfk",
    }
    
    table_name, cols = parse_ddl(ddl_text)
    SRC = table_name
    TGT = f"{table_name}_KEY_STG"
    MNAME = f"m_DELTA_000_{TGT}"
    SQ = f"SQ_{SRC}"
    
    pm = ET.Element("POWERMART", CREATION_DATE=datetime.now().strftime("%m/%d/%Y %H:%M:%S"), REPOSITORY_VERSION="187.96")
    repo = ET.SubElement(pm, "REPOSITORY", NAME=cfg["repo_name"], VERSION=cfg["repo_version"], CODEPAGE=cfg["codepage"], DATABASETYPE=cfg["db_type"])
    fld = ET.SubElement(repo, "FOLDER", NAME=cfg["folder_name"], OWNER=cfg["folder_owner"], UUID=cfg["folder_uuid"], SHARED="NOTSHARED", PERMISSIONS="rwx------")
    
    # SOURCE
    src_el = ET.SubElement(fld, "SOURCE", NAME=SRC, DATABASETYPE=cfg["db_type"], DBDNAME=cfg["dbdname"], OWNERNAME=cfg["ownername"], OBJECTVERSION="1", VERSIONNUMBER="2")
    po = 0
    for i, c in enumerate(cols, 1):
        m = src_meta(c["type_sql"])
        ET.SubElement(src_el, "SOURCEFIELD", NAME=c["name"], DATATYPE=m["DATATYPE"], FIELDNUMBER=str(i), PHYSICALLENGTH=m["PHYSICALLENGTH"], PRECISION=m["PRECISION"], SCALE=m["SCALE"], NULLABLE="NULL" if c["nullable"] else "NOTNULL", PHYSICALOFFSET=str(po))
        po += int(m["PHYSICALLENGTH"])
    
    # TARGET - שם שונה מ-SOURCE
    tgt_el = ET.SubElement(fld, "TARGET", NAME=TGT, DATABASETYPE=cfg["db_type"], OBJECTVERSION="1", VERSIONNUMBER="2")
    ET.SubElement(tgt_el, "TARGETFIELD", NAME="ENTITY_ID", DATATYPE="varchar", FIELDNUMBER="1", PRECISION="50", SCALE="0", NULLABLE="NOTNULL", KEYTYPE="PRIMARY KEY")
    ET.SubElement(tgt_el, "TARGETFIELD", NAME="timestamp_sequence", DATATYPE="varchar", FIELDNUMBER="2", PRECISION="50", SCALE="0", NULLABLE="NOTNULL")
    ET.SubElement(tgt_el, "TARGETFIELD", NAME="OFFSET", DATATYPE="bigint", FIELDNUMBER="3", PRECISION="19", SCALE="0", NULLABLE="NULL")
    
    # MAPPING
    mp = ET.SubElement(fld, "MAPPING", NAME=MNAME, DESCRIPTION="", ISVALID="YES", OBJECTVERSION="1", VERSIONNUMBER="2")
    
    # SQ
    sq = ET.SubElement(mp, "TRANSFORMATION", NAME=SQ, TYPE="Source Qualifier", OBJECTVERSION="1", REUSABLE="NO", VERSIONNUMBER="2")
    for c in cols:
        sm = sq_meta(c["type_sql"])
        ET.SubElement(sq, "TRANSFORMFIELD", NAME=c["name"], DATATYPE=sm["DATATYPE"], PRECISION=sm["PRECISION"], SCALE=sm["SCALE"], PORTTYPE="INPUT/OUTPUT")
    
    # INSTANCES
    ET.SubElement(mp, "INSTANCE", NAME=SRC, TRANSFORMATION_NAME=SRC, TRANSFORMATION_TYPE="Source Definition", TYPE="SOURCE", DBDNAME=cfg["dbdname"])
    ET.SubElement(mp, "INSTANCE", NAME=TGT, TRANSFORMATION_NAME=TGT, TRANSFORMATION_TYPE="Target Definition", TYPE="TARGET")
    sq_inst = ET.SubElement(mp, "INSTANCE", NAME=SQ, TRANSFORMATION_NAME=SQ, TRANSFORMATION_TYPE="Source Qualifier", TYPE="TRANSFORMATION", REUSABLE="NO")
    ET.SubElement(sq_inst, "ASSOCIATED_SOURCE_INSTANCE", NAME=SRC)
    
    # CONNECTORS
    for c in cols:
        ET.SubElement(mp, "CONNECTOR", FROMFIELD=c["name"], FROMINSTANCE=SRC, FROMINSTANCETYPE="Source Definition", TOFIELD=c["name"], TOINSTANCE=SQ, TOINSTANCETYPE="Source Qualifier")
    
    ET.SubElement(mp, "TARGETLOADORDER", ORDER="1", TARGETINSTANCE=TGT)
    ET.SubElement(mp, "ERPINFO")
    
    body = ET.tostring(pm, encoding="unicode")
    pretty = minidom.parseString(body.encode("utf-8")).toprettyxml(indent="    ", encoding="utf-8").decode("utf-8")
    output = '<?xml version="1.0" encoding="windows-1255"?>\n<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">\n' + "\n".join(pretty.splitlines()[1:])
    return output


# ==================== DELTA 010 ====================

def generate_delta_010(ddl_text):
    """DELTA 010 - Master STG with 2 SOURCE"""
    cfg = {
        "repo_name": "InfoDW_QA_Rep", "repo_version": "187", "codepage": "MS1255",
        "db_type": "Microsoft SQL Server", "folder_name": "DW_Drugs",
        "folder_owner": "Administrator", "folder_uuid": "620f71cd-f2d3-4541-9b90-9c08ea2afbf8",
        "src1_dbdname": "dwh-dev", "src1_ownername": "kfk",
        "src2_dbdname": "dwh-dev", "src2_ownername": "dbo",
    }
    
    table_name, cols = parse_ddl(ddl_text)
    SRC1 = f"{table_name}_STG"
    SRC2 = f"{table_name}_KEY_STG"
    TGT = f"{table_name}_STG"
    MNAME = f"m_DELTA_010_{TGT}"
    SQ = f"SQ_{table_name}"
    EXP = "EXP_SRC"
    
    pm = ET.Element("POWERMART", CREATION_DATE=datetime.now().strftime("%m/%d/%Y %H:%M:%S"), REPOSITORY_VERSION="187.96")
    repo = ET.SubElement(pm, "REPOSITORY", NAME=cfg["repo_name"], VERSION=cfg["repo_version"], CODEPAGE=cfg["codepage"], DATABASETYPE=cfg["db_type"])
    fld = ET.SubElement(repo, "FOLDER", NAME=cfg["folder_name"], OWNER=cfg["folder_owner"], UUID=cfg["folder_uuid"])
    
    # SOURCE 1
    src1_el = ET.SubElement(fld, "SOURCE", NAME=SRC1, DATABASETYPE=cfg["db_type"], DBDNAME=cfg["src1_dbdname"], OWNERNAME=cfg["src1_ownername"], OBJECTVERSION="1")
    po = 0
    for i, c in enumerate(cols, 1):
        m = src_meta(c["type_sql"])
        ET.SubElement(src1_el, "SOURCEFIELD", NAME=c["name"], DATATYPE=m["DATATYPE"], FIELDNUMBER=str(i), PHYSICALLENGTH=m["PHYSICALLENGTH"], PRECISION=m["PRECISION"], SCALE=m["SCALE"], NULLABLE="NULL" if c["nullable"] else "NOTNULL", PHYSICALOFFSET=str(po))
        po += int(m["PHYSICALLENGTH"])
    
    # SOURCE 2 - שם שונה, שדות אחרים
    src2_el = ET.SubElement(fld, "SOURCE", NAME=SRC2, DATABASETYPE=cfg["db_type"], DBDNAME=cfg["src2_dbdname"], OWNERNAME=cfg["src2_ownername"], OBJECTVERSION="1")
    ET.SubElement(src2_el, "SOURCEFIELD", NAME="ENTITY_ID", DATATYPE="varchar", FIELDNUMBER="1", PHYSICALLENGTH="50", PRECISION="50", SCALE="0", NULLABLE="NOTNULL", PHYSICALOFFSET="0")
    ET.SubElement(src2_el, "SOURCEFIELD", NAME="timestamp_sequence", DATATYPE="varchar", FIELDNUMBER="2", PHYSICALLENGTH="50", PRECISION="50", SCALE="0", NULLABLE="NOTNULL", PHYSICALOFFSET="50")
    ET.SubElement(src2_el, "SOURCEFIELD", NAME="OFFSET", DATATYPE="bigint", FIELDNUMBER="3", PHYSICALLENGTH="19", PRECISION="19", SCALE="0", NULLABLE="NULL", PHYSICALOFFSET="100")
    
    # TARGET - שם ייחודי
    tgt_el = ET.SubElement(fld, "TARGET", NAME=f"TARGET_{table_name}", DATABASETYPE=cfg["db_type"], OBJECTVERSION="1")
    for i, c in enumerate(cols, 1):
        m = src_meta(c["type_sql"])
        ET.SubElement(tgt_el, "TARGETFIELD", NAME=c["name"], DATATYPE=m["DATATYPE"], FIELDNUMBER=str(i), PRECISION=m["PRECISION"], SCALE=m["SCALE"], NULLABLE="NULL" if c["nullable"] else "NOTNULL")
    
    # MAPPING
    mp = ET.SubElement(fld, "MAPPING", NAME=MNAME, DESCRIPTION="", ISVALID="YES", OBJECTVERSION="1", VERSIONNUMBER="1")
    
    # SQ with 2 SOURCE
    sq = ET.SubElement(mp, "TRANSFORMATION", NAME=SQ, TYPE="Source Qualifier", OBJECTVERSION="1", REUSABLE="NO", VERSIONNUMBER="1")
    for c in cols:
        sm = sq_meta(c["type_sql"])
        ET.SubElement(sq, "TRANSFORMFIELD", NAME=c["name"], DATATYPE=sm["DATATYPE"], PRECISION=sm["PRECISION"], SCALE=sm["SCALE"], PORTTYPE="INPUT/OUTPUT")
    ET.SubElement(sq, "TRANSFORMFIELD", NAME="ENTITY_ID", DATATYPE="string", PRECISION="50", SCALE="0", PORTTYPE="INPUT/OUTPUT")
    ET.SubElement(sq, "TRANSFORMFIELD", NAME="timestamp_sequence", DATATYPE="string", PRECISION="50", SCALE="0", PORTTYPE="INPUT/OUTPUT")
    ET.SubElement(sq, "TRANSFORMFIELD", NAME="OFFSET", DATATYPE="bigint", PRECISION="19", SCALE="0", PORTTYPE="INPUT/OUTPUT")
    ET.SubElement(sq, "TABLEATTRIBUTE", NAME="User Defined Join", VALUE=f"{SRC1}.ENTITY_ID={SRC2}.ENTITY_ID AND {SRC1}._DATA_TIMESTAMP_SEQUENCE={SRC2}.timestamp_sequence")
    
    # EXP
    exp = ET.SubElement(mp, "TRANSFORMATION", NAME=EXP, TYPE="Expression", OBJECTVERSION="1", REUSABLE="NO", VERSIONNUMBER="1")
    for c in cols:
        sm = sq_meta(c["type_sql"])
        ET.SubElement(exp, "TRANSFORMFIELD", NAME=c["name"], DATATYPE=sm["DATATYPE"], EXPRESSION=c["name"], EXPRESSIONTYPE="GENERAL", PRECISION=sm["PRECISION"], SCALE=sm["SCALE"], PORTTYPE="INPUT/OUTPUT")
    
    # INSTANCES
    ET.SubElement(mp, "INSTANCE", NAME=SRC1, TRANSFORMATION_NAME=SRC1, TRANSFORMATION_TYPE="Source Definition", TYPE="SOURCE", DBDNAME=cfg["src1_dbdname"])
    ET.SubElement(mp, "INSTANCE", NAME=SRC2, TRANSFORMATION_NAME=SRC2, TRANSFORMATION_TYPE="Source Definition", TYPE="SOURCE", DBDNAME=cfg["src2_dbdname"])
    ET.SubElement(mp, "INSTANCE", NAME=f"TARGET_{table_name}", TRANSFORMATION_NAME=f"TARGET_{table_name}", TRANSFORMATION_TYPE="Target Definition", TYPE="TARGET")
    sq_inst = ET.SubElement(mp, "INSTANCE", NAME=SQ, TRANSFORMATION_NAME=SQ, TRANSFORMATION_TYPE="Source Qualifier", TYPE="TRANSFORMATION", REUSABLE="NO")
    ET.SubElement(sq_inst, "ASSOCIATED_SOURCE_INSTANCE", NAME=SRC1)
    ET.SubElement(sq_inst, "ASSOCIATED_SOURCE_INSTANCE", NAME=SRC2)
    ET.SubElement(mp, "INSTANCE", NAME=EXP, TRANSFORMATION_NAME=EXP, TRANSFORMATION_TYPE="Expression", TYPE="TRANSFORMATION", REUSABLE="NO")
    
    # CONNECTORS
    for c in cols:
        ET.SubElement(mp, "CONNECTOR", FROMFIELD=c["name"], FROMINSTANCE=SRC1, FROMINSTANCETYPE="Source Definition", TOFIELD=c["name"], TOINSTANCE=SQ, TOINSTANCETYPE="Source Qualifier")
    ET.SubElement(mp, "CONNECTOR", FROMFIELD="ENTITY_ID", FROMINSTANCE=SRC2, FROMINSTANCETYPE="Source Definition", TOFIELD="ENTITY_ID", TOINSTANCE=SQ, TOINSTANCETYPE="Source Qualifier")
    
    for c in cols:
        ET.SubElement(mp, "CONNECTOR", FROMFIELD=c["name"], FROMINSTANCE=SQ, FROMINSTANCETYPE="Source Qualifier", TOFIELD=c["name"], TOINSTANCE=EXP, TOINSTANCETYPE="Expression")
    
    for c in cols:
        ET.SubElement(mp, "CONNECTOR", FROMFIELD=c["name"], FROMINSTANCE=EXP, FROMINSTANCETYPE="Expression", TOFIELD=c["name"], TOINSTANCE=f"TARGET_{table_name}", TOINSTANCETYPE="Target Definition")
    
    ET.SubElement(mp, "TARGETLOADORDER", ORDER="1", TARGETINSTANCE=f"TARGET_{table_name}")
    ET.SubElement(mp, "ERPINFO")
    
    body = ET.tostring(pm, encoding="unicode")
    pretty = minidom.parseString(body.encode("utf-8")).toprettyxml(indent="    ", encoding="utf-8").decode("utf-8")
    output = '<?xml version="1.0" encoding="windows-1255"?>\n<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">\n' + "\n".join(pretty.splitlines()[1:])
    return output


# ==================== DELTA 020 ====================

def generate_delta_020(ddl_text):
    """DELTA 020 - Master CLN with 2 SOURCE"""
    try:
        table_name, cols = parse_ddl(ddl_text)
    except:
        table_name = "member_demographic_master"
        cols = []
    
    SRC1 = f"{table_name}_STG"
    SRC2 = f"{table_name}_KEY_STG"
    TGT = f"{table_name}_CLN"
    MNAME = f"m_DELTA_020_{TGT}"
    SQ = f"SQ_{table_name}"
    EXP = "EXP_Transform"
    
    pm = ET.Element("POWERMART", CREATION_DATE=datetime.now().strftime("%m/%d/%Y %H:%M:%S"), REPOSITORY_VERSION="187.96")
    repo = ET.SubElement(pm, "REPOSITORY", NAME="InfoDW_QA_Rep", VERSION="187", CODEPAGE="MS1255", DATABASETYPE="Microsoft SQL Server")
    fld = ET.SubElement(repo, "FOLDER", NAME="DW_Drugs", OWNER="Administrator", UUID="620f71cd-f2d3-4541-9b90-9c08ea2afbf8")
    
    # SOURCE 1
    src1_el = ET.SubElement(fld, "SOURCE", NAME=SRC1, DATABASETYPE="Microsoft SQL Server", DBDNAME="dwh-dev", OWNERNAME="kfk", OBJECTVERSION="1")
    po = 0
    for i, c in enumerate(cols, 1):
        m = src_meta(c["type_sql"])
        ET.SubElement(src1_el, "SOURCEFIELD", NAME=c["name"], DATATYPE=m["DATATYPE"], FIELDNUMBER=str(i), PHYSICALLENGTH=m["PHYSICALLENGTH"], PRECISION=m["PRECISION"], SCALE=m["SCALE"], NULLABLE="NULL" if c["nullable"] else "NOTNULL", PHYSICALOFFSET=str(po))
        po += int(m["PHYSICALLENGTH"])
    
    # SOURCE 2
    src2_el = ET.SubElement(fld, "SOURCE", NAME=SRC2, DATABASETYPE="Microsoft SQL Server", DBDNAME="dwh-dev", OWNERNAME="delta", OBJECTVERSION="1")
    ET.SubElement(src2_el, "SOURCEFIELD", NAME="ENTITY_ID", DATATYPE="varchar", FIELDNUMBER="1", PHYSICALLENGTH="50", PRECISION="50", SCALE="0", NULLABLE="NOTNULL", PHYSICALOFFSET="0")
    ET.SubElement(src2_el, "SOURCEFIELD", NAME="timestamp_sequence", DATATYPE="varchar", FIELDNUMBER="2", PHYSICALLENGTH="50", PRECISION="50", SCALE="0", NULLABLE="NOTNULL", PHYSICALOFFSET="50")
    ET.SubElement(src2_el, "SOURCEFIELD", NAME="OFFSET", DATATYPE="bigint", FIELDNUMBER="3", PHYSICALLENGTH="19", PRECISION="19", SCALE="0", NULLABLE="NULL", PHYSICALOFFSET="100")
    
    # TARGET
    tgt_el = ET.SubElement(fld, "TARGET", NAME=TGT, DATABASETYPE="Microsoft SQL Server", OBJECTVERSION="1")
    for i, c in enumerate(cols, 1):
        m = src_meta(c["type_sql"])
        ET.SubElement(tgt_el, "TARGETFIELD", NAME=c["name"], DATATYPE=m["DATATYPE"], FIELDNUMBER=str(i), PRECISION=m["PRECISION"], SCALE=m["SCALE"], NULLABLE="NULL" if c["nullable"] else "NOTNULL")
    
    # MAPPING
    mp = ET.SubElement(fld, "MAPPING", NAME=MNAME, ISVALID="YES", OBJECTVERSION="1", VERSIONNUMBER="1")
    
    # SQ with 2 SOURCE
    sq = ET.SubElement(mp, "TRANSFORMATION", NAME=SQ, TYPE="Source Qualifier", OBJECTVERSION="1", REUSABLE="NO", VERSIONNUMBER="1")
    for c in cols:
        sm = sq_meta(c["type_sql"])
        ET.SubElement(sq, "TRANSFORMFIELD", NAME=c["name"], DATATYPE=sm["DATATYPE"], PRECISION=sm["PRECISION"], SCALE=sm["SCALE"], PORTTYPE="INPUT/OUTPUT")
    ET.SubElement(sq, "TABLEATTRIBUTE", NAME="User Defined Join", VALUE=f"{SRC1}.ENTITY_ID={SRC2}.ENTITY_ID")
    
    # EXP
    exp = ET.SubElement(mp, "TRANSFORMATION", NAME=EXP, TYPE="Expression", OBJECTVERSION="1", REUSABLE="NO", VERSIONNUMBER="1")
    for c in cols:
        sm = sq_meta(c["type_sql"])
        ET.SubElement(exp, "TRANSFORMFIELD", NAME=c["name"], DATATYPE=sm["DATATYPE"], EXPRESSION=c["name"], EXPRESSIONTYPE="GENERAL", PRECISION=sm["PRECISION"], SCALE=sm["SCALE"], PORTTYPE="INPUT/OUTPUT")
    
    # INSTANCES
    ET.SubElement(mp, "INSTANCE", NAME=SRC1, TRANSFORMATION_NAME=SRC1, TRANSFORMATION_TYPE="Source Definition", TYPE="SOURCE", DBDNAME="dwh-dev")
    ET.SubElement(mp, "INSTANCE", NAME=SRC2, TRANSFORMATION_NAME=SRC2, TRANSFORMATION_TYPE="Source Definition", TYPE="SOURCE", DBDNAME="dwh-dev")
    ET.SubElement(mp, "INSTANCE", NAME=TGT, TRANSFORMATION_NAME=TGT, TRANSFORMATION_TYPE="Target Definition", TYPE="TARGET")
    sq_inst = ET.SubElement(mp, "INSTANCE", NAME=SQ, TRANSFORMATION_NAME=SQ, TRANSFORMATION_TYPE="Source Qualifier", TYPE="TRANSFORMATION", REUSABLE="NO")
    ET.SubElement(sq_inst, "ASSOCIATED_SOURCE_INSTANCE", NAME=SRC1)
    ET.SubElement(sq_inst, "ASSOCIATED_SOURCE_INSTANCE", NAME=SRC2)
    ET.SubElement(mp, "INSTANCE", NAME=EXP, TRANSFORMATION_NAME=EXP, TRANSFORMATION_TYPE="Expression", TYPE="TRANSFORMATION", REUSABLE="NO")
    
    # CONNECTORS
    for c in cols:
        ET.SubElement(mp, "CONNECTOR", FROMFIELD=c["name"], FROMINSTANCE=SRC1, FROMINSTANCETYPE="Source Definition", TOFIELD=c["name"], TOINSTANCE=SQ, TOINSTANCETYPE="Source Qualifier")
    ET.SubElement(mp, "CONNECTOR", FROMFIELD="ENTITY_ID", FROMINSTANCE=SRC2, FROMINSTANCETYPE="Source Definition", TOFIELD="ENTITY_ID", TOINSTANCE=SQ, TOINSTANCETYPE="Source Qualifier")
    
    for c in cols:
        ET.SubElement(mp, "CONNECTOR", FROMFIELD=c["name"], FROMINSTANCE=SQ, FROMINSTANCETYPE="Source Qualifier", TOFIELD=c["name"], TOINSTANCE=EXP, TOINSTANCETYPE="Expression")
    
    for c in cols:
        ET.SubElement(mp, "CONNECTOR", FROMFIELD=c["name"], FROMINSTANCE=EXP, FROMINSTANCETYPE="Expression", TOFIELD=c["name"], TOINSTANCE=TGT, TOINSTANCETYPE="Target Definition")
    
    ET.SubElement(mp, "TARGETLOADORDER", ORDER="1", TARGETINSTANCE=TGT)
    ET.SubElement(mp, "ERPINFO")
    
    body = ET.tostring(pm, encoding="unicode")
    pretty = minidom.parseString(body.encode("utf-8")).toprettyxml(indent="    ", encoding="utf-8").decode("utf-8")
    output = '<?xml version="1.0" encoding="windows-1255"?>\n<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">\n' + "\n".join(pretty.splitlines()[1:])
    return output


# ==================== DELTA 030 ====================

def generate_delta_030(ddl_text):
    """DELTA 030 - Communication Detail with 2 SOURCE"""
    try:
        table_name, cols = parse_ddl(ddl_text)
    except:
        table_name = "member_demographic_communication_detail"
        cols = []
    
    SRC1 = f"{table_name}_STG"
    SRC2 = "member_demographic_master_CLN"
    TGT = f"{table_name}_CLN"
    MNAME = f"m_DELTA_030_{TGT}"
    SQ = f"SQ_{table_name}"
    EXP = "EXP_Transform"
    
    pm = ET.Element("POWERMART", CREATION_DATE=datetime.now().strftime("%m/%d/%Y %H:%M:%S"), REPOSITORY_VERSION="187.96")
    repo = ET.SubElement(pm, "REPOSITORY", NAME="InfoDW_QA_Rep", VERSION="187", CODEPAGE="MS1255", DATABASETYPE="Microsoft SQL Server")
    fld = ET.SubElement(repo, "FOLDER", NAME="DW_Drugs", OWNER="Administrator", UUID="620f71cd-f2d3-4541-9b90-9c08ea2afbf8")
    
    # SOURCE 1
    src1_el = ET.SubElement(fld, "SOURCE", NAME=SRC1, DATABASETYPE="Microsoft SQL Server", DBDNAME="dwh-dev", OWNERNAME="kfk", OBJECTVERSION="1")
    po = 0
    for i, c in enumerate(cols, 1):
        m = src_meta(c["type_sql"])
        ET.SubElement(src1_el, "SOURCEFIELD", NAME=c["name"], DATATYPE=m["DATATYPE"], FIELDNUMBER=str(i), PHYSICALLENGTH=m["PHYSICALLENGTH"], PRECISION=m["PRECISION"], SCALE=m["SCALE"], NULLABLE="NULL" if c["nullable"] else "NOTNULL", PHYSICALOFFSET=str(po))
        po += int(m["PHYSICALLENGTH"])
    
    # SOURCE 2
    src2_el = ET.SubElement(fld, "SOURCE", NAME=SRC2, DATABASETYPE="Microsoft SQL Server", DBDNAME="dwh-dev", OWNERNAME="delta", OBJECTVERSION="1")
    ET.SubElement(src2_el, "SOURCEFIELD", NAME="TRANSACTION_ID", DATATYPE="bigint", FIELDNUMBER="1", PHYSICALLENGTH="19", PRECISION="19", SCALE="0", NULLABLE="NOTNULL", PHYSICALOFFSET="0")
    ET.SubElement(src2_el, "SOURCEFIELD", NAME="entity_type", DATATYPE="varchar", FIELDNUMBER="2", PHYSICALLENGTH="50", PRECISION="50", SCALE="0", NULLABLE="NULL", PHYSICALOFFSET="19")
    
    # TARGET
    tgt_el = ET.SubElement(fld, "TARGET", NAME=TGT, DATABASETYPE="Microsoft SQL Server", OBJECTVERSION="1")
    for i, c in enumerate(cols, 1):
        m = src_meta(c["type_sql"])
        ET.SubElement(tgt_el, "TARGETFIELD", NAME=c["name"], DATATYPE=m["DATATYPE"], FIELDNUMBER=str(i), PRECISION=m["PRECISION"], SCALE=m["SCALE"], NULLABLE="NULL" if c["nullable"] else "NOTNULL")
    
    # MAPPING
    mp = ET.SubElement(fld, "MAPPING", NAME=MNAME, ISVALID="YES", OBJECTVERSION="1", VERSIONNUMBER="1")
    
    # SQ with 2 SOURCE
    sq = ET.SubElement(mp, "TRANSFORMATION", NAME=SQ, TYPE="Source Qualifier", OBJECTVERSION="1", REUSABLE="NO", VERSIONNUMBER="1")
    for c in cols:
        sm = sq_meta(c["type_sql"])
        ET.SubElement(sq, "TRANSFORMFIELD", NAME=c["name"], DATATYPE=sm["DATATYPE"], PRECISION=sm["PRECISION"], SCALE=sm["SCALE"], PORTTYPE="INPUT/OUTPUT")
    ET.SubElement(sq, "TABLEATTRIBUTE", NAME="User Defined Join", VALUE=f"{SRC1}.entity_id={SRC2}.entity_id")
    
    # EXP
    exp = ET.SubElement(mp, "TRANSFORMATION", NAME=EXP, TYPE="Expression", OBJECTVERSION="1", REUSABLE="NO", VERSIONNUMBER="1")
    for c in cols:
        sm = sq_meta(c["type_sql"])
        ET.SubElement(exp, "TRANSFORMFIELD", NAME=c["name"], DATATYPE=sm["DATATYPE"], EXPRESSION=c["name"], EXPRESSIONTYPE="GENERAL", PRECISION=sm["PRECISION"], SCALE=sm["SCALE"], PORTTYPE="INPUT/OUTPUT")
    
    # INSTANCES
    ET.SubElement(mp, "INSTANCE", NAME=SRC1, TRANSFORMATION_NAME=SRC1, TRANSFORMATION_TYPE="Source Definition", TYPE="SOURCE", DBDNAME="dwh-dev")
    ET.SubElement(mp, "INSTANCE", NAME=SRC2, TRANSFORMATION_NAME=SRC2, TRANSFORMATION_TYPE="Source Definition", TYPE="SOURCE", DBDNAME="dwh-dev")
    ET.SubElement(mp, "INSTANCE", NAME=TGT, TRANSFORMATION_NAME=TGT, TRANSFORMATION_TYPE="Target Definition", TYPE="TARGET")
    sq_inst = ET.SubElement(mp, "INSTANCE", NAME=SQ, TRANSFORMATION_NAME=SQ, TRANSFORMATION_TYPE="Source Qualifier", TYPE="TRANSFORMATION", REUSABLE="NO")
    ET.SubElement(sq_inst, "ASSOCIATED_SOURCE_INSTANCE", NAME=SRC1)
    ET.SubElement(sq_inst, "ASSOCIATED_SOURCE_INSTANCE", NAME=SRC2)
    ET.SubElement(mp, "INSTANCE", NAME=EXP, TRANSFORMATION_NAME=EXP, TRANSFORMATION_TYPE="Expression", TYPE="TRANSFORMATION", REUSABLE="NO")
    
    # CONNECTORS
    for c in cols:
        ET.SubElement(mp, "CONNECTOR", FROMFIELD=c["name"], FROMINSTANCE=SRC1, FROMINSTANCETYPE="Source Definition", TOFIELD=c["name"], TOINSTANCE=SQ, TOINSTANCETYPE="Source Qualifier")
    ET.SubElement(mp, "CONNECTOR", FROMFIELD="entity_type", FROMINSTANCE=SRC2, FROMINSTANCETYPE="Source Definition", TOFIELD="entity_type", TOINSTANCE=SQ, TOINSTANCETYPE="Source Qualifier")
    
    for c in cols:
        ET.SubElement(mp, "CONNECTOR", FROMFIELD=c["name"], FROMINSTANCE=SQ, FROMINSTANCETYPE="Source Qualifier", TOFIELD=c["name"], TOINSTANCE=EXP, TOINSTANCETYPE="Expression")
    
    for c in cols:
        ET.SubElement(mp, "CONNECTOR", FROMFIELD=c["name"], FROMINSTANCE=EXP, FROMINSTANCETYPE="Expression", TOFIELD=c["name"], TOINSTANCE=TGT, TOINSTANCETYPE="Target Definition")
    
    ET.SubElement(mp, "TARGETLOADORDER", ORDER="1", TARGETINSTANCE=TGT)
    ET.SubElement(mp, "ERPINFO")
    
    body = ET.tostring(pm, encoding="unicode")
    pretty = minidom.parseString(body.encode("utf-8")).toprettyxml(indent="    ", encoding="utf-8").decode("utf-8")
    output = '<?xml version="1.0" encoding="windows-1255"?>\n<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">\n' + "\n".join(pretty.splitlines()[1:])
    return output


# ==================== STREAMLIT UI ====================

def main():
    st.set_page_config(page_title="Informatica XML Generator", layout="wide")
    
    st.markdown("""
    <style>
    h1, h2, h3 { text-align: right; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🔧 Informatica PowerCenter XML Generator")
    st.markdown("<h2 style='text-align: right; direction: rtl;'>יוצר XML לאפליקציית Informatica PowerCenter</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='text-align: right; direction: rtl;'><b>בחר את שלב Delta המתאים, הדבק את ה-CREATE TABLE שלך, וייצר את קובץ ה-XML</b></div>", unsafe_allow_html=True)
    
    # בחירת שלב
    st.markdown("### בחר שלב Delta")
    delta_stage = st.radio(
        "בחר את שלב ה-Delta להפקה:",
        ["DELTA 000 - Master Key STG", "DELTA 010 - Master STG", "DELTA 020 - Master CLN", "DELTA 030 - Communication Detail CLN"],
        index=0
    )
    
    st.markdown("---")
    
    # הזנת DDL
    st.markdown("### הזן את CREATE TABLE DDL")
    ddl_input = st.text_area(
        "הדבק את סקריפט CREATE TABLE שלך כאן:",
        height=250,
        placeholder="CREATE TABLE [schema].[table_name] (\n  [COLUMN1] [type],\n  [COLUMN2] [type],\n  ...\n)",
        key="ddl_input"
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("✨ ייצר קובץ XML", use_container_width=True, type="primary"):
            if not ddl_input.strip():
                st.error("❌ אנא הדבק CREATE TABLE DDL")
            else:
                with st.spinner("⏳ מעבד את ה-DDL וממיר ל-XML..."):
                    try:
                        if "DELTA 000" in delta_stage:
                            xml_content = generate_delta_000(ddl_input)
                        elif "DELTA 010" in delta_stage:
                            xml_content = generate_delta_010(ddl_input)
                        elif "DELTA 020" in delta_stage:
                            xml_content = generate_delta_020(ddl_input)
                        else:
                            xml_content = generate_delta_030(ddl_input)
                        
                        st.session_state.xml_content = xml_content
                        st.success("✅ XML נוצר בהצלחה!")
                    except Exception as e:
                        st.error(f"❌ שגיאה: {str(e)}")
    
    # הצגת XML
    if "xml_content" in st.session_state and st.session_state.xml_content:
        st.markdown("---")
        st.markdown("### 📄 XML שנוצר")
        
        with st.expander("הצג XML (לחץ להרחבה)", expanded=False):
            st.code(st.session_state.xml_content, language="xml")
        
        st.download_button(
            label="⬇️ הורד קובץ XML",
            data=st.session_state.xml_content,
            file_name=f"informatica_mapping_{delta_stage.split()[1]}.xml",
            mime="application/xml",
            use_container_width=True,
            type="primary"
        )


if __name__ == "__main__":
    main()
