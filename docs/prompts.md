# Prompts Used in AI Talent Advisor

This document contains all prompts used in the system that materially influenced implementation and results.

## Overview

The system uses 5 main prompt templates across the orchestration chain. All prompts are stored in `app/orchestration/prompts.py` and are designed to be:
- **Specific**: Include context and structure
- **Composable**: Work as part of a larger chain
- **Debuggable**: Outputs can be parsed and validated
- **Fallback-Safe**: Have sensible defaults if parsing fails

---

## 1. Role Summary Prompt

**Location**: `ROLE_SUMMARY_PROMPT_TEMPLATE` in `app/orchestration/prompts.py`

**Purpose**: Generate a 2-3 sentence executive summary of the role requirements

**Template**:
```
Given the following job description and company context, create a concise role summary (2-3 sentences) that highlights the key responsibilities and required competencies.

Company: {company_name}
Job Title: {job_title}
Job Description: {job_description}

Role Summary:
```

**Example Input**:
```
Company: TechCorp
Job Title: Senior Software Engineer
Job Description: 5+ years full-stack development experience with Python, JavaScript, and AWS. 
                 Must have experience with microservices architecture and REST API design.
```

**Expected Output**:
```
This is a senior-level full-stack engineering role at TechCorp requiring 5+ years of experience 
in building scalable web applications with Python and JavaScript. The ideal candidate will have 
strong expertise in cloud platforms (AWS), microservices architecture, and REST API design, with 
a proven track record of delivering high-quality software solutions.
```

**Design Choices**:
- Explicitly requests "2-3 sentences" for conciseness
- Includes company name for context
- Concatenates job title and description to provide complete picture
- Clean, structured output format

---

## 2. Student Scoring Prompt

**Location**: `STUDENT_SCORING_PROMPT_TEMPLATE` in `app/orchestration/prompts.py`

**Purpose**: Evaluate a student's fit for a role and assign a match score (0-100)

**Template**:
```
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
```

**Example Input**:
```
Student ID: student_001
Student Resume Excerpt: 5+ years of full-stack development experience with Python, Django, 
                        Flask, React, and Node.js. AWS certified with microservices experience.

Job Title: Senior Software Engineer
Job Requirements: 5+ years full-stack, Python/JS expertise, AWS knowledge
```

**Expected Output**:
```
SCORE: 88
MATCHES:
- Meets required 5+ years full-stack development experience
- Strong Python expertise with Django and Flask frameworks
- AWS certification demonstrates cloud platform proficiency
DEVELOPMENT_AREAS:
- Limited mention of REST API design experience
- No explicit microservices architecture projects mentioned
```

**Design Choices**:
- Specific format for easy parsing (SCORE:, MATCHES:, DEVELOPMENT_AREAS:)
- Requests both strengths AND weaknesses for balanced evaluation
- Limited to top 3 matches and 2 development areas (prevents verbose output)
- Uses structured parsing pattern in `_parse_score_from_response()`

---

## 3. Interview Question Prompt

**Location**: `INTERVIEW_QUESTION_PROMPT_TEMPLATE` in `app/orchestration/prompts.py`

**Purpose**: Generate 3 contextual interview questions tied to student's background

**Template**:
```
Create 3 technical interview questions specifically for this student based on their resume 
and the job requirements. Each question should be tied to specific evidence from their background.

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
```

**Example Input**:
```
Student ID: student_001
Student Background: Built microservices platform serving 1M+ users. Architected REST APIs 
                   using Django. Led team of 4 junior developers.

Job Requirements: Senior Python Developer with API design and team leadership experience
```

**Expected Output**:
```
Q1: Describe your approach to designing REST APIs for scalability. How did you ensure 
    your Django APIs could handle the 1M+ user load you mentioned?
EVIDENCE: "Architected REST APIs using Django"

Q2: Tell us about your experience mentoring junior developers. How did you help them 
    improve their skills and grow professionally?
EVIDENCE: "Led team of 4 junior developers"

Q3: Walk us through your approach to breaking down a monolithic application into 
    microservices. What were the key challenges you faced?
EVIDENCE: "Built microservices platform"
```

**Design Choices**:
- Requests questions tied to specific resume evidence (for fairness)
- 3 questions cover: technical, leadership, and architectural thinking
- EVIDENCE field links to resume excerpt for transparency
- Parsing handles Q1/Q2/Q3 format with EVIDENCE: markers

---

## 4. Outreach Email Prompt

**Location**: `OUTREACH_EMAIL_PROMPT_TEMPLATE` in `app/orchestration/prompts.py`

**Purpose**: Generate personalized recruiting outreach email for a student

**Template**:
```
Write a professional outreach email to a student for a specific job opportunity. 
The email should be personalized based on their background and the role.

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
```

