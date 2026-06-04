"""Prompt templates for the orchestration chain."""

ROLE_SUMMARY_PROMPT_TEMPLATE = """
Given the following job description and company context, create a concise role summary (2-3 sentences) that highlights the key responsibilities and required competencies.

Company: {company_name}
Job Title: {job_title}
Job Description: {job_description}

Role Summary:
"""

STUDENT_SCORING_PROMPT_TEMPLATE = """
Evaluate the following student profile against the job requirements and provide:
1. A match score (0-100)
2. Key matching points (top 3)
3. Areas for development (top 2)

Student ID: {student_id}
Student Resume Excerpt: {resume_excerpt}

Job Title: {job_title}
Job Requirements: {job_description}

Provide the evaluation in this format:
SCORE: [number]
MATCHES:
- [point 1]
- [point 2]
- [point 3]
DEVELOPMENT_AREAS:
- [area 1]
- [area 2]
"""

INTERVIEW_QUESTION_PROMPT_TEMPLATE = """
Create 3 technical interview questions specifically for this student based on their resume and the job requirements. Each question should be tied to specific evidence from their background.

Student ID: {student_id}
Student Background: {resume_excerpt}
Job Requirements: {job_description}

Format each question as:
Q1: [Question text]
EVIDENCE: [Reference to what in their background prompted this]

Q2: [Question text]
EVIDENCE: [Reference to what in their background prompted this]

Q3: [Question text]
EVIDENCE: [Reference to what in their background prompted this]
"""

OUTREACH_EMAIL_PROMPT_TEMPLATE = """
Write a professional outreach email to a student for a specific job opportunity. The email should be personalized based on their background and the role.

Student Name: {student_name}
Student Background: {resume_excerpt}
Company: {company_name}
Job Title: {job_title}

The email should:
- Be 150-250 words
- Reference something specific from their resume
- Include a clear call to action
- Be professional but warm

Email:
"""

# Prompt for generating comprehensive scorecards
SCORECARD_PROMPT_TEMPLATE = """
Create a comprehensive recruitment scorecard for a student applying to a specific role. Synthesize all available information.

Student ID: {student_id}
Student Resume: {resume_excerpt}
Company: {company_name}
Job Title: {job_title}
Job Description: {job_description}

Provide:
1. Overall Score (0-100): [number]
2. Technical Match: [brief assessment]
3. Experience Alignment: [brief assessment]
4. Recommended Action: [Hire/Maybe/Pass]

Keep it concise and actionable.
"""
