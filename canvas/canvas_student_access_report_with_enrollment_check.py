#!/usr/bin/python
#
import os
import sys
import time
import base64
import requests
from datetime import datetime, timedelta, timezone
from columnar import columnar
from boxsdk import JWTAuth, Client
from boxsdk.exception import BoxAPIException
from boxsdk.object.collaboration import CollaborationRole
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException

sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm, getEnv, yesOrNo
from canvasFunctions import canvasGetUserInfoLive as canvasGetUserInfo

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
REPORTS_PATH = "/var/lib/canvas-mgmt/reports/"
ENROLLMENT_STATES = ["active", "inactive", "deleted", "completed", "invited"]
STATUS_MENU = {
    "a": "active",
    "c": "completed",
    "i": "inactive",
    "d": "delete",
}


def parse_canvas_datetime(value):
    if not value:
        return None
    cleaned = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def require_input(prompt_text):
    value = ""
    while not value:
        value = input(prompt_text).strip()
    return value


def setup_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument("--enable-javascript")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(3)
    return driver


def canvas_login(driver, canvas_user, canvas_pass, canvas_url):
    try:
        driver.get(canvas_url)
        print("  = WebDriver launched and Canvas login page loaded.")
    except Exception as ex:
        print(f"  >>> Error launching browser/login page: {ex}")
        return False

    try:
        username_field = WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"][aria-required="true"]'))
        )
        username_field.clear()
        username_field.send_keys(canvas_user)
        driver.find_element(By.ID, "idSIButton9").click()
    except Exception as ex:
        print(f"  >>> Error entering Canvas username: {ex}")
        return False

    try:
        password_field = WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"][aria-required="true"]'))
        )
        password_field.clear()
        password_field.send_keys(canvas_pass)
        driver.find_element(By.ID, "idSIButton9").click()
    except Exception as ex:
        print(f"  >>> Error entering Canvas password: {ex}")
        return False

    try:
        WebDriverWait(driver, 8).until(EC.url_matches("^" + canvas_url + ".*"))
        print("  = Canvas login completed.")
        return True
    except TimeoutException:
        print("  >>> Canvas login failed or did not redirect in time.")
        return False


def fetch_enrollments_for_term(canvas_user_id, term_code, canvas_api, canvas_auth):
    search_results = []
    enrollments_url = f"{canvas_api}users/{canvas_user_id}/enrollments?enrollment_term_id=sis_term_id%3A{term_code}"

    for state in ENROLLMENT_STATES:
        params = {"per_page": 100, "state": state}
        try:
            response = requests.get(enrollments_url, headers=canvas_auth, params=params)
        except Exception as ex:
            print(f"  >>> Failed to query enrollments for state {state}: {ex}")
            continue

        if response.status_code != 200:
            print(f"  >>> Enrollment query failed for state {state}. HTTP {response.status_code}")
            continue

        state_results = response.json()
        if isinstance(state_results, list):
            search_results.extend(state_results)

        while "next" in response.links:
            try:
                response = requests.get(response.links["next"]["url"], headers=canvas_auth, params=params)
                if response.status_code != 200:
                    print(f"  >>> Pagination failed for state {state}. HTTP {response.status_code}")
                    break
                next_results = response.json()
                if isinstance(next_results, list):
                    search_results.extend(next_results)
            except Exception as ex:
                print(f"  >>> Pagination request failed for state {state}: {ex}")
                break

    dedupe = {}
    for row in search_results:
        dedupe[str(row.get("id"))] = row

    return list(dedupe.values())


def build_enrollment_rows(search_results):
    rows = []
    for row in search_results:
        enrollment_id = str(row.get("id", ""))
        course_id = row.get("course_id")
        if not enrollment_id or not course_id:
            continue

        rows.append(
            {
                "course_id": course_id,
                "enroll_id": enrollment_id,
                "net_id": row.get("sis_user_id", "n/a"),
                "sis_course_id": row.get("sis_course_id", "n/a"),
                "sub_account_id": row.get("sis_account_id") or "n/a",
                "sis_section_id": row.get("sis_section_id") or "n/a",
                "section_id": row.get("course_section_id"),
                "role": row.get("role", "n/a"),
                "status": row.get("enrollment_state", "unknown"),
            }
        )

    rows.sort(key=lambda x: (x.get("sis_course_id") or "", x.get("enroll_id") or ""))
    return rows


