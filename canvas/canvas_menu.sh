#!/bin/bash

pressKey() {
    echo ""
    echo "============================"
    read -n 1 -p "Press any key to continue..."
}

executeCommand() {
    local command=$1
    eval "$command"
    pressKey
}

menuText=$(cat <<'EOF'

    ===============================================================================
                              Canvas@Illinois Operations
                                   Management Menu
    ===============================================================================
    Please enter your choice:

    Canvas Course/User/Roster Info:
       (a) Canvas: Get Single Course Enrollments (PROD-Live)
       (b) Canvas: Get Enrollments for Single User in Banner Term (PROD-Live)
       (c) Canvas: Get Course Info (PROD)
       (d) Canvas: Get User Info (PROD-live)
       (e) Canvas: Audit Course Events
       (%) Canvas: Get All Student Completion Status in Course
       (=) Canvas: Move course dept/acct in Canvas and SRA
       (?) Canvas: Student Access Report (optional upload to BOX)
       (f) Class Rosters: Get Course Memberships (PROD)

    Canvas Course/User/Roster Management:
       (g) Canvas: Enrollment Info and Status Change (PROD/STAGE-Live)
       (h) Canvas: Enroll User In non-Closed Course (PROD/STAGE-Live)
       (i) Canvas: Observer Manager (PROD/STAGE-Live)
       ($) Canvas: Extend Course For a Single Student
       (@) Canvas: Move Registrar-enabled Course (also affects SRA placement)
       (#) Canvas: Add Enrollment to Closed Course
       (Z) Canvas: Export Course as Zip, Qti or CC

    Canvas Data 2:
       (j) CD2: Postgres Query

    Active Directory - Class Rosters:
       (k) AD: User Info (PROD)
       (l) AD: Roster List by CRN or Space ID (PROD/STAGE)
       (M) CR: CRN and Space Members (with SIS course ID)

    Space Request Application:
       (n) SRA: User Manager (PROD/STAGE)
       (o) SRA: Space Information (PROD/STAGE)
       (p) SRA: Status Change (PROD/STAGE)
       (r) SRA: CRN Add/Remove on Space (PROD/STAGE)
       (s) SRA: Space History (PROD/STAGE)
       (t) SRA: Term Add (PROD/STAGE)
       (u) SRA: Spaces Waiting (PROD/STAGE)

    Systems and Maintenance:
       (v) Canvas SIS ID Details            (y) Edit Crontab (PROD)
       (w) Canvas SIS Uploads Info          (z) Python 3.12 Virtual Env (PROD)
       (x) Update Canvas Objects (PROD)     (+) Generate a Complex Password

    (Q/q)uit
    ===============================================================================

EOF
)

while :
do
    clear
    echo "$menuText"
    read -n1 -s
    case "$REPLY" in
        "a") executeCommand "~/bin/canvas_course_enrollments_PROD.sh" ;;
        "b") executeCommand "~/bin/canvas_get_user_enrollments_live.sh" ;;
        "c") executeCommand "~/bin/canvas_get_course_info.sh" ;;
        "d") executeCommand "~/bin/canvas_get_user_info_live.sh" ;;
        "e") executeCommand "~/bin/canvas_audit_course.sh" ;;
        "%") executeCommand "~/bin/canvas_get_bulk_user_progress_in_course.sh" ;;
        "=") executeCommand "~/bin/canvas_sra_move_course.sh" ;;
        "?") executeCommand "~/bin/canvas_student_access_report.sh" ;;
        "f") executeCommand "~/bin/cr_member_info.sh" ;;
        "g") executeCommand "~/bin/canvas_enrollment_info_and_edit.sh" ;;
        "h") executeCommand "~/bin/canvas_enroll_user.sh" ;;
        "i") executeCommand "~/bin/canvas_observer_mgr.sh" ;;
        "$") executeCommand "~/bin/canvas_extend_course_for_single_student.sh" ;;
        "@") executeCommand "~/bin/canvas_sra_move_course.sh" ;;
        "#") executeCommand "~/bin/canvas_add_enrollment_to_closed_course.sh" ;;
        "Z") executeCommand "~/bin/canvas_export_course.sh" ;;
        "j") executeCommand "~/bin/cd2_query_db.sh" ;;
        "k") executeCommand "~/bin/ad_user_info.sh" ;;
        "l") executeCommand "~/bin/ad_roster_by_crn_or_space.sh" ;;
        "M") executeCommand "~/bin/cr_crn_and_space_members.sh" ;;
        "n") executeCommand "~/bin/req_user_mgr.sh" ;;
        "o") executeCommand "~/bin/req_space_info.sh" ;;
        "p") executeCommand "~/bin/req_space_status_change.sh" ;;
        "r") executeCommand "~/bin/req_space_crn_edit.sh" ;;
        "s") executeCommand "~/bin/req_space_history.sh" ;;
        "t") executeCommand "~/bin/req_term_add.sh" ;;
        "u") executeCommand "~/bin/req_space_waiting.sh" ;;
        "v") executeCommand "~/bin/canvas_sis_id_details.sh" ;;
        "w") executeCommand "~/bin/canvas_sis_uploads_info.sh" ;;
        "x") executeCommand "~/bin/canvas_objects_download.sh" ;;
        "y") echo ""; eval crontab -e; pressKey ;;
        "z") echo "Starting Python 3.12 Virtual Development environment..."; echo ""; eval source ~/python312-venv/bin/activate; python; pressKey ;;
        "+") executeCommand "~/bin/generate_password.sh" ;;
        "Q"|"q") exit ;;
        * ) echo "Invalid option..."; echo "" ;;
    esac
done
