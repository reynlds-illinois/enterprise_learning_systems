#!/usr/bin/python
#
import sys, requests, json
sys.path.append("/var/lib/canvas-mgmt/bin")
from pprint import pprint
from columnar import columnar
from canvasFunctions import getEnv
#
envDict = getEnv()
validTerms = envDict['banner.terms'].split(",")
#logScriptStart()
crHost = envDict['class.rosters.host']
crXapikey = envDict['class.rosters.xapi']
crAuth = {"X-API-KEY": crXapikey}
action = ''
bannerTerm = ''
#
def crnGetDetails(crn, bannerTerm, crAuth, crHost):
    url = f'{crHost}v1.0/section-lookup/{bannerTerm}/{crn}'
    response = requests.get(url, headers=crAuth)
    if response.status_code == 200:
        crnInfo = response.json()
        print(json.dumps(crnInfo, indent=4))
        print()
    else:
        print(f'  = Error: {response.status_code} - {response.text}')
        print()
#
def crnGetSubject(subject, bannerTerm, crAuth, crHost):
    columnHeader = ['CRN', 'Subject', 'Section', 'Cross List Group ID', 'Course Title']
    allCRNs = []
    url = f'{crHost}v1.0/sections/{bannerTerm}/{subject}'
    print('  >>> Please wait while the CRN information is retrieved...')
    print()
    response = requests.get(url, headers=crAuth)
    if response.status_code == 200:
        crnList = response.json()
        for item in crnList['sections']:
            allCRNs.append([item['crn'], item['crs_subj_cd'], item['sect_nbr'], item['cross_list_group_id'], item['crs_title']])
        allCRNs.sort(key=lambda x: x[0])
        print(columnar(allCRNs, columnHeader, no_borders=True))
        print()
        return allCRNs
    else:
        print(f'  = Error: {response.status_code} - {response.text}')
        return []
#
while action not in ['1','2']:
    print()
    print('  = Please choose an action from the list below:')
    print()
    print('    1. Get info for a single CRN')
    print('    2. Get a list of CRNs for a subject (i.e., MATH, BADM, etc.)')
    print()
    action = input('  = Enter the number for the action you want to perform: ')
    print()
#
if action == '1':
    crn = input('  = Please enter the CRN: ')
    print()
    bannerTerm = input('  = Please enter the Banner term: ')
    print()
    crnGetDetails(crn, bannerTerm,crAuth, crHost)
#
elif action == '2':
    myCRN = ''
    targetCRN  = False
    subject = input('  = Please enter the subject (e.g., MATH, BADM, etc.): ').upper()
    print()
    while bannerTerm not in validTerms:
        bannerTerm = input('  = Please enter the Banner term: ')
        print()
    crns = crnGetSubject(subject, bannerTerm, crAuth, crHost)
    print()
    while True:
        myCRN = input('  = Enter the CRN for details or press Enter to exit: ')
        if myCRN == '':
            break
        else:
             targetCRN = False
             for sublist in crns:
                if sublist[0] == myCRN:
                    targetCRN = True
                    break
             if targetCRN:
                crnGetDetails(myCRN, bannerTerm, crAuth, crHost)
                break
             else:
                print(f'  = CRN {myCRN} not found in the list. Please try again.')
print()