def print_enrollment_table(rows):
    table_rows = []
    headers = [
        "course_id",
        ">ENROLL_ID<",
        "net_id",
        "sis_course_id",
        "sub_acct_id",
        "sis_section_id",
        "section_id",
        "role",
        "status",
    ]

    for row in rows:
        table_rows.append(
            [
                row["course_id"],
                row["enroll_id"],
                row["net_id"],
                row["sis_course_id"],
                row["sub_account_id"],
                row["sis_section_id"],
                row["section_id"],
                row["role"],
                row["status"],
            ]
        )

    print()
    print(columnar(table_rows, headers, no_borders=True))
    print()


def choose_status_for_enrollment(enrollment_id, current_status):
    while True:
        prompt = (
            f"New status for enrollment {enrollment_id} (a=active, c=completed, i=inactive, d=delete, q=skip) "
            f"[current={current_status}]: "
        )
        choice = input(prompt).strip().lower()
        if choice == "q":
            return None
        if choice in STATUS_MENU:
            return STATUS_MENU[choice]
        print("  >>> Invalid status choice. Please enter a, c, i, d, or q.")


def plan_enrollment_changes(rows):
    by_id = {row["enroll_id"]: row for row in rows}
    deleted_rows = [row for row in rows if row["status"] == "deleted"]
    plan = {}

    if deleted_rows:
        print(f"  = Found {len(deleted_rows)} deleted enrollment(s) in this term.")
        if yesOrNo("Auto-plan all deleted enrollments to COMPLETED before custom selection?"):
            for row in deleted_rows:
                plan[row["enroll_id"]] = "completed"
            print("  = Added deleted enrollments to the change plan with status COMPLETED.")
        else:
            print("  = Skipping auto-plan for deleted enrollments.")

    print()
    print("  > You can now add or override specific enrollment changes.")
    print("  > Enter enrollment IDs as comma-separated values. Press Enter to stop adding IDs.")

    while True:
        selection = input("Enrollment ID(s) to modify (blank to finish): ").strip()
        if not selection:
            break

        requested_ids = [item.strip() for item in selection.split(",") if item.strip()]
        valid_ids = []

        for enrollment_id in requested_ids:
            if enrollment_id not in by_id:
                print(f"  >>> Enrollment ID not in table: {enrollment_id}")
            else:
                valid_ids.append(enrollment_id)

        for enrollment_id in valid_ids:
            current_status = by_id[enrollment_id]["status"]
            new_status = choose_status_for_enrollment(enrollment_id, current_status)
            if not new_status:
                print(f"  = Skipped {enrollment_id}")
                continue
            if new_status == current_status:
                print(f"  = No-op for {enrollment_id}; target status matches current status.")
                continue
            plan[enrollment_id] = new_status

    if not plan:
        print("  = No enrollment changes were planned.")
        return []

    preview_rows = []
    for enrollment_id, target_status in plan.items():
        row = by_id[enrollment_id]
        preview_rows.append(
            [
                enrollment_id,
                row["sis_course_id"],
                row["status"],
                target_status,
            ]
        )

    preview_rows.sort(key=lambda x: x[1])
    print()
    print("Planned enrollment changes:")
    print(columnar(preview_rows, ["enroll_id", "sis_course_id", "current_status", "new_status"], no_borders=True))
    print()

    if not yesOrNo("Proceed with these enrollment changes?"):
        print("  = Enrollment changes cancelled by user.")
        return []

    return [{"enroll_id": enroll_id, "new_status": new_status, "row": by_id[enroll_id]} for enroll_id, new_status in plan.items()]