**Example Input**:
```
Student Name: John Smith
Student Background: 5+ years full-stack development, AWS certified, microservices expert
Company: TechCorp
Job Title: Senior Software Engineer
```

**Expected Output**:
```
Subject: Exciting Senior Engineer Opportunity at TechCorp

Dear John,

I came across your profile and was impressed by your extensive experience in full-stack 
development and your AWS certification. Your work on microservices platforms particularly 
caught my attention, as this aligns perfectly with TechCorp's current technology initiatives.

We're currently looking for a Senior Software Engineer to join our growing engineering team. 
The role involves designing and implementing scalable systems using modern cloud technologies—
exactly the kind of work where your skills would have significant impact.

I'd love to discuss how your experience could be a great fit for this opportunity. Could you 
spare 20 minutes for a quick conversation this week? Feel free to reply with times that work best.

Looking forward to connecting!

Best regards,
[Recruiter Name]
TechCorp Recruitment Team
```

**Design Choices**:
- Specific word count range (150-250) for appropriate brevity
- Emphasizes "reference something specific" to personalize
- Clear CTA (request for meeting)
- Professional but warm tone
- Includes signature line placeholders

---

## 5. Scorecard Synthesis Prompt

**Location**: `SCORECARD_PROMPT_TEMPLATE` in `app/orchestration/prompts.py`

**Purpose**: Create comprehensive recruitment scorecard with all evaluation data

**Template**:
```
Create a comprehensive recruitment scorecard for a student applying to a specific role. 
Synthesize all available information.

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
```

**Example Output**:
```
1. Overall Score: 82
2. Technical Match: Strong in core languages (Python/JS) and cloud platforms (AWS). 
                    Good understanding of microservices but limited REST API design depth.
3. Experience Alignment: 5+ years meets tenure requirement. Team leadership experience 
                        demonstrates seniority. Some gaps in specific domain knowledge.
4. Recommended Action: Hire - Strong technical foundation with some room for growth
```

**Design Choices**:
- Synthesizes all prior evaluations into single scorecard
- Includes explicit recommendation (Hire/Maybe/Pass)
- Focuses on actionability for recruiters
- Balanced assessment of strengths and weaknesses

---

## Prompt Engineering Decisions

### 1. Structured Output Formats
All prompts use explicit delimiters (SCORE:, EVIDENCE:, Q1:) to enable reliable parsing without regex complexity.

### 2. Context Integration
Each prompt receives both the student information AND job requirements to enable nuanced comparisons.

### 3. Fallback Handling
If LLM output doesn't parse correctly, the system provides sensible defaults:
- Scoring: Returns 75.0 (neutral)
- Questions: Provides 3 generic technical questions
- Email: Returns template email with placeholders

### 4. Token Optimization
Prompts are concise and use template substitution to avoid repeating instructions:
- Job descriptions truncated to 300-500 characters
- Resume excerpts limited to 400-500 characters

### 5. Bias Mitigation
Prompts explicitly request:
- Objective criteria-based scoring
- Both strengths AND areas for development
- Specific evidence citations (not assumptions)

---

## LLM Model Selection

**Model**: GPT-3.5-turbo
**Reasoning**:
- Fast inference (50-100ms typical)
- Good instruction-following for structured outputs
- Cost-effective for high-volume candidate evaluation
- Sufficient capability for scoring/questions task

**Alternative**: GPT-4 for higher quality, with trade-off of higher latency/cost

---

## Mock vs Production Responses

### Mock Mode (DEFAULT)
- **Enabled by**: `USE_MOCK_LLM=true` in `.env`
- **Behavior**: Returns deterministic, sensible responses
- **Purpose**: Local development and testing without API calls
- **Implementation**: `_mock_completion()` in `llm_client.py`

### Production Mode
- **Enabled by**: `USE_MOCK_LLM=false` and valid `OPENAI_API_KEY`
- **Behavior**: Makes actual API calls to OpenAI
- **Cost**: ~0.001-0.01 per orchestration request (varies by token usage)
- **Fallback**: Automatically falls back to mock if API fails

---

## Evaluation Metrics

These prompts were validated against:
1. **Relevance**: Do outputs match the specific student profile?
2. **Actionability**: Can recruiters make decisions based on output?
3. **Consistency**: Do outputs align with scoring and recommendations?
4. **Parseability**: Can structured outputs be reliably extracted?

---

## Future Prompt Improvements

1. **Fine-tuning**: Collect feedback and fine-tune model on real campus hiring data
2. **Bias Auditing**: Run through fairness evaluation frameworks (e.g., AI Fairness 360)
3. **Multi-role Variants**: Create specialized prompts for different role types
4. **Multilingual**: Support non-English resumes and emails
5. **Feedback Loop**: Learn from recruiter feedback to refine scores

---

**Last Updated**: June 2024
