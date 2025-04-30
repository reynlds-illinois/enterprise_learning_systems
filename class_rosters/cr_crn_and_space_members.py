#!/usr/bin/python

import sys
sys.path.append("/var/lib/canvas-mgmt/bin")  # Ensure this line is included as close to the top as possible
import json
from sqlalchemy import create_engine, text
from ldap3 import Server, Connection, ALL
from canvasFunctions import getEnv, batchLookupReg, bind2Ldap, logScriptStart

# Constants
REALM_PROD = 'p'
REALM_STAGE = 's'

def initialize_environment():
    """
    Initializes the environment by retrieving configuration values and logging the script start.
    Returns:
        dict: A dictionary containing environment variables.
    """
    envDict = getEnv()
    logScriptStart()
    print()
    return envDict


def get_database_connection(env, envDict):
    """
    Creates a SQLAlchemy engine for the database connection based on the selected environment.

    Args:
        env (str): The selected environment ('p' for prod, 's' for stage).
        envDict (dict): The environment configuration dictionary.

    Returns:
        sqlalchemy.engine.Engine: The SQLAlchemy engine for the database connection.
    """
    if env == REALM_PROD:
        dbUser = envDict['req-prod.db.user']
        dbPass = envDict['req-prod.db.pass']
        dbHost = envDict['req-prod.db.sys']
        dbPort = 1521
        dbSid = envDict['req-prod.db.sid']
        envLabel = "PROD"
    else:
        dbUser = envDict['req-stage.db.user']
        dbPass = envDict['req-stage.db.pass']
        dbHost = envDict['req-stage.db.sys']
        dbPort = 1521
        dbSid = envDict['req-stage.db.sid']
        envLabel = "STAGE"

    db_url = f"oracle+cx_oracle://{dbUser}:{dbPass}@{dbHost}:{dbPort}/?service_name={dbSid}"
    engine = create_engine(db_url)
    print(f"Connected to: {dbHost}:{dbPort} ({envLabel})")
    print()
    return engine


def get_ldap_connection(envDict):
    """
    Establishes an LDAP connection using the provided environment configuration.

    Args:
        envDict (dict): The environment configuration dictionary.

    Returns:
        ldap3.Connection: The LDAP connection object.
    """
    ldapHost = envDict['UofI.ldap.ad_sys']
    ldapBindDn = envDict['UofI.ad_bind']
    ldapBindPw = envDict['UofI.ad_bindpwd']
    return bind2Ldap(ldapHost, ldapBindDn, ldapBindPw)


def query_spaces_by_crn(engine, crn, termcode):
    """
    Queries the database for spaces associated with a given CRN and term code.

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine for the database connection.
        crn (str): The CRN to query.
        termcode (str): The term code to query.

    Returns:
        list: A list of spaces associated with the CRN and term code.
    """
    query = text("""
        SELECT SR.TARGET_PRODUCT_KEY || TM.BANNER_PART_OF_TERM || '_' || SR.SPACE_ID CID
        FROM CORREL.T_SPACE_ROSTER SRR
        JOIN CORREL.T_SPACE_REQUEST SR ON (SRR.SPACE_ID = SR.SPACE_ID)
        LEFT JOIN CORREL.T_TERM TM ON (SR.TERM_ID = TM.TERM_ID)
        WHERE SRR.TERM_CODE = :termcode
        AND SR.PRODUCT_ID = 'BB9'
        AND SRR.ROSTER_DATA_SOURCE_KEY = :crn
    """)
    with engine.connect() as connection:
        return connection.execute(query, {"termcode": termcode, "crn": crn}).fetchall()


def query_crns_by_space(engine, space_id):
    """
    Queries the database for CRNs associated with a given space ID.

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine for the database connection.
        space_id (str): The space ID to query.

    Returns:
        list: A list of CRNs associated with the space ID.
    """
    query = text("""
        SELECT SRR.ROSTER_DATA_SOURCE_KEY CRN,
               ADR.RUBRIC,
               ADR.COURSE_NUMBER,
               ADR.SECTION,
               ADR.TERM_CODE TERM
        FROM CORREL.T_SPACE_ROSTER SRR
        LEFT JOIN CORREL.T_AD_ROSTER ADR ON (SRR.ROSTER_DATA_SOURCE_KEY = ADR.CRN AND SRR.TERM_CODE = ADR.TERM_CODE)
        WHERE SRR.SPACE_ID = :space_id
    """)
    with engine.connect() as connection:
        return connection.execute(query, {"space_id": space_id}).fetchall()


def lookup_members(crHost, crXapikey, termcode, crns, ldapConn, ldapSearchBase):
    """
    Looks up members for a list of CRNs and retrieves their LDAP information.

    Args:
        crHost (str): The class roster host.
        crXapikey (str): The API key for the class roster.
        termcode (str): The term code.
        crns (list): The list of CRNs.
        ldapConn (ldap3.Connection): The LDAP connection object.
        ldapSearchBase (str): The LDAP search base.

    Returns:
        None
    """
    results = batchLookupReg(crHost, crXapikey, termcode, crns)
    for crn, sections in results.items():
        print(f"CRN: {crn} - term: {termcode}")
        print()
        for section, uins in sections.items():
            print(f"  Section: {section}")
            for uin in uins:
                adFilter = f"(&(objectclass=user)(uiucEduUIN={uin}))"
                ldapConn.search(search_base=ldapSearchBase, search_filter=adFilter,
                                attributes=['sAMAccountName', 'displayName', 'uiucEduUIN'], size_limit=0)
                response = json.loads(ldapConn.response_to_json())
                if response['entries']:
                    netId = response['entries'][0]['attributes']['sAMAccountName']
                    displayName = response['entries'][0]['attributes']['displayName']
                    print(f"    {netId} - {displayName}")
        print()


def main():
    """
    Main function to manage the script workflow.
    """
    # Initialize environment and connections
    envDict = initialize_environment()
    env = ''
    while env not in [REALM_PROD, REALM_STAGE]:
        env = input('Please enter the realm to use: (p)rod or (s)tage: ').lower()[0]

    engine = get_database_connection(env, envDict)
    ldapConn = get_ldap_connection(envDict)

    crHost = envDict['class.rosters.host']
    crXapikey = envDict['class.rosters.xapi']
    ldapSearchBase = envDict['ad-prod.searchbase_new']

    while True:
        lookupChoice = ''
        while lookupChoice not in ['s', 'c']:
            lookupChoice = input('Lookup by (s)pace or (c)rn? ').lower()
        print()

        if lookupChoice == 'c':
            crn = input('Enter CRN: ')
            termcode = input('Enter Banner Term ID: ')
            spaces = query_spaces_by_crn(engine, crn, termcode)
            if spaces:
                print(f"Spaces using CRN {crn}:")
                for space in spaces:
                    print(f"  {space[0]}")
                print()
            else:
                print(f"No spaces found for CRN {crn}.")
                print()
        else:
            space_id = input('Enter space ID: ')
            crns = query_crns_by_space(engine, space_id)
            if crns:
                termcode = crns[0][4]
                lookup_members(crHost, crXapikey, termcode, [crn[0] for crn in crns], ldapConn, ldapSearchBase)
            else:
                print(f"No CRNs found for space ID {space_id}.")
                print()

        answer = input("Continue with another SPACE or CRN? (y/n): ").strip().lower()
        print()
        if answer != 'y':
            break

    print("Closing connection and exiting...")
    print()
    ldapConn.unbind()


if __name__ == "__main__":
    main()
