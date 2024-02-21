# Trainees-Attendance

Traditionally, instructors manually track trainee attendance and compile daily status reports via WhatsApp for their supervisors. To streamline this process and minimize errors, I developed a web application using React, Flask, and a PostgreSQL database.

The application consists of three tabs:

**Home**: Instructors select the excuse given to trainees. Under each excuse, the names of trainees currently excused are displayed. Instructors can add new names using the ADD button, edit existing records with the UPDATE button, and void records with the DELETE option.

**Status**: This tab generates the daily status report.

**MC**: Reflects the total medical leave duration (MC) of recruits. Supervisors can use this information to identify individuals requiring additional attention and follow-up.