def canvas_enrollment_edit(enroll_id, canvas_api, canvas_auth, row, enrollment_new_status, canvas_user_id, sleep_delay=1):
    reset_date = False
    original_end_date = None
    course_id = row["course_id"]
    course_url = f"{canvas_api}courses/{course_id}"

    try:
        course_resp = requests.get(course_url, headers=canvas_auth)
        if course_resp.status_code != 200:
            return False, f"Course lookup failed (HTTP {course_resp.status_code})"
        canvas_course_info = course_resp.json()
    except Exception as ex:
        return False, f"Course lookup failed: {ex}"

    now_dt = datetime.now(timezone.utc)
    end_dt = parse_canvas_datetime(canvas_course_info.get("end_at"))
    if end_dt and end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    try:
        if end_dt and end_dt < now_dt:
            print(f"  = Course {course_id} ended in the past. Extending end date to allow modification.")
            reset_date = True
            original_end_date = canvas_course_info.get("end_at")
            new_end_date = (now_dt + timedelta(hours=1)).strftime(DATE_FORMAT)
            course_params = {"course[end_at]": new_end_date}
            date_change = requests.put(course_url, headers=canvas_auth, params=course_params)
            if date_change.status_code not in [200, 201]:
                return False, f"Unable to temporarily extend course end date (HTTP {date_change.status_code})"

        time.sleep(sleep_delay)

        if enrollment_new_status == "delete":
            delete_url = f"{canvas_api}courses/{course_id}/enrollments/{enroll_id}"
            params = {"task": "delete"}
            modify_resp = requests.delete(delete_url, params=params, headers=canvas_auth)
        else:
            create_url = f"{canvas_api}courses/{course_id}/enrollments"
            params = {
                "enrollment[user_id]": canvas_user_id,
                "enrollment[type]": row["role"],
                "enrollment[enrollment_state]": enrollment_new_status,
                "enrollment[notify]": False,
                "enrollment[course_section_id]": row["section_id"],
            }
            modify_resp = requests.post(create_url, headers=canvas_auth, params=params)

        if modify_resp.status_code not in [200, 201]:
            detail = modify_resp.text[:500]
            return False, f"Enrollment modify failed (HTTP {modify_resp.status_code}): {detail}"

        response_data = modify_resp.json()
        if not isinstance(response_data, dict) or not response_data.get("id"):
            return False, f"Unexpected enrollment response: {response_data}"

        time.sleep(sleep_delay)
        return True, response_data

    except Exception as ex:
        return False, f"Enrollment modify exception: {ex}"

    finally:
        if reset_date:
            try:
                print(f"  = Reverting course {course_id} end date to original value.")
                restore_params = {"course[end_at]": original_end_date}
                requests.put(course_url, headers=canvas_auth, params=restore_params)
            except Exception as ex:
                print(f"  >>> Failed to restore original course end date for {course_id}: {ex}")


def student_access_report_export(driver, report_url, target_file_path):
    try:
        driver.get(report_url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.XPATH, '//*[@id="content"]')))

        pdf_data = driver.execute_cdp_cmd(
            "Page.printToPDF",
            {
                "format": "A4",
                "printBackground": True,
            },
        )

        decoded_pdf_data = base64.b64decode(pdf_data["data"])
        with open(target_file_path, "wb") as pdf_file:
            pdf_file.write(decoded_pdf_data)

        return True, None
    except TimeoutException:
        return False, "Timeout waiting for Canvas report content"
    except Exception as ex:
        return False, str(ex)


def create_box_folder_and_share(box_client, parent_folder_id, folder_name, requestor_email):
    try:
        box_folder = box_client.folder(parent_folder_id).create_subfolder(folder_name)
    except BoxAPIException as ex:
        if ex.status == 409:
            fallback_name = f"{folder_name}_{int(time.time())}"
            print(f"  >>> BOX folder already exists. Using fallback folder name: {fallback_name}")
            box_folder = box_client.folder(parent_folder_id).create_subfolder(fallback_name)
            folder_name = fallback_name
        else:
            raise

    folder_id = int(box_folder["id"])
    try:
        box_client.folder(folder_id).collaborate_with_login(requestor_email, CollaborationRole.VIEWER)
    except BoxAPIException as ex:
        if ex.status == 409:
            print("  = Requestor already has collaboration access to this folder.")
        else:
            raise

    # Match existing script behavior: provide the folder URL directly.
    shared_link = f"https://uofi.box.com/folder/{folder_id}"

    return folder_id, folder_name, shared_link


