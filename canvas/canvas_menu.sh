#!/bin/bash

pressKey() {
    echo ""
    echo "============================"
    read -n 1 -p "Press any key to continue..."
}

while :
do
    clear
    cat<<EOF

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
       (m) AD: CRN Info (PROD)
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
    read -n1 -s
    case "$REPLY" in

    "a") ~/bin/canvas_course_enrollments_PROD.sh
         pressKey ;;

    "b") ~/bin/canvas_get_user_enrollments_live.sh
         pressKey ;;

    "c") ~/bin/canvas_get_course_info.sh
         pressKey ;;

    "d") ~/bin/canvas_get_user_info_live.sh
         pressKey ;;

    "e") ~/bin/canvas_audit_course.sh
         pressKey ;;

    "%") ~/bin/canvas_get_bulk_user_progress_in_course.sh
         pressKey ;;

    "=") ~/bin/canvas_sra_move_course.sh
         pressKey ;;

    "?") ~/bin/canvas_student_access_report.sh
         pressKey ;;

    "f") ~/bin/cr_member_info.sh
         pressKey ;;

    "g") ~/bin/canvas_enrollment_info_and_edit.sh
         pressKey ;;

    "h") ~/bin/canvas_enroll_user.sh
         pressKey ;;

    "i") ~/bin/canvas_observer_mgr.sh
         pressKey ;;

    "$") ~/bin/canvas_extend_course_for_single_student.sh
         pressKey ;;

    "@") ~/bin/canvas_sra_move_course.sh
         presskey ;;

    "#") ~/bin/canvas_add_enrollment_to_closed_course.sh
         presskey ;;

    "Z") ~/bin/canvas_export_course.sh
         presskey ;;

    "j") ~/bin/cd2_query_db.sh
         pressKey ;;

    "k") ~/bin/ad_user_info.sh
         pressKey ;;

    "l") ~/bin/ad_roster_by_crn_or_space.sh
         pressKey ;;

    "m") ~/bin/ad_crn_info.sh
         pressKey ;;

    "M") ~/bin/cr_crn_and_space_members.sh
         pressKey ;;

    "n") ~/bin/req_user_mgr.sh
         pressKey ;;

    "o") ~/bin/req_space_info.sh
         pressKey ;;

    "p") ~/bin/req_space_status_change.sh
         pressKey ;;

    "r") ~/bin/req_space_crn_edit.sh
         pressKey ;;

    "s") ~/bin/req_space_history.sh
         pressKey ;;

    "t") ~/bin/req_term_add.sh
         pressKey ;;

    "u") ~/bin/req_space_waiting.sh
         pressKey ;;

    "v") ~/bin/canvas_sis_id_details.sh
         pressKey ;;

    "w") ~/bin/canvas_sis_uploads_info.sh
         pressKey ;;

    "x") ~/bin/canvas_objects_download.sh
         pressKey ;;

    "y") echo ""
         eval crontab -e
         pressKey ;;

    "z") echo "Starting Python 3.12 Virtual Development environment..."
         echo ""
         eval source ~/python312-venv/bin/activate
         python
         pressKey ;;

    "+") ~/bin/generate_password.sh
         pressKey ;;

#    "w") PLACEHOLDER

    "Q") exit ;;
    "q") exit ;;
     * ) echo "Invalid option..."
         echo "" ;;
    esac
#    sleep 1
done
