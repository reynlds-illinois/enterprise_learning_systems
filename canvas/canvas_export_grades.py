#!/usr/bin/python
# 
import sys, requests, urllib, json, time, datetime, csv
from datetime import date
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
#logScriptStart()
env = getEnv()
canvasToken = env["canvas.token"]
canvasApi = env["canvas.api-prod"]
loopDelay = 10
today = str(date.today().strftime("%Y-%m-%d"))
#
def get_active_terms_from_csv(terms_csv_path):
    active = []
    skipped = []
    try:
        with open(terms_csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                end_date_str = row.get("end_date", "").strip()
                canvas_term_id = row.get("canvas_term_id", "").strip()
                if not canvas_term_id or not end_date_str:
                    continue
                try:
                    end_date = datetime.datetime.fromisoformat(end_date_str).date()
                except ValueError:
                    print(f"  WARNING: Could not parse end_date '{end_date_str}' "
                          f"for term '{canvas_term_id}' -- skipping.")
                    continue
                if end_date > date.today():
                    active.append((canvas_term_id, row.get("term_id", "").strip()))
                else:
                    skipped.append((canvas_term_id, row.get("term_id", ""), end_date_str))
    except FileNotFoundError:
        print(f"ERROR: Terms CSV not found: {terms_csv_path}")
        sys.exit(1)
    if skipped:
        print(f"  Skipping {len(skipped)} expired term(s):")
        for tid, label, ed in skipped:
            print(f"    canvas_term_id={tid}  term_id={label}  end_date={ed}")
    print(f"  {len(active)} active term(s) found: {active}")
    return active
#
activeTerms = get_active_terms_from_csv("/var/lib/canvas-mgmt/config/canvas_terms.csv")
canvasReportsPath = str('/var/lib/canvas-mgmt/reports/enrollments/')
#
canvasEndpoint = f"accounts/1/reports/grade_export_csv"
reportURL = f"{canvasApi}{canvasEndpoint}"
headers = {"Authorization": f"Bearer {canvasToken}"}
#
for canvas_term_id, term_id in activeTerms:
    reportProgress = 0
    print()
    print(f'  > Processing canvas_term_id: {canvas_term_id}  term_id: {term_id}')
    print()
    downloadFilePath = f'{canvasReportsPath}canvas_grades_{term_id}_{today}.csv'
    params = {"parameters[enrollment_term_id]": f"{canvas_term_id}"}
    #
    r = requests.post(reportURL, headers=headers, params=params).json()
    #
    reportID = r["id"]
    reportEndpoint = f"accounts/1/reports/grade_export_csv/{reportID}"
    #
    while reportProgress < 100:
        checkReportUrl = urllib.parse.urljoin(canvasApi,reportEndpoint)
        response = requests.get(checkReportUrl, headers=headers)
        responseJson2 = json.loads(response.text)
        reportProgress = int(responseJson2['progress'])
        print(f"checking {reportID} report progress. Currently: {reportProgress}")
        time.sleep(loopDelay)
    #
    with open(downloadFilePath, "wb") as file:
        downloadFile = str(responseJson2["attachment"]["url"])
        fileLink = requests.get(downloadFile)
        file.write(fileLink.content)
print()