def upload_file_to_box(box_client, folder_id, target_file_path, target_file_name):
    try:
        box_client.folder(folder_id).upload(target_file_path, target_file_name)
        return True, None
    except Exception as ex:
        return False, str(ex)


def get_illinois_email(user_info):
    email = (user_info.get("email") or "").strip().lower()
    if email.endswith("@illinois.edu"):
        return email

    sis_user_id = (user_info.get("sis_user_id") or "").strip().lower()
    if sis_user_id:
        return f"{sis_user_id}@illinois.edu"

    return ""


def main():
    print("")
    env = getEnv()
    selected_realm = realm()
    canvas_api = selected_realm["canvasApi"]
    canvas_url = selected_realm["canvasUrl"]
    canvas_token = selected_realm["canvasToken"]
    canvas_terms = selected_realm["canvasTerms"]
    env_label = selected_realm["envLabel"]

    canvas_auth = {"Authorization": f"Bearer {canvas_token}"}

    print(f"Connected to {env_label} - {canvas_url}")
    print("")

    canvas_user = env["canvas.ro-user"]
    canvas_pass = env["canvas.ro-pass"]
    box_parent_folder_id = env["uofi.box.tdx.parent.folder"]
    box_jwt_auth_file = env["uofi.box.jwtauth.file"]

    # Gather required request metadata before processing anything.
    tdx_ticket = require_input("  > Enter TDX support request number: ")

    requestor_search = require_input("  > Enter the UIN, NetID or Illinois Email of the support requestor: ")
    requestor_info = canvasGetUserInfo(requestor_search, canvas_api, canvas_auth)
    if not requestor_info:
        print("\n>>> Unable to locate requestor in Canvas. Exiting.\n")
        return

    requestor_email = get_illinois_email(requestor_info)
    if not requestor_email:
        requestor_email = require_input("  > Requestor Canvas record had no Illinois email. Enter Illinois email manually: ").lower()
    if not requestor_email.endswith("@illinois.edu"):
        print("\n>>> Requestor email must be an @illinois.edu address. Exiting.\n")
        return

    student_search = require_input("  > Enter the student's UIN, NetID or Illinois email address: ")
    student_info = canvasGetUserInfo(student_search, canvas_api, canvas_auth)
    if not student_info:
        print("\n>>> Unable to locate student in Canvas. Exiting.\n")
        return

    student_canvas_id = student_info.get("id")
    student_net_id = student_info.get("sis_user_id") or student_search
    if not student_canvas_id:
        print("\n>>> Student record did not include a Canvas ID. Exiting.\n")
        return

    term_code = ""
    while not term_code:
        term_code = input("  > Enter Banner term code: ").strip().upper()
    if term_code not in canvas_terms:
        print(f"  >>> Warning: {term_code} is not in configured terms list.")
        if not yesOrNo("Continue with this term code anyway?"):
            print("\n>>> Exiting by user request.\n")
            return

    print("\n  = Looking up enrollments for the selected student and term...\n")
    search_results = fetch_enrollments_for_term(student_canvas_id, term_code, canvas_api, canvas_auth)
    rows = build_enrollment_rows(search_results)

    if not rows:
        print(f">>> No enrollments found for {student_net_id} in term {term_code}. Exiting.\n")
        return

    print_enrollment_table(rows)
    planned_changes = plan_enrollment_changes(rows)
    if not planned_changes:
        if not yesOrNo("No enrollment changes are planned. Continue to report generation anyway?"):
            print("\n>>> Exiting with no changes made.\n")
            return

    changed_rows = []
    failed_changes = []

    if planned_changes:
        print("\n  = Applying enrollment changes...\n")
        for planned in planned_changes:
            enroll_id = planned["enroll_id"]
            new_status = planned["new_status"]
            row = planned["row"]

            print(f"  > Updating enrollment {enroll_id} ({row['sis_course_id']}) to {new_status}...")
            ok, result = canvas_enrollment_edit(
                enroll_id,
                canvas_api,
                canvas_auth,
                row,
                new_status,
                student_canvas_id,
            )
            if ok:
                state = result.get("enrollment_state", "unknown")
                print(f"  = Success: enrollment {enroll_id} now in state {state}.")
                changed_rows.append(row)
            else:
                print(f"  >>> Failed: enrollment {enroll_id}. {result}")
                failed_changes.append({"enroll_id": enroll_id, "error": result, "row": row})
            print("")

        print(f"  = Enrollment changes complete. Success: {len(changed_rows)}, Failed: {len(failed_changes)}")

        if failed_changes:
            for failure in failed_changes:
                print(f"    - {failure['enroll_id']}: {failure['error']}")
            print("")
            if not changed_rows:
                print(">>> No enrollment changes succeeded. Cannot proceed to report generation for changed enrollments.\n")
                return
            if not yesOrNo("Continue to report generation using only successful enrollment changes?"):
                print("\n>>> Exiting by user request after partial enrollment failures.\n")
                return

    target_rows = changed_rows if changed_rows else rows
    unique_target_rows = {}
    for row in target_rows:
        unique_target_rows[str(row["course_id"])] = row
    report_rows = list(unique_target_rows.values())

    print("\n  = Preparing BOX destination...\n")
    try:
        box_auth = JWTAuth.from_settings_file(box_jwt_auth_file)
        box_client = Client(box_auth)
    except Exception as ex:
        print(f">>> Failed to initialize BOX client: {ex}\n")
        return

    folder_base_name = f"tdx_{tdx_ticket}"
    try:
        box_folder_id, box_folder_name, shared_link = create_box_folder_and_share(
            box_client,
            box_parent_folder_id,
            folder_base_name,
            requestor_email,
        )
        print(f"  = BOX folder ready: {box_folder_name} (ID: {box_folder_id})")
        print(f"  = Folder shared with {requestor_email}")
    except Exception as ex:
        print(f">>> Failed to create/share BOX folder: {ex}\n")
        return

    print("\n  = Launching browser and logging into Canvas for report exports...\n")
    driver = None
    upload_success_count = 0
    upload_failures = []

    try:
        driver = setup_browser()
        if not canvas_login(driver, canvas_user, canvas_pass, canvas_url):
            print(">>> Canvas login failed. Cannot continue report generation.\n")
            return

        os.makedirs(REPORTS_PATH, exist_ok=True)

        for row in report_rows:
            course_id = row["course_id"]
            enroll_id = row["enroll_id"]
            report_url = f"{canvas_url}/courses/{course_id}/users/{student_canvas_id}/usage"
            target_file_name = f"tdx_{tdx_ticket}_{student_net_id}_{course_id}_{enroll_id}_access_report.pdf"
            target_file_path = os.path.join(REPORTS_PATH, target_file_name)

            print(f"  > Generating report for course {course_id} (enrollment {enroll_id})...")
            ok, err = student_access_report_export(driver, report_url, target_file_path)
            if not ok:
                print(f"  >>> Failed to export report for course {course_id}: {err}")
                upload_failures.append({"course_id": course_id, "reason": f"export failed: {err}"})
                continue

            print(f"  = Report exported: {target_file_path}")
            ok, err = upload_file_to_box(box_client, box_folder_id, target_file_path, target_file_name)
            if ok:
                upload_success_count += 1
                print(f"  = Uploaded to BOX: {target_file_name}")
            else:
                print(f"  >>> Failed to upload {target_file_name} to BOX: {err}")
                upload_failures.append({"course_id": course_id, "reason": f"upload failed: {err}"})
            print("")

    except Exception as ex:
        print(f">>> Unexpected error during report generation: {ex}")
    finally:
        if driver:
            driver.quit()
            print("  = Browser closed.")

    print("\n=== PROCESS SUMMARY ===")
    print(f"TDX ticket:           {tdx_ticket}")
    print(f"Requestor email:      {requestor_email}")
    print(f"Student NetID:        {student_net_id}")
    print(f"Term code:            {term_code}")
    print(f"Reports uploaded:     {upload_success_count}")
    print(f"Report failures:      {len(upload_failures)}")
    if upload_failures:
        for failure in upload_failures:
            print(f"  - Course {failure['course_id']}: {failure['reason']}")

    print("")
    print("Share this BOX link with the requestor:")
    print(shared_link)
    print("")


if __name__ == "__main__":
    main()
